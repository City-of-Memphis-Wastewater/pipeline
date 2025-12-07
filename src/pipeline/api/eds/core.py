# pipeline/core/eds.py
"""
This was placed here by Grok.
Yes, we need a core directory, but for eds stuff we should be calling pipeline.api.eds...
"""
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9import time
import plotly.offline as pyo # You'll need this for the desktop display
import webbrowser
from pathlib import Path
import os
import tempfile
from typer import BadParameter


from pipeline.security_and_config import get_configurable_idcs_list
from pipeline.api.eds.config import get_configurable_default_plant_name
from pipeline.api.eds.rest.config import get_eds_rest_api_credentials
from pipeline import helpers
from pipeline.time_manager import TimeManager
from pipeline.plotbuffer import PlotBuffer
from pipeline.api.eds.rest.client import EdsRestClient
from pipeline.api.eds.config import get_idcs_to_iess_suffix 

def resolve_idcs_list(idcs: list[str] | None, default_idcs: bool, plant_name: str) -> list[str]:
    """
    Handles the logic for determining the final list of IDCS values.
    Raises BadParameter if required IDCS are missing.
    """
    if idcs is None:
        if default_idcs:
            # plant_name should already be resolved from defaults if None was passed in CLI
            current_plant_name = plant_name if plant_name is not None else get_configurable_default_plant_name()
            idcs = get_configurable_idcs_list(current_plant_name)

            if not idcs:
                raise BadParameter(
                    "The '--default-idcs' flag was used, but no IDCS points were configured.",
                    param_hint="--default-idcs"
                )
        else:
            # This is the GUI case where idcs_list is an empty string, which becomes None
            # or the CLI case where no arguments were provided without the flag.
            error_message = (
                "\nIDCS values are required. You must either:\n"
                "1. Provide IDCS values as arguments: `eds trend IDCS1 IDCS2 ...`\n"
                "2. Use the default IDCS list: `eds trend --default-idcs`"
            )
            raise BadParameter(error_message, param_hint="IDCS...")

    # Strip commas if the list was provided comma separated
    idcs = [s.rstrip(",") for s in idcs]

    # Convert all idcs values to uppercase
    idcs = [s.upper() for s in idcs]
    return idcs

def fetch_trend_data(
    idcs: list[str] | None, 
    starttime: str | None, 
    endtime: str | None, 
    days: float | None, 
    plant_name: str | None,
    seconds_between_points: int | None, 
    datapoint_count: int | None,
    default_idcs: bool = False,
    use_mock: bool = False
) -> tuple[PlotBuffer, list[str]]:
    """
    Core logic to fetch trend data from EDS REST API.
    Returns a populated PlotBuffer and the list of IESS names used.
    """
    # 1. Resolve Plant Name
    if plant_name is None:
        plant_name = get_configurable_default_plant_name()

    # 0b. If use_mock is requested, return a MockBuffer with synthetic data
    if use_mock:
        try:
            from pipeline.gui_plotly_static import MockBuffer
            return MockBuffer(), []
        except Exception:
            # Fallback: return an empty PlotBuffer so calling code behaves correctly
            return PlotBuffer(), []
    
    # 2. Resolve IDCS List
    # The list passed from the GUI will be a list of one string if the user entered values,
    # or None if the input box was empty.
    idcs = resolve_idcs_list(idcs, default_idcs, plant_name)

    # 3. Get Credentials and Login
    # This will prompt the user if any are missing.
    if isinstance(plant_name, list):
        # Handle the multi-plant case from CLI if needed, but for core logic, we use one.
        plant_name = plant_name[0]

    api_credentials = get_eds_rest_api_credentials(plant_name=plant_name)
    idcs_to_iess_suffix = api_credentials.get("idcs_to_iess_suffix")
    idcs_to_iess_suffix = get_idcs_to_iess_suffix(plant_name=plant_name) if idcs_to_iess_suffix is None else idcs_to_iess_suffix    
    iess_list = [x + idcs_to_iess_suffix for x in idcs]
    
    session = EdsRestClient.login_to_session_with_api_credentials(api_credentials)

    # 4. Get Point Metadata
    points_data = EdsRestClient.get_points_metadata(session, filter_iess=iess_list)

    # 5. Assess Time Range
    dt_start, dt_finish = helpers.asses_time_range(starttime=starttime, endtime=endtime, days=days)

    # 6. Determine Step Seconds
    time_delta_seconds = TimeManager(dt_finish).as_unix() - TimeManager(dt_start).as_unix()
    if datapoint_count is not None: 
        step_seconds = int(time_delta_seconds / datapoint_count)
    elif seconds_between_points is not None:
        step_seconds = seconds_between_points
    else:
        # Default behavior: use nice_step
        step_seconds = helpers.nice_step(time_delta_seconds)

    # 7. Load Historic Data
    results = EdsRestClient.load_historic_data(session, iess_list, dt_start, dt_finish, step_seconds) 
    
    if not results:
        # Return an empty buffer if no data is found
        return PlotBuffer(), iess_list 
        
    # 8. Populate PlotBuffer
    data_buffer = PlotBuffer() 
    for idx, rows in enumerate(results):
        
        attributes = points_data.get(iess_list[idx], {}) # Use .get for robustness
        unit = attributes.get('UN', 'N/A')
        description = attributes.get('DESC', 'Unknown Sensor')
        label = f"{idcs[idx]}, {description}, ({unit})"
        
        for row in rows:
            # raw is a dictionary with keys: ts (unix timestamp), value, quality
            ts = helpers.iso(row.get("ts"))
            av = row.get("value")
            
            data_buffer.append(label, ts, av, unit)
            
    return data_buffer, iess_list

def plot_trend_data(data_buffer: PlotBuffer, force_webplot: bool, force_matplotlib: bool):
    """
    Handles the common logic for plotting the data based on flags.  
    """
    import pyhabitat as ph # Assuming ph is a local import in the original CLI
    fig = None
    # Determine the plotting method
    use_plotly = force_webplot or not force_matplotlib or not ph.matplotlib_is_available_for_gui_plotting()

    if force_matplotlib and not ph.matplotlib_is_available_for_gui_plotting():
        # Using typer.echo here for CLI compatibility, but could be print/sg.Print
        print(f"force_matplotlib = {force_matplotlib}, but matplotlib is not available. Plotly, web-based plotting will be used.\n")
    
    # Check if we should use Plotly (webplot, or default when matplotlib isn't forced/available)
    if use_plotly:
        from pipeline import gui_plotly_static
        fig = gui_plotly_static.show_static(data_buffer)
    elif ph.matplotlib_is_available_for_gui_plotting():
        from pipeline import gui_mpl_live
        fig = gui_mpl_live.show_static(data_buffer)
    else: 
        print("No suitable plotting environment found.")
        return None
    # CUT OFF AFTER THIS TO REVERT
    return fig
    if fig and use_plotly and not ph.on_termux() and not ph.on_ish_alpine():
        # This section replaces the file/server launch logic removed from show_static
        tmp_file = Path(tempfile.gettempdir()) / f"eds_plot_{os.getpid()}.html"
        
        # Plotly method to save the figure to a local HTML file and open it
        pyo.plot(fig, filename=str(tmp_file), auto_open=False, include_plotlyjs='full')
        webbrowser.open(f"file://{tmp_file.resolve()}")
        
        
    return fig

# Assuming EdsRestClient and PlotBuffer are available via imports
# from pipeline.eds_client import EdsRestClient, PlotBuffer