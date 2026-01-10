"""CLI"""

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table
from sqlalchemy.exc import NoResultFound, OperationalError

from snipster import Language, Snippet
from snipster.exceptions import SnippetNotFoundError
from snipster.repositories.backend import create_repository

app = typer.Typer()
console = Console()


def create_table_header(title: str | None = None) -> Table:
    """Create Rich table header"""
    table = Table(title=title)
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Code", style="magenta")
    table.add_column("Description", style="dim")
    table.add_column("Language", justify="center", style="blue")
    table.add_column("Tags", style="yellow")
    table.add_column("Favorite", justify="center", style="red")
    table.add_column("Created", justify="right", style="green")

    return table


@app.callback()
def init(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    if not verbose:
        logger.remove()
        logger.add(lambda msg: None, level="ERROR")

    ctx.obj = create_repository()


@app.command()
def add(
    title: str = typer.Option(..., prompt=True),
    code: str = typer.Option(..., prompt=True),
    description: str = typer.Option(None, help="Optional description"),
    language: str = typer.Option(
        Language.PYTHON.value,
        help=f"Programming language. Valid: {'|'.join(lang for lang in Language)}",
    ),
    tags: str = typer.Option(None, help="Optional comma separated tags"),
    favorite: bool = typer.Option(default=False, help="Favourite snippet"),
    ctx: typer.Context = None,
):
    """Add a new code snippet"""
    repo = ctx.obj
    repo.add(
        Snippet(
            title=title,
            code=code,
            description=description,
            language=language,
            tags=tags,
            favorite=favorite,
        )
    )
    # typer.secho(f" Added snippet: {title}")
    console.print(
        f":white_check_mark: [bold green]Snippet '{title}' added[/bold green]"
    )


@app.command()
def list(ctx: typer.Context = None):
    """List snippets"""
    repo = ctx.obj
    all_snippets = repo.list()

    table = create_table_header(title=":heavy_check_mark: List of snippets")
    if all_snippets:
        for snippet in all_snippets:
            table.add_row(
                str(snippet.id),
                snippet.title,
                snippet.code,
                snippet.description,
                snippet.language.value,
                snippet.tags or "-",
                ":star:" if snippet.favorite else "",
                snippet.created_at.strftime("%Y-%m-%d") if snippet.created_at else "-",
            )
    if not all_snippets:
        console.print("[yellow]No snippets found[/yellow]")
    console.print(table)


@app.command()
def get(snippet_id: int = typer.Option(..., prompt=True), ctx: typer.Context = None):
    """Get single snippet"""
    repo = ctx.obj
    snippet = repo.get(snippet_id)

    if snippet:
        table = create_table_header(
            title=f":heavy_check_mark: Details of Snippet {snippet_id}"
        )
        table.add_row(
            str(snippet.id),
            snippet.title,
            snippet.code,
            snippet.description,
            snippet.language.value,
            snippet.tags or "-",
            ":star:" if snippet.favorite else "",
            snippet.created_at.strftime("%Y-%m-%d") if snippet.created_at else "-",
        )
        console.print(table)
    else:
        console.print()
        console.print(f"[yellow]No snippet found for id {snippet_id}[/yellow]")
        raise typer.Exit(code=1)


@app.command()
def delete(snippet_id: int = typer.Option(..., prompt=True), ctx: typer.Context = None):
    """Delete single snippet"""
    repo = ctx.obj

    try:
        repo.delete(snippet_id)
        console.print(
            f":white_check_mark: [bold green]Snippet '{snippet_id}' deleted[/bold green]"
        )
    except NoResultFound:
        console.print(
            f":cross_mark: [bold red]Snippet '{snippet_id}' not found[/bold red]"
        )
        raise typer.Exit(code=1)
    except OperationalError as err:
        console.print(f"[bold red] Operational Error: {err}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def search(
    term: str = typer.Option(..., prompt=True, help="Search term"),
    language: str = typer.Option(None, help="Language search is optional"),
    ctx: typer.Context = None,
):
    """Search for term in snippet"""
    repo = ctx.obj

    try:
        matches = repo.search(term, language=language)
        table = create_table_header(title=f"Search results for term {term}")
        for snippet in matches:
            table.add_row(
                str(snippet.id),
                snippet.title,
                snippet.code,
                snippet.description,
                snippet.language.value,
                snippet.tags or "-",
                ":star:" if snippet.favorite else "",
                snippet.created_at.strftime("%Y-%m-%d") if snippet.created_at else "-",
            )
        console.print(table)
    except ValueError:
        console.print(f"[yellow]No matches found for {term}[/yellow]")
        raise typer.Exit(code=1)
    except OperationalError as err:
        console.print(f"[bold red] Operational Error: {err}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def toggle_favourite(
    snippet_id: int = typer.Option(..., prompt=True), ctx: typer.Context = None
):
    """Toggle favourite snippet"""
    repo = ctx.obj

    try:
        repo.toggle_favourite(snippet_id)
        console.print(
            f":white_check_mark: [bold green]Snippet '{snippet_id}' favourited[/bold green]"
        )
    except SnippetNotFoundError:
        console.print(
            f":cross_mark: [bold red]Snippet '{snippet_id}' not found[/bold red]"
        )
        raise typer.Exit(code=1)


@app.command()
def tags(
    snippet_id: int = typer.Option(..., prompt=True),
    tags: str = typer.Option(..., prompt=True, help="Add comma separated tags"),
    remove: bool = typer.Option(
        False, prompt=True, help="True to remove tags. Default is False"
    ),
    sort: bool = typer.Option(True, help="True if tags are sorted. Default is True"),
    ctx: typer.Context = None,
):
    """Add comma separted tags to snippet"""
    repo = ctx.obj

    try:
        tags = tags.strip().split(",")
        repo.tags(snippet_id, *tags, remove=remove, sort=sort)
        console.print(
            f":white_check_mark: [bold green]Tags added for Snippet '{snippet_id}'[/bold green]"
        )
    except SnippetNotFoundError:
        console.print(
            f":cross_mark: [bold red]Snippet '{snippet_id}' not found[/bold red]"
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()  # pragma: no cover
