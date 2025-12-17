"""CLI sub-commands for FKG-Core."""

import json
from pathlib import Path

import typer
from rich.console import Console

console = Console()

# Database commands
db_app = typer.Typer(help="Database operations")


@db_app.command("init")
def db_init():
    """Initialize or migrate the database."""
    from alembic import command
    from alembic.config import Config

    from fkg.settings import get_settings

    settings = get_settings()

    console.print("[cyan]Initializing database...[/cyan]")
    console.print(f"[dim]Database URL: {settings.database.url.split('@')[-1]}[/dim]")

    # Find alembic.ini
    alembic_ini = Path(__file__).parent.parent.parent.parent.parent / "alembic.ini"
    if not alembic_ini.exists():
        alembic_ini = Path.cwd() / "alembic.ini"

    if not alembic_ini.exists():
        console.print("[red]alembic.ini not found[/red]")
        raise typer.Exit(1)

    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database.url)

    try:
        command.upgrade(alembic_cfg, "head")
        console.print("[green]Database initialized successfully![/green]")
    except Exception as e:
        console.print(f"[red]Database initialization failed: {e}[/red]")
        raise typer.Exit(1)


@db_app.command("status")
def db_status():
    """Check database connection and migration status."""
    from fkg.db import check_database_connection

    if check_database_connection():
        console.print("[green]Database connection: OK[/green]")
    else:
        console.print("[red]Database connection: FAILED[/red]")
        raise typer.Exit(1)


# PKG commands
pkg_app = typer.Typer(help="PKG export/import operations")


@pkg_app.command("export")
def pkg_export(
    out: Path = typer.Option("./pkg", "--out", "-o", help="Output directory"),
    no_changelog: bool = typer.Option(False, "--no-changelog", help="Exclude changelog"),
):
    """Export PKG snapshot to directory."""
    from fkg.db import get_sync_session
    from fkg.pkg.export import export_pkg

    console.print(f"[cyan]Exporting PKG to {out}[/cyan]")

    session = get_sync_session()
    try:
        stats = export_pkg(
            session,
            out,
            include_changelog=not no_changelog,
        )
        session.commit()

        console.print("\n[green]Export completed![/green]")
        console.print(f"  Entities: {stats['entities']}")
        console.print(f"  Edges: {stats['edges']}")
        console.print(f"  Sources: {stats['sources']}")
        console.print(f"  Manifest: {stats['manifest']}")
    except Exception as e:
        session.rollback()
        console.print(f"[red]Export failed: {e}[/red]")
        raise typer.Exit(1)
    finally:
        session.close()


@pkg_app.command("import")
def pkg_import(
    path: Path = typer.Option(..., "--path", "-p", help="Path to PKG directory"),
    authority: str = typer.Option("local", "--authority", "-a", help="Authority: 'local' or remote ID"),
    skip_verify: bool = typer.Option(False, "--skip-verify", help="Skip checksum verification"),
    skip_validate: bool = typer.Option(False, "--skip-validate", help="Skip schema validation"),
):
    """Import PKG from directory."""
    from fkg.db import get_sync_session
    from fkg.pkg.import_ import import_pkg

    console.print(f"[cyan]Importing PKG from {path}[/cyan]")
    console.print(f"[dim]Authority: {authority}[/dim]")

    session = get_sync_session()
    try:
        stats = import_pkg(
            session,
            path,
            authority=authority,
            verify_checksums_flag=not skip_verify,
            validate=not skip_validate,
        )

        console.print("\n[green]Import completed![/green]")
        console.print(f"  Entities: {stats['entities']}")
        console.print(f"  Edges: {stats['edges']}")
        console.print(f"  Sources: {stats['sources']}")
        console.print(f"  Authority ID: {stats['authority_id']}")
    except Exception as e:
        session.rollback()
        console.print(f"[red]Import failed: {e}[/red]")
        raise typer.Exit(1)
    finally:
        session.close()


@pkg_app.command("validate")
def pkg_validate(
    path: Path = typer.Option(..., "--path", "-p", help="Path to PKG directory"),
):
    """Validate a PKG without importing."""
    from fkg.pkg.import_ import validate_pkg

    console.print(f"[cyan]Validating PKG at {path}[/cyan]")

    results = validate_pkg(path)

    if results["valid"]:
        console.print("\n[green]PKG is valid![/green]")
    else:
        console.print("\n[red]PKG validation failed![/red]")

    if results["errors"]:
        console.print("\n[red]Errors:[/red]")
        for error in results["errors"]:
            console.print(f"  - {error}")

    if results["warnings"]:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in results["warnings"]:
            console.print(f"  - {warning}")

    if results["manifest"]:
        console.print("\n[bold]Manifest Info:[/bold]")
        manifest = results["manifest"]
        console.print(f"  Authority: {manifest.get('authority_id')}")
        console.print(f"  Created: {manifest.get('created_at')}")
        counts = manifest.get("counts", {})
        console.print(f"  Entities: {counts.get('entities', 0)}")
        console.print(f"  Edges: {counts.get('edges', 0)}")
        console.print(f"  Sources: {counts.get('sources', 0)}")

    if not results["valid"]:
        raise typer.Exit(1)


# Ingest commands
ingest_app = typer.Typer(help="Data ingestion")


@ingest_app.command("csv")
def ingest_csv(
    path: Path = typer.Option(..., "--path", "-p", help="Path to CSV file"),
    entity_type: str = typer.Option(..., "--entity-type", "-t", help="Entity type"),
    name_column: str = typer.Option("name", "--name-column", help="Column for entity name"),
    skip_validate: bool = typer.Option(False, "--skip-validate", help="Skip schema validation"),
):
    """Import entities from a CSV file."""
    import csv

    from fkg.db import get_sync_session
    from fkg.storage.entities import EntityStorage

    console.print(f"[cyan]Importing CSV from {path}[/cyan]")
    console.print(f"[dim]Entity type: {entity_type}[/dim]")

    session = get_sync_session()
    storage = EntityStorage(session)
    count = 0
    errors = 0

    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    data = {
                        "type": entity_type,
                        "name": row.get(name_column, ""),
                        **{k: v for k, v in row.items() if v},  # Include non-empty fields
                    }
                    storage.upsert(data, validate=not skip_validate)
                    count += 1
                except Exception as e:
                    errors += 1
                    console.print(f"[yellow]Row error: {e}[/yellow]")

        session.commit()
        console.print(f"\n[green]Imported {count} entities ({errors} errors)[/green]")
    except Exception as e:
        session.rollback()
        console.print(f"[red]Import failed: {e}[/red]")
        raise typer.Exit(1)
    finally:
        session.close()


@ingest_app.command("jsonl")
def ingest_jsonl(
    path: Path = typer.Option(..., "--path", "-p", help="Path to JSONL file"),
    skip_validate: bool = typer.Option(False, "--skip-validate", help="Skip schema validation"),
):
    """Import entities/edges from a JSONL file."""
    from fkg.db import get_sync_session
    from fkg.storage.edges import EdgeStorage
    from fkg.storage.entities import EntityStorage

    console.print(f"[cyan]Importing JSONL from {path}[/cyan]")

    session = get_sync_session()
    entity_storage = EntityStorage(session)
    edge_storage = EdgeStorage(session)
    entity_count = 0
    edge_count = 0
    errors = 0

    try:
        with open(path) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # Determine if entity or edge
                    if "src_id" in data and "dst_id" in data:
                        edge_storage.upsert(data, validate=not skip_validate)
                        edge_count += 1
                    elif "type" in data:
                        entity_storage.upsert(data, validate=not skip_validate)
                        entity_count += 1
                    else:
                        console.print(f"[yellow]Line {line_num}: Unknown record type[/yellow]")
                        errors += 1
                except Exception as e:
                    errors += 1
                    console.print(f"[yellow]Line {line_num}: {e}[/yellow]")

        session.commit()
        console.print(f"\n[green]Imported {entity_count} entities, {edge_count} edges ({errors} errors)[/green]")
    except Exception as e:
        session.rollback()
        console.print(f"[red]Import failed: {e}[/red]")
        raise typer.Exit(1)
    finally:
        session.close()


@ingest_app.command("markdown")
def ingest_markdown(
    path: Path = typer.Option(..., "--path", "-p", help="Path to markdown directory"),
):
    """Import from Markdown vault (placeholder adapter).

    This is a placeholder for the Markdown importer. Full parsing can be
    deferred, but the interface is established here.
    """
    console.print(f"[cyan]Markdown import from {path}[/cyan]")
    console.print("[yellow]Note: Markdown importer is a placeholder in v0.1[/yellow]")
    console.print("[dim]Full parsing to be implemented in a future version.[/dim]")

    # Count .md files
    md_files = list(path.glob("**/*.md"))
    console.print(f"\nFound {len(md_files)} markdown files")

    # Placeholder: would parse markdown and extract entities/edges
    console.print("\n[yellow]Skipping actual import (placeholder implementation)[/yellow]")


# Remote/Federation commands
remote_app = typer.Typer(help="Federation remote management")


@remote_app.command("add")
def remote_add(
    remote_id: str = typer.Option(..., "--id", help="Remote ID"),
    endpoint: str = typer.Option(..., "--endpoint", help="Remote endpoint URL"),
    pubkey: str = typer.Option(None, "--pubkey", help="Remote public key"),
):
    """Add a federation remote."""
    console.print(f"[cyan]Adding remote: {remote_id}[/cyan]")
    console.print(f"[dim]Endpoint: {endpoint}[/dim]")

    # In v0.1, we just show how to configure - actual persistence would
    # modify the config file or use a remotes table
    console.print("\n[yellow]Note: Add the following to your fkg.yaml:[/yellow]")
    console.print(f"""
federation:
  remotes:
    - id: {remote_id}
      endpoint: {endpoint}
      public_key: {pubkey or 'null'}
      trust:
        verify_signatures: false
        allow_entity_types:
          - organization
          - service
          - location
""")


@remote_app.command("list")
def remote_list():
    """List configured remotes."""
    from fkg.settings import get_settings

    settings = get_settings()

    if not settings.federation.remotes:
        console.print("[dim]No remotes configured[/dim]")
        return

    console.print("\n[bold]Configured Remotes[/bold]\n")
    for remote in settings.federation.remotes:
        console.print(f"  [cyan]{remote.id}[/cyan]")
        console.print(f"    Endpoint: {remote.endpoint}")
        console.print(f"    Verify Signatures: {remote.trust.verify_signatures}")
        console.print(f"    Allowed Types: {', '.join(remote.trust.allow_entity_types)}")
        console.print()
