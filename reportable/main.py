import typer
import shutil
from pathlib import Path
import re
import markdown2
import yaml
from rich.console import Console
from subprocess import run

app = typer.Typer()
console = Console()

# Regex patterns for LaTeX, Markdown, and Quarto media links
LATEX_MEDIA_PATTERN = re.compile(r'\\includegraphics\{([^}]+)\}')
MD_MEDIA_PATTERN = re.compile(r'!\[.*?\]\((.*?)\)')
QUARTO_PATTERN = re.compile(
    r'(?::\s*["\']?([^"\',\s]+)["\']?)'     # Match colon followed by optional quotes around a value
    r'|(?:=\s*["\']?([^"\',\s]+)["\']?)'    # Match equal sign followed by optional quotes around a value
    r'|!\[.*?\]\((.*?)\)'                   # Match markdown image paths
    r'|(?<=:\s)["\']?([^"\',\s]+)["\']?',    # Special handling for YAML key-value lines after colon
    re.MULTILINE
)

# Supported file extensions for media
SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".mp4", ".mp3", ".wav"]


def find_latex_media(content: str):
    return LATEX_MEDIA_PATTERN.findall(content)


def find_markdown_media(content: str):
    return MD_MEDIA_PATTERN.findall(content)


def find_quarto_media(content: str):
    """
    Finds media paths in Quarto files from YAML headers, inline attributes, and markdown syntax.
    """
    matches = QUARTO_PATTERN.findall(content)
    media_paths = [m for group in matches for m in group if m]
    return media_paths


def check_path_validity(paths, report_file: Path):
    """
    Checks if extracted paths are valid media files with supported extensions.
    Returns a list of valid media paths.
    """
    valid_paths = []
    valid_old_paths = []
    for path in paths:
        media_path = Path(path)
        old_media_path = Path(media_path)
        
        # If the path is relative, resolve it based on the report's location
        if not media_path.is_absolute():
            full_path = report_file.parent / media_path
            full_path = full_path.resolve()
        else:
            full_path = media_path
            full_path = full_path.resolve()

        # Check if file exists and has a supported extension
        if full_path.suffix.lower() in SUPPORTED_EXTENSIONS and full_path.exists():
            valid_paths.append(full_path)
            valid_old_paths.append(old_media_path)
        # else:
        #     typer.echo(f"Invalid or unsupported path: {full_path}")

    return valid_paths, valid_old_paths


def copy_media_files(media_paths, report_file: Path, dest_dir: Path):
    """Copy media files to the destination directory."""
    for media_path in media_paths:
        media_path = Path(media_path)

        # If the media path is relative, resolve it with respect to the report file's directory
        if not media_path.is_absolute():
            full_path = report_file.parent / media_path
            full_path = full_path.resolve()
        else:
            full_path = media_path
            full_path = full_path.resolve()

        # Copy media file if it exists and has a valid extension
        if full_path.suffix.lower() in SUPPORTED_EXTENSIONS and full_path.exists():
            dest_path = dest_dir / media_path.name
            shutil.copy(full_path, dest_path)
            msg = f"Copied: [bold green]{full_path.name}[/bold green] to {dest_path.parent}"
            console.print(msg)
        else:
            typer.echo(f"Warning: {full_path} not found or unsupported extension.")


def replace_media_paths(content, old_paths, new_paths):
    """
    Replace old media paths with new paths in the content.
    """
    for old_path, new_path in zip(old_paths, new_paths):
        content = content.replace(str(old_path), str(new_path))
    return content


def make_relative_paths(media_paths, dest_dir):
    parent = dest_dir.name
    new_paths = []
    for media_path in media_paths:
        new_path = Path(parent) / media_path.name
        new_paths.append(new_path)
    return new_paths


def process_latex_file(file_path: Path, dest_dir: Path):
    msg = "[bold red]Not implemented yet![/bold red]"
    console.print(msg)

    # with open(file_path, 'r', encoding='utf-8') as f:
    #     content = f.read()
    # media_paths = find_latex_media(content)
    # copy_files(media_paths, file_path, dest_dir)


def process_markdown_file(file_path: Path, dest_dir: Path):
    msg = "[bold red]Not implemented yet![/bold red]"
    console.print(msg)

    # with open(file_path, 'r', encoding='utf-8') as f:
    #     content = f.read()
    # media_paths = find_markdown_media(content)
    # copy_files(media_paths, file_path, dest_dir)


def process_quarto_file(file_path: Path, dest_dir: Path):
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract media paths and check their validity
    media_paths = find_quarto_media(content)
    valid_media_paths, old_valid_media_paths = check_path_validity(media_paths, file_path)

    # Copy valid media files to the destination directory
    copy_media_files(valid_media_paths, file_path, dest_dir)
    new_relative_paths = make_relative_paths(valid_media_paths, dest_dir)

    # Replace old media paths with new paths in the content
    new_content = replace_media_paths(content, old_valid_media_paths, new_relative_paths)

    # Write new content to a new file
    new_file_path = Path(dest_dir.parent) / file_path.name
    with open(new_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        console.print(f"New file created: [bold green]{new_file_path}[/bold green]")

    # Check if an "_extensions" directory exists and copy it to the destination directory
    extensions_dir = file_path.parent / "_extensions"
    if extensions_dir.exists():
        dest_extensions_dir = Path(dest_dir.parent) / "_extensions"
        shutil.copytree(extensions_dir, dest_extensions_dir)
        console.print(f"Copied: [bold green]{extensions_dir}[/bold green] to {dest_extensions_dir}")

    # Run the Quarto build command
    console.print("Running Quarto build command...")
    build_command = f"quarto render {new_file_path}"
    run(build_command, shell=True)


@app.command()
def extract(
    report_file: Path = typer.Argument(..., help="Path to the report file (LaTeX, Markdown, or Quarto)."),
    output_dir: Path = typer.Argument(..., help="Output directory to copy the linked media files.")
):
    """
    Extract and copy media files linked in a LaTeX, Markdown, or Quarto report.
    """
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    if report_file.suffix == ".tex":
        msg = f"Processing LaTeX file: {report_file}"
        console.print(msg)
        process_latex_file(report_file, assets_dir)
    elif report_file.suffix == ".md":
        msg = f"Processing Markdown file: {report_file}"
        console.print(msg)
        process_markdown_file(report_file, assets_dir)
    elif report_file.suffix == ".qmd":
        msg = f"Processing Quarto file: {report_file}"
        console.print(msg)
        process_quarto_file(report_file, assets_dir)
    else:
        msg = "Unsupported file format. Please provide a LaTeX, Markdown, or Quarto file."
        console.print(msg)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
