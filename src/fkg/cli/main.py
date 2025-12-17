"""Main CLI entry point for FKG-Core."""

import typer
from rich.console import Console

from fkg.cli.commands import db_app, ingest_app, pkg_app, remote_app

app = typer.Typer(
    name="fkg",
    help="FKG-Core: County-hosted knowledge graph runtime",
    no_args_is_help=True,
)
console = Console()

# Add sub-commands
app.add_typer(db_app, name="db", help="Database operations")
app.add_typer(pkg_app, name="pkg", help="PKG export/import operations")
app.add_typer(ingest_app, name="ingest", help="Data ingestion")
app.add_typer(remote_app, name="remote", help="Federation remote management")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Start the FKG API server."""
    import uvicorn

    from fkg.settings import get_settings

    settings = get_settings()

    # Use settings values if not overridden
    if host == "127.0.0.1":
        host = settings.api.host
    if port == 8000:
        port = settings.api.port

    console.print(f"[green]Starting FKG API server at http://{host}:{port}[/green]")
    console.print(f"[dim]Instance: {settings.instance.id}[/dim]")

    uvicorn.run(
        "fkg.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def whoami():
    """Print instance identity and configuration."""
    from fkg.settings import get_settings
    from fkg.validate.registry import get_registry

    settings = get_settings()
    registry = get_registry()

    console.print("\n[bold]FKG Instance Identity[/bold]\n")
    console.print(f"  [cyan]ID:[/cyan] {settings.instance.id}")
    console.print(f"  [cyan]Authority Name:[/cyan] {settings.instance.authority_name}")
    console.print(f"  [cyan]Jurisdiction:[/cyan] {settings.instance.jurisdiction}")
    console.print(f"  [cyan]Schema Version:[/cyan] {settings.instance.schema_version}")

    if settings.instance.public_key:
        console.print(f"  [cyan]Public Key:[/cyan] {settings.instance.public_key}")
    else:
        console.print("  [cyan]Public Key:[/cyan] [dim]Not configured[/dim]")

    console.print("\n[bold]Available Entity Types[/bold]\n")
    for entity_type in registry.list_entity_types():
        console.print(f"  - {entity_type}")

    console.print("\n[bold]Federation Remotes[/bold]\n")
    if settings.federation.remotes:
        for remote in settings.federation.remotes:
            console.print(f"  - {remote.id}: {remote.endpoint}")
    else:
        console.print("  [dim]No remotes configured[/dim]")

    console.print()


@app.command()
def pull(
    remote_id: str = typer.Argument(..., help="ID of remote to pull from"),
):
    """Pull latest PKG from a remote."""
    from fkg.federation.pull import pull_remote
    from fkg.db import get_sync_session
    from fkg.settings import get_settings

    settings = get_settings()

    # Find remote config
    remote_config = None
    for remote in settings.federation.remotes:
        if remote.id == remote_id:
            remote_config = remote
            break

    if remote_config is None:
        console.print(f"[red]Remote not found: {remote_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Pulling from remote: {remote_id}[/cyan]")
    console.print(f"[dim]Endpoint: {remote_config.endpoint}[/dim]")

    with get_sync_session() as session:
        try:
            stats = pull_remote(session, remote_config)
            console.print("\n[green]Pull completed successfully![/green]")
            console.print(f"  Entities: {stats.get('entities', 0)}")
            console.print(f"  Edges: {stats.get('edges', 0)}")
            console.print(f"  Sources: {stats.get('sources', 0)}")
        except Exception as e:
            console.print(f"[red]Pull failed: {e}[/red]")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
