import typer
import os
import shutil
from typing import Optional
from typing_extensions import Annotated
from .config import load_config
from .indexer import Indexer
from .state import StateManager
from .server import start_server

app = typer.Typer(add_completion=False)

@app.command()
def main(
    dir_path: Annotated[Optional[str], typer.Option("--dir", "-d", help="Target directory path")] = None,
    config_path: Annotated[str, typer.Option("--config", "-c", help="Config file path")] = "config.yaml",
    clean: Annotated[bool, typer.Option("--clean", "-cl", help="Clean RAG database")] = False,
    backup: Annotated[bool, typer.Option("--backup", "-b", help="Backup RAG database")] = False,
    backup_path: Annotated[Optional[str], typer.Option("--backup-path", "-bp", help="Backup storage path")] = None,
    serve: Annotated[bool, typer.Option("--serve", "-s", help="Start MCP server after processing")] = False,
    version: Annotated[bool, typer.Option("--version", "-v", help="Show version")] = False,
):
    """
    RAG MCP Tool CLI.
    If no arguments are provided, starts the MCP server.
    """
    if version:
        print("RAG MCP Tool v0.1.0")
        return

    # If clean or backup is requested, dir_path is required
    if clean:
        if not dir_path:
            typer.echo("Error: --dir is required for --clean", err=True)
            raise typer.Exit(code=1)
        
        target_dir = os.path.abspath(dir_path)
        rag_dir = os.path.join(target_dir, ".muxue_rag")
        if os.path.exists(rag_dir):
            confirm = typer.confirm(f"Are you sure you want to delete {rag_dir}?")
            if confirm:
                shutil.rmtree(rag_dir)
                StateManager.remove_directory(target_dir)
                typer.echo("Cleaned up database.")
        else:
            typer.echo("No database found to clean.")
        return

    if backup:
        if not dir_path:
            typer.echo("Error: --dir is required for --backup", err=True)
            raise typer.Exit(code=1)
        if not backup_path:
            typer.echo("Error: --backup-path is required for --backup", err=True)
            raise typer.Exit(code=1)
            
        target_dir = os.path.abspath(dir_path)
        rag_dir = os.path.join(target_dir, ".muxue_rag")
        if os.path.exists(rag_dir):
            shutil.copytree(rag_dir, backup_path, dirs_exist_ok=True)
            typer.echo(f"Backup created at {backup_path}")
        else:
            typer.echo("No database found to backup.")
        return

    if dir_path:
        # Validate directory
        if not os.path.exists(dir_path):
            typer.echo("Error: Directory does not exist", err=True)
            raise typer.Exit(code=1)
        if not os.path.isdir(dir_path):
            typer.echo("Error: Path is not a directory", err=True)
            raise typer.Exit(code=1)

        # If only indexing (no serve), perform indexing
        if not serve:
            config = load_config(config_path)
            indexer = Indexer(dir_path, config)
            indexer.index()

            # Add to state
            StateManager.add_directory(dir_path)
            return

    # Start Server
    print("Starting MCP Server...")
    if config_path != "config.yaml":
        os.environ["RAG_MCP_CONFIG"] = config_path
    
    # If we are serving a specific directory (passed via --dir and --serve)
    if dir_path and serve:
        os.environ["RAG_MCP_SERVE_DIR"] = os.path.abspath(dir_path)
        
    start_server()

if __name__ == "__main__":
    app()
