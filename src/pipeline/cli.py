'''
import typer
from pathlib import Path

app = typer.Typer()

@app.command()
def list_workspaces(workspaces_dir: Path = Path("workspaces")):
    """List valid mulch workspaces in the given directory."""
    if not workspaces_dir.exists():
        typer.echo(f"Directory not found: {workspaces_dir}")
        raise typer.Exit(code=1)
    for path in workspaces_dir.iterdir():
        if path.is_dir() and (path / ".mulch").is_dir():
            typer.echo(f"🪴 {path.name}")

@app.command()
def list_mulch_folders(start: Path = Path(".")):
    """Recursively find folders containing a .mulch/ directory."""
    for path in start.rglob(".mulch"):
        typer.echo(f"📁 {path.parent}")

@app.command()
def inspect(workspace: Path):
    """Show scaffold or metadata info from a workspace."""
    metadata = workspace / ".mulch" / "mulch-scaffold.json"
    if metadata.exists():
        typer.echo(f"🔍 {workspace.name}: {metadata}")
        typer.echo(metadata.read_text())
    else:
        typer.echo(f"No scaffold found in {workspace}")
'''
# src/pipeline/cli.py

import typer
import importlib
from src.pipeline.workspace_manager import WorkspaceManager

app = typer.Typer(help="CLI for running pipeline workspaces.")



@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
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
    if workspace is None:
        workspace = WorkspaceManager.identify_default_workspace()
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
def list_workspaces():
    """
    List all available workspaces detected in the workspaces folder.
    """
    # Determine workspace name
    
    workspace = WorkspaceManager.identify_default_workspace()
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
    from src.pipeline.api.rjn import RjnClient
    from src.pipeline.calls import call_ping
    from src.pipeline.env import SecretConfig
    from src.pipeline.workspace_manager import WorkspaceManager
    from src.pipeline import helpers
    import logging

    logger = logging.getLogger(__name__)
    workspace_name = WorkspaceManager.identify_default_workspace()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    
    api_secrets_r = helpers.get_nested_config(secrets_dict, ["contractor_apis","RJN"])
    session = RjnClient.login_to_session(api_url = api_secrets_r["url"],
                                                client_id = api_secrets_r["client_id"],
                                                password = api_secrets_r["password"])
    if session is None:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.\n")
        return
    else:
        logger.info("RJN session established successfully.")
        #session.custom_dict = api_secrets_r
        #api_url = session.custom_dict["url"]
        session.base_url = api_secrets_r["url"].rstrip("/")
        response = call_ping(session.base_url)

@app.command()
def ping_rjn_services():
    """
    Ping all RJN services found in the secrets configuration.
    """
    from src.pipeline.calls import find_urls, call_ping
    from src.pipeline.env import SecretConfig
    from src.pipeline.workspace_manager import WorkspaceManager
    import logging

    logger = logging.getLogger(__name__)
    workspace_name = WorkspaceManager.identify_default_workspace()
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
    from src.pipeline.calls import find_urls, call_ping
    from src.pipeline.env import SecretConfig
    from src.pipeline.workspace_manager import WorkspaceManager
    import logging

    logger = logging.getLogger(__name__)
    workspace_name = WorkspaceManager.identify_default_workspace()
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
