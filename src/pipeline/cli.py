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
from pipeline.workspace_manager import WorkspaceManager

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



if __name__ == "__main__":
    app()
