import typer
import shutil
from pathlib import Path
import re
import markdown2
import yaml
from rich.console import Console

app = typer.Typer()

# Regex patterns for LaTeX, Markdown, and Quarto media links
LATEX_MEDIA_PATTERN = re.compile(r'\\includegraphics\{([^}]+)\}')
MD_MEDIA_PATTERN = re.compile(r'!\[.*?\]\((.*?)\)')
QUARTO_PATTERN = re.compile(
    r'(?<=[:=]\s)["\']?([^"\',\s]+)["\']?'   # Match value after colon or equal sign
    r'|!\[.*?\]\((.*?)\)',                   # Match markdown image paths
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

    # Flatten the matches since regex might return groups
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
        else:
            typer.echo(f"Invalid or unsupported path: {full_path}")

    return valid_paths, valid_old_paths


def copy_files(media_paths, report_file: Path, dest_dir: Path):
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
            typer.echo(f"Copied: {full_path}")
        else:
            typer.echo(f"Warning: {full_path} not found or unsupported extension.")


def replace_media_paths(content, old_paths, new_paths):
    """
    Replace old media paths with new paths in the content.
    """
    for old_path, new_path in zip(old_paths, new_paths):
        content = content.replace(str(old_path), str(new_path))
    return content


def parse_latex_file(file_path: Path, dest_dir: Path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    media_paths = find_latex_media(content)
    copy_files(media_paths, file_path, dest_dir)


def parse_markdown_file(file_path: Path, dest_dir: Path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    media_paths = find_markdown_media(content)
    copy_files(media_paths, file_path, dest_dir)


def parse_quarto_file(file_path: Path, dest_dir: Path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Check for YAML metadata and Markdown content
    # try:
    #     yaml_header, markdown_content = content.split('---', 2)[1:]
    #     yaml_data = yaml.safe_load(yaml_header)
    #     # Handle any media paths declared in the YAML if necessary
    # except ValueError:
    #     markdown_content = content
    media_paths = find_quarto_media(content)
    valid_media_paths, old_valid_media_paths = check_path_validity(media_paths, file_path)
    copy_files(valid_media_paths, file_path, dest_dir)


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
        typer.echo(f"Processing LaTeX file: {report_file}")
        parse_latex_file(report_file, assets_dir)
    elif report_file.suffix in [".md", ".qmd"]:
        typer.echo(f"Processing Markdown/Quarto file: {report_file}")
        if report_file.suffix == ".qmd":
            parse_quarto_file(report_file, assets_dir)
        else:
            parse_markdown_file(report_file, assets_dir)
    else:
        typer.echo("Unsupported file type. Please provide a LaTeX (.tex), Markdown (.md), or Quarto (.qmd) file.")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
