'''
@app.command()
def list_workspaces(workspaces_dir: Path = Path("workspaces")):
    """List valid mulch workspaces in the given directory."""
    if not workspaces_dir.exists():
        typer.echo(f"Directory not found: {workspaces_dir}")
        raise typer.Exit(code=1)
    for path in workspaces_dir.iterdir():
        if path.is_dir() and (path / ".mulch").is_dir():
            typer.echo(f"🪴 {path.name}")

'''
import typer
import importlib
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

from pipeline.env import SecretConfig
from pipeline.time_manager import TimeManager
#from pipeline.helpers import setup_logging
#from pipeline.workspace_manager import WorkspaceManager

### Versioning
CLI_APP_NAME = "pipeline"
def print_version(value: bool):
    if value:
        try:
            typer.secho(f"{CLI_APP_NAME} {PIPELINE_VERSION}",fg=typer.colors.GREEN, bold=True)
        except PackageNotFoundError:
            typer.echo("Version info not found")
        raise typer.Exit()
try:
    PIPELINE_VERSION = version(CLI_APP_NAME)
    __version__ = version(CLI_APP_NAME)
except PackageNotFoundError:
    PIPELINE_VERSION = "unknown"

try:
    from importlib.metadata import version
    __version__ = version(CLI_APP_NAME)
except PackageNotFoundError:
    # fallback if running from source
    try:
        with open(Path(__file__).parent / "VERSION") as f:
            __version__ = f.read().strip()
    except FileNotFoundError:
        __version__ = "dev"

### Pipeline CLI

app = typer.Typer(help="CLI for running pipeline workspaces.")


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


@app.command()
def run(
    workspace: str = typer.Option(None, help="Workspace to run"),
):
    """
    Import and run a workspace's main() function.
    """
    # Determine workspace name
    from pipeline.workspace_manager import WorkspaceManager
    if workspace is None:
        workspace = WorkspaceManager.identify_default_workspace_name()
    wm = WorkspaceManager(workspace)

    workspace_dir = wm.get_workspace_dir()
    module_path = f"workspaces.{workspace}.main"

    typer.echo(f"🚀 Running {module_path} from {workspace_dir}")

    try:
        mod = importlib.import_module(module_path)
        if not hasattr(mod, "main"):
            typer.echo("❌ This workspace does not have a 'main()' function.")
            raise typer.Exit(1)
        mod.main()
    except Exception as e:
        typer.echo(f"💥 Error while running {workspace}: {e}")
        raise typer.Exit(1)

@app.command()
def typical(zd: str):
    """
    Print the typical idcs list for an EDS zd.
    """
    pass

@app.command()
def trend(
    idcs: list[str] = typer.Argument(..., help="Provide known idcs values that match the given zd."), # , "--idcs", "-i"
    starttime: str = typer.Option(None, "--start", "-s", help="Index from 'mulch order' to choose scaffold source."),
    endtime: str = typer.Option(None, "--end", "-end", help="Reference a known template for workspace organization."),
    zd: str = typer.Option('Maxson', "--zd", "-z", help = "Define the EDS ZD from your secrets file. This must correlate with your idcs point selection(s)."),
    workspacename: str = typer.Option(None,"--workspace","-w", help = "Provide the name of the workspace you want to use, for the secrets.yaml credentials and for the timezone config. If a start time is not provided, the workspace queries can checked for the most recent successful timestamp. "),
    print_csv: bool = typer.Option(False,"--print-csv","-p",help = "Print the CSV style for pasting into Excel."),
    step_seconds: int = typer.Option(None, "--step-seconds", help="You can explicitly provide the delta between datapoints. If not, ~400 data points will be used, based on the nice_step() function.") 
    ):
    """
    Show a curve for a sensor over time.
    """
    #from dateutil import parser
    import pendulum
    from pipeline.api.eds import EdsClient, load_historic_data
    from pipeline import helpers
    from pipeline.plotbuffer import PlotBuffer
    from pipeline import environment
    from pipeline.workspace_manager import WorkspaceManager
    workspaces_dir = WorkspaceManager.ensure_appdata_workspaces_dir()

    # must set up %appdata for pip/x installation. Use mulch or yeoman for this. And have a secrets filler.
    if workspacename is None:
        workspacename = WorkspaceManager.identify_default_workspace_name()
    wm = WorkspaceManager(workspacename)
    secrets_file_path = wm.get_secrets_file_path()
    secrets_dict = SecretConfig.load_config(secrets_file_path)

    if zd.lower() == "stiles":
        zd = "WWTF"

    if zd == "Maxson":
        idcs_to_iess_suffix = ".UNIT0@NET0"
    elif zd == "WWTF":
        idcs_to_iess_suffix = ".UNIT1@NET1"
    else:
        # assumption
        idcs_to_iess_suffix = ".UNIT0@NET0"
    iess_list = [x+idcs_to_iess_suffix for x in idcs]

    base_url = secrets_dict.get("eds_apis", {}).get(zd, {}).get("url").rstrip("/")
    session = EdsClient.login_to_session(api_url = base_url,
                                                username = secrets_dict.get("eds_apis", {}).get(zd, {}).get("username"),
                                                password = secrets_dict.get("eds_apis", {}).get(zd, {}).get("password"))
    session.base_url = base_url
    session.zd = secrets_dict.get("eds_apis", {}).get(zd, {}).get("zd")
    

    if starttime is None:
        # back_to_last_success = True
        from pipeline.queriesmanager import QueriesManager
        queries_manager = QueriesManager(wm)
        dt_start = queries_manager.get_most_recent_successful_timestamp(api_id=zd)
    else:
        dt_start = pendulum.parse(starttime, strict=False)
    if endtime is None:
        dt_finish = helpers.get_now_time_rounded(wm)
    else:
        dt_finish = pendulum.parse(endtime, strict=False)

    # Should automatically choose time step granularity based on time length; map 
    if step_seconds is None:
        step_seconds = helpers.nice_step(TimeManager(dt_finish).as_unix()-TimeManager(dt_start.as_unix())) # TimeManager(starttime).as_unix()
    results = load_historic_data(session, iess_list, dt_start, dt_finish, step_seconds) 
    if not results:
        return 

    data_buffer = PlotBuffer()
    for idx, rows in enumerate(results):
        for row in rows:
            #label = f"({row.get('units')})"
            label = iess_list[0]
            ts = helpers.iso(row.get("ts"))
            av = row.get("value")
            #print(f"{round(av,2)}")
            data_buffer.append(label, ts, av) # needs to be adapted for multiple iess sensor results
    #print(f"data_buffer = {data_buffer}")
    #print(f"data_buffer.get_all() = {data_buffer.get_all()}")
    if not environment.matplotlib_enabled():
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
    

@app.command()
def list_workspaces():
    """
    List all available workspaces detected in the workspaces folder.
    """
    # Determine workspace name
    
    workspace = WorkspaceManager.identify_default_workspace_name()
    wm = WorkspaceManager(workspace)
    workspaces = wm.get_all_workspaces_names()
    typer.echo("📦 Available workspaces:")
    for name in workspaces:
        typer.echo(f" - {name}")

@app.command()
def demo_rjn_ping():
    """
    Demo function to ping RJN service.
    """
    from pipeline.api.rjn import RjnClient
    from pipeline.calls import call_ping
    from pipeline.env import SecretConfig
    from pipeline.workspace_manager import WorkspaceManager
    from pipeline import helpers
    import logging

    logger = logging.getLogger(__name__)
    workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())    
    base_url = secrets_dict.get("contractor_apis", {}).get("RJN", {}).get("url").rstrip("/")
    session = RjnClient.login_to_session(api_url = base_url,
                                    client_id = secrets_dict.get("contractor_apis", {}).get("RJN", {}).get("client_id"),
                                    password = secrets_dict.get("contractor_apis", {}).get("RJN", {}).get("password"))
    if session is None:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.\n")
        return
    else:
        logger.info("RJN session established successfully.")
        session.base_url = base_url
        response = call_ping(session.base_url)

@app.command()
def ping_rjn_services():
    """
    Ping all RJN services found in the secrets configuration.
    """
    from pipeline.calls import find_urls, call_ping
    from pipeline.env import SecretConfig
    from pipeline.workspace_manager import WorkspaceManager
    import logging

    logger = logging.getLogger(__name__)
    workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    
    sessions = {}

    url_set = find_urls(secrets_dict)
    for url in url_set:
        if "rjn" in url.lower():
            print(f"ping url: {url}")
            call_ping(url)

@app.command()
def ping_eds_services():
    """
    Ping all EDS services found in the secrets configuration.
    """
    from pipeline.calls import find_urls, call_ping
    from pipeline.env import SecretConfig
    from pipeline.workspace_manager import WorkspaceManager
    import logging

    logger = logging.getLogger(__name__)
    workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    
    sessions = {}

    url_set = find_urls(secrets_dict)
    typer.echo(f"Found {len(url_set)} URLs in secrets configuration.")
    logger.info(f"url_set: {url_set}")
    for url in url_set:
        if "172.19.4" in url.lower():
            print(f"ping url: {url}")
            call_ping(url)

@app.command()
def daemon_runner_main():
    """
    Run the daemon_runner script from the eds_to_rjn workspace.
    """
    import workspaces.eds_to_rjn.scripts.daemon_runner as dr

    dr.main()

@app.command()
def daemon_runner_once():
    """
    Run the daemon_runner script from the eds_to_rjn workspace.
    """
    import workspaces.eds_to_rjn.scripts.daemon_runner as dr

    dr.run_hourly_tabular_trend_eds_to_rjn()

@app.command()
def help():
    """
    Show help information.
    """
    typer.echo(app.get_help())

if __name__ == "__main__":
    app()
