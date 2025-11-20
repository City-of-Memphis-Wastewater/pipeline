# pipeline/interfaces/gui_eds.py

from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9

from typer import BadParameter
from pathlib import Path
from pipeline.core import eds as eds_core
import os
import pyhabitat

from pipeline.server.trend_server_eds import launch_server_for_web_gui_eds_trend_specific 
from pipeline.interface.utils import save_history, load_history

"""
To force webmode or localmode in PowerShell:
$env:PIPELINE_FORCE_WEB_GUI = 1
$env:PIPELINE_FORCE_LOCAL_GUI = 1

To force webmode or localmode in Bash:
export PIPELINE_FORCE_WEB_GUI=1
export PIPELINE_FORCE_LOCAL_GUI=1
"""


# --- Status Bar Helper Function ---
def update_status(window, message, color='white'):
    """Updates the status bar text and color."""
    # Use an alias to the element for cleaner code
    #window['STATUS_BAR'].update(message, text_color=color)
    window['STATUS_BAR'].update(message)

def create_separator(sg_lib):
    """Returns a fresh list containing a new sg.Text separator element."""
    return [sg_lib.Text('_' * 50, justification='center')]
    # return [sg.HorizontalSeparator()]

def launch_fsg()->None:
    """
    Launches the FreeSimpleGUI interface for EDS Trend.
    Web usage is deprecated. For posterity, the brittle but functional approach was
        - freesimplegui = "^5.2.0.post1"
        - legacy-cgi = "^2.6.4"
        - freesimpleguiweb = "^1.1.0"
        - remi = {git = "https://github.com/rawpython/remi.git
    
    """
    # Load history for the dropdown list
    idcs_history = load_history()

    try:
        import FreeSimpleGUI as sg
    except:
        """Fallback to web if FreeSimpleGUI is not available."""
        launch_server_for_web_gui_eds_trend_specific()
        #launch_server_for_web_gui()
        return
    # Set theme for a slightly better look
    #sg.theme('DarkGrey15') # not available in web
    sg.theme('DarkGreen3')
    #sg.theme('DarkGreen4') 

        

    
    # Desktop (FreeSimpleGUI) - Combo allows typing and history selection
    idcs_input = [sg.Combo(
        values=idcs_history,                 # The list of historical queries
        default_value=idcs_history[0] if idcs_history else '', # Default to the last query
        size=(50, 1),
        key="idcs_list",
        enable_events=False,                 # Do not trigger events when an item is selected
        readonly=False                       # Allows typing new entries
    )]



    
    plot_web_or_local_radio_buttons = [sg.Radio("Web-Based Plot (Plotly)", group_id= "plot_environment", key="force_webplot", default=True, tooltip="Uses Plotly/browser. Recommended for most users."),
         sg.Radio("Matplotlib Plot (Local)", group_id= "plot_environment", key="force_matplotlib", default=False, tooltip="Uses Matplotlib. Requires a local display environment.")]
        

    # Define the layout
    layout = [
        [sg.Text("EDS Trend", font=("Helvetica", 16))],
        create_separator(sg),
        [sg.Text("Ovation Sensor IDCS (e.g., M100FI M310LI FI8001).", size=(40, 1))],
        [sg.Text("Separate with spaces or commas. ", size=(40, 1))],
        idcs_input,
        [sg.Checkbox("Use Configured Default IDCS", key="default_idcs", default=False)],
        
        create_separator(sg),

        [sg.Text("Time Range (leave empty for last 48 hours)", font=("Helvetica", 12))],
        [sg.Text("Days:", size=(10, 1)), sg.InputText(key="days", size=(15, 1))],
        [sg.Text("Start Time:", size=(10, 1)), sg.InputText(key="starttime", size=(25, 1))], 
        [sg.Text("End Time:", size=(10, 1)), sg.InputText(key="endtime", size=(25, 1))],
        
        create_separator(sg),

        [sg.Text("Frequency (leave empty for 400 data points)", font=("Helvetica", 12))],
        [sg.Text("Seconds Between Points:", size=(20, 1)), sg.InputText(key="seconds_between_points", size=(10, 1))],
        [sg.Text(" OR ")],
        [sg.Text("Datapoint Count:", size=(15, 1)), sg.InputText(key="datapoint_count", size=(10, 1))],
        
        create_separator(sg),
        plot_web_or_local_radio_buttons,
        
        create_separator(sg),
        [sg.Button("Fetch & Plot Trend", key="OK"), sg.Button("Close")],

        [sg.Text(" ", size=(50, 1), key='STATUS_BAR', text_color='white', background_color='#333333')]
    ]



    window = sg.Window("EDS Trend", layout, finalize=True)
    update_status(window, "Ready to fetch data.")

    while True: 
        event, values = window.read(timeout=100)
        
        if event == sg.WIN_CLOSED or event == "Close" or event == "Exit":
            # 1. Update status for the user before server shutdown
        
            break

        if event == "OK":
            update_status(window, "Processing request...")
            # --- Input Processing ---
            # Typer Argument (idcs) is a list[str], so we need to convert the string.
            if values["idcs_list"] is not None:
                idcs_input = values["idcs_list"].strip()
            else:
                idcs_input=None

            # Typer boolean options
            default_idcs = values["default_idcs"]

            # Check if input is empty, default_idcs is False, and history exists.
            if not idcs_input and not default_idcs and idcs_history:
                idcs_input = idcs_history[0] 
                update_status(window, f"IDCS input empty. Using history: {idcs_input}", 'yellow')

            # Save the successful input to history
            if idcs_input and idcs_input != (idcs_history[0] if idcs_history else ''): # Only save if non-empty and new/different
                save_history(idcs_input)
            idcs_list = idcs_input.split() if idcs_input else None

            if idcs_list == [] or idcs_input is None:
                idcs_input = idcs_history[0] # default to most recent request
            
            # Convert optional inputs to their correct types or None
            try:
                days = float(values["days"]) if values["days"] else None
                sec_between = int(values["seconds_between_points"]) if values["seconds_between_points"] else None
                dp_count = int(values["datapoint_count"]) if values["datapoint_count"] else None
            except ValueError:
                sg.popup_error("Invalid number entered for Days, Seconds, or Datapoint Count.")
                continue

            starttime = values["starttime"] if values["starttime"] else None
            endtime = values["endtime"] if values["endtime"] else None
            
            
            force_webplot = True    
            force_matplotlib = False
            try:
                force_webplot = values["force_webplot"]
                force_matplotlib = values["force_matplotlib"]       
            except:
                pass
            # --- Core Logic Execution ---
            try:
                # The core function handles all the logic and error checking
                data_buffer, _ = eds_core.fetch_trend_data(
                    idcs=idcs_list, 
                    starttime=starttime, 
                    endtime=endtime, 
                    days=days, 
                    plant_name=None, # Not an option in the current GUI
                    seconds_between_points=sec_between, 
                    datapoint_count=dp_count,
                    default_idcs=default_idcs
                )
                
                if data_buffer.is_empty():
                    #sg.popup_ok("Success, but no data points were returned for the selected time range and sensors.")
                    update_status(window, "Success, but no data points were returned for the selected time range and sensors. Check that all IDCS values are valid.", 'yellow')
                else:
                    # --- Plotting ---
                    update_status(window, "Data successfully fetched. Launching plot...", 'lime')
                    fig = eds_core.plot_trend_data(data_buffer, force_webplot, force_matplotlib)
                    update_status(window, "Plot launched. Ready for new query.", 'white')
                    
            except BadParameter as e:
                # Catch the specific error raised by the core logic
                #sg.popup_error("Configuration/Input Error:", str(e).strip())
                update_status(window, f"Configuration/Input Error: {str(e).strip()}", 'red')
            except Exception as e:
                # Catch all other unexpected errors
                #sg.popup_error("An unexpected error occurred during data fetching:", str(e))
                update_status(window, f"Check your VPN. An unexpected error occurred: {str(e)}", 'red')

    window.close()

def main(force_web:bool=False, force_local:bool=False):
    """
    If both force_local and force_web are specified (via args or env),
    web mode is favored. Successfully forcing local mode results in a
    failure message if it is not available in the environment.
    """

    # 1. Resolve arguments and environment variables into final flags
    # Centralize: Web wins over Local if both are set.
    
    # Get combined force flags (args OR env var)
    force_local_combined = force_local or os.getenv('PIPELINE_FORCE_LOCAL_GUI', '').lower() in ('1', 'true', 'yes')
    force_web_combined = force_web or os.getenv('PIPELINE_FORCE_WEB_GUI', '').lower() in ('1', 'true', 'yes')

    # Resolve conflict: Web wins over Local
    if force_local_combined and force_web_combined:
        force_local_combined = False # Web is the winner

    # 2. Define environmental availability
    is_mobile_env = pyhabitat.on_termux() or pyhabitat.on_ish_alpine()
    tkinter_available = pyhabitat.tkinter_is_available()
    web_browser_available = pyhabitat.web_browser_is_available()

    # 3. Decision Tree

    # A. User forced local mode
    if force_local_combined:
        if is_mobile_env or not tkinter_available:
            # Cannot succeed in this environment
            print("You tried to force local web gui, but it cannot succeeed in the current environment.")
            print(f"pyhabitat.tkinter_is_available() = {tkinter_available}")
        else:
            # Local is available and forced
            launch_fsg()
        return # Exit after attempting local force

    # B. If not forced local, check if web is required or forced
    web_required = is_mobile_env or not tkinter_available
    
    if force_web_combined or web_required:
        if web_browser_available:
            # Web is either required by environment OR explicitly requested
            launch_server_for_web_gui_eds_trend_specific()
        else:
            print("Web GUI is required/forced but no web browser is available to launch it.")
    
    # C. Default: Local desktop mode
    else:
        # Local GUI is available and no force flags were set.
        launch_fsg()

if __name__ == "__main__":
    main()    
   
