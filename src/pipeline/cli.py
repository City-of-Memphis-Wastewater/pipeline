from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import sqlite3
from rich.table import Table
from rich.console import Console
from click import BadParameter 
import typer
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
from requests.exceptions import Timeout
import sys 

from pipeline.time_manager import TimeManager
from pipeline.create_sensors_db import get_db_connection, create_packaged_db, reset_user_db # get_user_db_path, ensure_user_db, 
from pipeline.api.eds import demo_eds_webplot_point_live
from pipeline import environment
from pipeline.security_and_config import get_eds_api_credentials, get_external_api_credentials, get_eds_db_credentials, get_all_configured_urls, get_configurable_plant_name, init_security, CONFIG_PATH
from pipeline.termux_setup import setup_termux_shortcut
#from pipeline.helpers import setup_logging

# --- TERMUX SETUP HOOK ---
# This runs on every command (including --version and --help or without sub commands), 
# but the function's internal logic
# ensures the shortcut file is only created once in the Termux environment.
if environment.is_termux():
    setup_termux_shortcut()

# -- Versioning --
CLI_APP_NAME = "pipeline"
PIP_PACKAGE_NAME = "pipeline-eds"
def print_version(value: bool):
    if value:
        try:
            typer.secho(f"{CLI_APP_NAME} {PIPELINE_VERSION}",fg=typer.colors.GREEN, bold=True)
        except PackageNotFoundError:
            typer.echo("Version info not found")
        raise typer.Exit()
try:
    PIPELINE_VERSION = version(PIP_PACKAGE_NAME)
    __version__ = version(PIP_PACKAGE_NAME)
except PackageNotFoundError:
    PIPELINE_VERSION = "unknown"

try:
    from importlib.metadata import version
    __version__ = version(PIP_PACKAGE_NAME)
except PackageNotFoundError:
    # fallback if running from source
    try:
        with open(Path(__file__).parent / "VERSION") as f:
            __version__ = f.read().strip()
    except FileNotFoundError:
        __version__ = "dev" 

### Pipeline CLI

app = typer.Typer(help="CLI for running pipeline workspaces.")
console = Console()
init_security()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", callback=lambda v: print_version(v), is_eager=True, help="Show the version and exit.")
    ):
    """
    Pipeline CLI – run workspaces built on the pipeline framework.
    """

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()
    
    # 1. Access the list of all command-line arguments
    full_command_list = sys.argv
    
    # 2. Join the list into a single string to recreate the command
    command_string = " ".join(full_command_list)
    
    # 3. Print the command
    typer.echo(f"command:\n{command_string}\n")


@app.command()
def list_sensors(
    db_path: str = None,
    reset: bool = typer.Option(False, "--reset", help = "Reset the database file from the code-embedded sensor data"),
    ):
    """ See a cheatsheet of commonly used sensors from the database."""
    if reset:
        packaged_db = create_packaged_db()
        user_db = reset_user_db(packaged_db)

    # db_path: str = "sensors.db"
    if db_path is not None:
        conn = sqlite3.connect(db_path)
    else:  
        conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT idcs, iess, zd, ovation_drop, units, description FROM sensors")
    rows = cur.fetchall()
    conn.close()

    table = Table(title="Common Sensor Cheat Sheet (hard-coded)")
    table.add_column("IDCS", style="cyan")
    #table.add_column("IESS", style="magenta") # no reason to show this
    table.add_column("ZD", style="green")
    table.add_column("DROP", style="white")
    table.add_column("UNITS", style="white")
    table.add_column("DESCRIPTION", style="white")
    

    for idcs, iess, zd, ovation_drop, units, description in rows:
        table.add_row(idcs, zd, ovation_drop, units, description)
        

    console.print(table)
    console.print("⚠️ The ZD for the Stiles plant is WWTF", style = "magenta")

@app.command()
def live_query(
    idcs: list[str] = typer.Argument(..., help="Provide known idcs values that match the given zd."), # , "--idcs", "-i"
    zd: str = typer.Option('Maxson', "--zd", "-z", help = "Define the EDS ZD from your secrets file. This must correlate with your idcs point selection(s)."),
    webplot: bool = typer.Option(False,"--webplot","-w",help = "Use a web-based plot (plotly) instead of matplotlib. Useful for remote servers without display.")
):
    """live data plotting, based on CSV query files. Coming soon - call any, like the 'trend' command."""
    demo_eds_webplot_point_live()

@app.command()
def defaultplant(
    overwrite: bool = typer.Option(False, "--overwrite", "-o", help = "Overwrite existing plant name(s) to be used as default.")
    ):
    """Set the plant name(s) to be used if one is not explicitly provided in other commands, like trend. Comma separate for multiple."""
    configurable_plant_name = get_configurable_plant_name(overwrite=overwrite)
    typer.echo(f"Configurable plant name(s) for EDS API: {configurable_plant_name}")

@app.command()
def trend(
    idcs: list[str] = typer.Argument(None, help="Provide known idcs values that match the given zd."), # , "--idcs", "-i"
    starttime: str = typer.Option(None, "--start", "-s", help="Identify start time. Use any reasonable format, to be parsed automatically. If you must use spaces, use quotes."),
    endtime: str = typer.Option(None, "--end", "-end", help="Identify end time. Use any reasonable format, to be parsed automatically. If you must use spaces, use quotes."),
    plant_name: str = typer.Option(None, "--plantname", "-pn", help = "Define the EDS ZD for your credentials. This must correlate with your idcs point selection(s)."),
    #workspacename: str = typer.Option(None,"--workspace","-w", help = "Provide the name of the workspace you want to use, for the secrets.yaml credentials and for the timezone config. If a start time is not provided, the workspace queries can checked for the most recent successful timestamp. "),
    print_csv: bool = typer.Option(False,"--print-csv","-p",help = "Print the CSV style for pasting into Excel."),
    step_seconds: int = typer.Option(None, "--step-seconds", help="You can explicitly provide the delta between datapoints. If not, ~400 data points will be used, based on the nice_step() function."), 
    webplot: bool = typer.Option(False,"--webplot","-w",help = "Use a browser-based plot instead of local (matplotlib). Useful for remote servers without display."),
    default_idcs: bool = typer.Option(False, "--default-idcs", "-d", help="Use the default IDCS values for the configured plant name, instead of providing them as arguments.")
    ):
    """
    Show a curve for a sensor over time.
    """
    #from dateutil import parser
    import pendulum
    from pipeline.api.eds import EdsClient, load_historic_data, EdsLoginException
    from pipeline import helpers
    from pipeline.plotbuffer import PlotBuffer

    #zd = api_credentials.get("zd")
    if plant_name is None:
        plant_name = get_configurable_plant_name()

    # --- Conditional IDCS Input ---
    if idcs is None:
        if default_idcs:
            from pipeline.security_and_config import get_configurable_idcs_list
            # plant_name is resolved below, but we need a valid name for the helper
            # Temporarily resolve plant_name for the prompt if needed
            current_plant_name = plant_name if plant_name is not None else get_configurable_plant_name()
            idcs = get_configurable_idcs_list(current_plant_name)
            
            if not idcs:
                # Use a standard Typer error for missing config value
                raise BadParameter(
                    "The '--default-idcs' flag was used, but no IDCS points were configured or provided interactively.",
                    param_hint="--default-idcs"
                )
        else:
            # Raise a BadParameter exception to trigger the Typer/Rich error box
            error_message = (
                "\nIDCS values are required. You must either:\n"
                "1. Provide IDCS values as arguments: `eds trend IDCS1 IDCS2 ...`\n"
                "2. Use the default IDCS list: `eds trend --default-idcs`"
            )
            # This will now be wrapped in the structured error box.
            raise BadParameter(error_message, param_hint="IDCS...")
    # Convert all idcs values to uppercase, whether input now or stored in config. This assumes all IDCS value are uppcase all the time at every plant.
    idcs = [s.upper() for s in idcs]
    # --- END Conditional IDCS Input ---
    

    # Retrieve all necessary API credentials and config values.
    # This will prompt the user if any are missing.
    if isinstance(plant_name,str):
        api_credentials = get_eds_api_credentials(plant_name=plant_name)
    if isinstance(plant_name,list):
        typer.echo("")
        typer.echo(f"Multiple plant names provided: {plant_name} ")
        typer.echo("Querying multiple plants at once currently supported.") 
        typer.echo("Defaulting to use the first name.")
        api_credentials = get_eds_api_credentials(plant_name=plant_name[0])

    typer.echo(f"")
    typer.echo(f"Data request processing...")
    typer.echo(f"plant_name = {plant_name}")
    idcs_to_iess_suffix = api_credentials.get("idcs_to_iess_suffix")
    iess_list = [x+idcs_to_iess_suffix for x in idcs]
    typer.echo(f"iess_list = {iess_list}")
    typer.echo(f"")

    """
    # Use the retrieved credentials to log in to the API
    session = EdsClient.login_to_session(
        api_url=api_credentials.get("url"),
        username=api_credentials.get("username"),
        password=api_credentials.get("password")
    )
    """

    session = None
    try:
        session = EdsClient.login_to_session(
            api_url=api_credentials.get("url"),
            username=api_credentials.get("username"),
            password=api_credentials.get("password"),
            timeout=10 # Add a 10-second timeout to the request
        )
    except Timeout:
        typer.echo(
            typer.style(
                "\nConnection to the EDS API timed out. Please check your VPN connection and try again.",
                fg=typer.colors.RED,
                bold=True,
            )
        )
        raise typer.Exit(code=1)
    except EdsLoginException as e:
        typer.echo(
            typer.style(
                f"\nLogin failed for EDS API: {e}",
                fg=typer.colors.RED,
                bold=True,
            )
        )
        raise typer.Exit(code=1)
    

    # Set the session attributes based on the retrieved credentials
    session.base_url = api_credentials.get("url")
    session.zd = api_credentials.get("zd")
    
    points_data = EdsClient.get_points_metadata(session, iess_list=iess_list)
    
    
    if endtime is None:
        dt_finish = pendulum.from_timestamp(helpers.get_now_time_rounded())
        print(f"No endtime provided, so defaulting to now: {dt_finish.to_datetime_string()}")
    else:
        dt_finish = pendulum.parse(helpers.sanitize_date_input(endtime), strict=False)
    if starttime is None:
        days_past = 2
        dt_start = dt_finish.subtract(days=days_past) # default to 2 days ago
        print(f"No starttime provided, so defaulting to {days_past} days before endtime: {dt_start.to_datetime_string()}")
    else:
        dt_start = pendulum.parse(helpers.sanitize_date_input(starttime), strict=False)

    # Should automatically choose time step granularity based on time length; map 
    if step_seconds is None:
        step_seconds = helpers.nice_step(TimeManager(dt_finish).as_unix()-TimeManager(dt_start).as_unix()) # TimeManager(starttime).as_unix()
    results = load_historic_data(session, iess_list, dt_start, dt_finish, step_seconds) 
    # results is a list of lists. Each inner list is a separate curve.
    if not results:
        return 
    
    # The PlotBuffer instance is created once, outside the loop.
    data_buffer = PlotBuffer() 
    for idx, rows in enumerate(results):
        
        # We create a unique label for each of the 'rows' in the outer loop.
        # The plot will use this label to draw a separate line for each 'rows'.
        
        attributes = points_data[iess_list[idx]]
        label = f"{idcs[idx]}, {attributes.get('DESC')}, {attributes.get('UN')}"
        #label = idcs[idx]
        
        # The raw from EdsClient.get_tabular_trend() is brought in like this: 
        #   sample = [1757763000, 48.93896783431371, 'G'] 
        #   and then is converted to a dictionary with keys: ts, value, quality
        
        for row in rows:
            ts = helpers.iso(row.get("ts"))
            av = row.get("value")
            
            # All data is appended to the *same* data_buffer,
            # but the unique 'label' tells the buffer which series it belongs to.
            data_buffer.append(label, ts, av)

    # Once the loop is done, you can call your show_static function
    # with the single, populated data_buffer.

    if not environment.matplotlib_enabled() or webplot:
        from pipeline import gui_plotly_static
        #gui_fastapi_plotly_live.run_gui(data_buffer)
        gui_plotly_static.show_static(data_buffer)
    else:
        from pipeline import gui_mpl_live
        #gui_mpl_live.run_gui(data_buffer)
        gui_mpl_live.show_static(data_buffer)
    
    if print_csv:
        print(f"Time,\\{iess_list[0]}\\,")
        for idx, rows in enumerate(results):
            for row in rows:
                print(f"{helpers.iso(row.get('ts'))},{row.get('value')},")

@app.command(name="configure", help="Configure and store API and database credentials.")
def configure_credentials(
    overwrite: bool = typer.Option(False, "--overwrite", "-o", help="Overwrite existing credentials, with confirmation protection."),
    textedit: bool = typer.Option(False, "--textedit", "-t", help = "Open the config file in a text editor instead of using the guided prompt.")
    ):
    """
    Guides the user through a guided credential setup process. This is not necessary, as necessary credentials will be prompted for as needed, but this is a convenient way to set up multiple credentials at once. This command with the `--overwrite` flag is the designed way to edit existing credentials.
    """
    if textedit:
        typer.echo(F"Config filepath: {CONFIG_PATH}")
        environment.open_text_file_in_default_app(CONFIG_PATH)
        return
            
    typer.echo("")
    typer.echo("--- Pipeline-EDS Credential Setup ---")
    #typer.echo("This will securely store your credentials in the system keyring and a local config file.")
    typer.echo("You can skip any step by saying 'no' or 'n' when prompted.")
    typer.echo("You can quit editing credentials at any time by escaping with `control+C`.")
    typer.echo("You can run this command again later to add or modify credentials.")
    typer.echo("If you are not prompted for a credential, it is likely already configured. To change it, use the --overwrite flag.")
    typer.echo("")
    if overwrite:
        typer.echo("⚠️ Overwrite mode is enabled. Existing credentials will shown and you will be prompted to confirm overwriting them.")
        typer.echo(f"Alternatively, edit the configuration file directly in a text editor with the `--textedit` flag.")
        typer.echo(f"Config file path: {CONFIG_PATH}", color=typer.colors.MAGENTA)   

    # Get a list of plant names from the user
    num_plants = typer.prompt("How many EDS plants do you want to configure?", type=int, default=1)
    
    plant_names = []
    for i in range(num_plants):
        plant_name = typer.prompt(f"Enter a unique name for Plant #{i+1} (e.g., 'Maxson' or 'Stiles')")
        plant_names.append(plant_name)

    # Loop through each plant to configure its credentials
    for name in plant_names:
        typer.echo(f"\nConfiguring credentials for {name}...")
        
        # Configure API for this plant
        if typer.confirm(f"Do you want to configure the EDS API for '{name}'?", default=True):
            get_eds_api_credentials(plant_name=name, overwrite=overwrite)

        # Configure DB for this plant
        if False and typer.confirm(f"Do you want to configure the EDS database for '{name}'?",  default=False):
            get_eds_db_credentials(plant_name=name, overwrite=overwrite)
    
    # Configure any other external APIs
    if False and typer.confirm("Do you want to configure external API credentials? (e.g., RJN)"):
        external_api_name = typer.prompt("Enter a name for the external API (e.g., 'RJN')")
        get_external_api_credentials(party_name=external_api_name, overwrite=overwrite)

    typer.echo("\nSetup complete. You can now use the commands that require these credentials.")
    typer.echo("If a question was skipped, it is because the credential is already configured.")
    typer.echo("Run this command again with --overwrite to change it.")

@app.command()
def list_workspaces():
    """
    List all available workspaces detected in the workspaces folder.
    """
    # Determine workspace name
    from pipeline.workspace_manager import WorkspaceManager
    workspaces_path = WorkspaceManager.get_workspaces_dir()
    typer.echo(f"Workspaces directory: {workspaces_path}", color=typer.colors.MAGENTA)
    workspaces_list = WorkspaceManager.get_all_workspaces_names()
    typer.echo("📦 Available workspaces:")
    for name in workspaces_list:
        typer.echo(f" - {name}")


@app.command()
def ping(
    eds: bool = typer.Option(False,"--eds","-e",help = "Limit the pinged URL's to just the EDS services known to the configured secrets.")
    ):
    """
    Ping all HTTP/S URL's found in the secrets configuration.
    """
    from pipeline.calls import call_ping
    
    import logging

    logger = logging.getLogger(__name__)

    # Our new function handles loading from the config file and returns a set of URLs.
    url_set = get_all_configured_urls(only_eds=eds)

    typer.echo(f"Found {len(url_set)} URLs in configuration.")
    logger.info(f"url_set: {url_set}")
    for url in url_set:
        print(f"ping url: {url}")
        call_ping(url)

@app.command()
def help():
    """
    Show help information.
    """
    typer.echo(app.get_help())

if __name__ == "__main__":
    app()
