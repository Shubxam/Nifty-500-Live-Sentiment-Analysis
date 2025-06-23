import subprocess  # nosec B404

from funlog import log_calls
from rich import get_console, reconfigure
from rich import print as rprint

# Update as needed.
SRC_PATHS = ['tests', 'src']
DOC_PATHS = ['docs', 'readme.md']


reconfigure(
    emoji=not get_console().options.legacy_windows
)  # No emojis on legacy windows.


def main():
    rprint()

    errcount = 0
    errcount += run(
        [
            'uv',
            'run',
            'codespell',
            '--write-changes',
            *SRC_PATHS,
            *DOC_PATHS,
        ]
    )
    errcount += run(['uv', 'run', 'ruff', 'check', '--fix', *SRC_PATHS])
    errcount += run(['uv', 'run', 'ruff', 'format', *SRC_PATHS])
    errcount += run(['uv', 'run', 'ty', 'check', *SRC_PATHS])
    errcount += run(
        [
            'uv',
            'run',
            'bandit',
            '-c',
            'pyproject.toml',
            '-r',
            *SRC_PATHS,
            '.github/workflows',
        ]
    )

    rprint()

    if errcount != 0:
        rprint(f'[bold red]:x: Lint failed with {errcount} errors.[/bold red]')
    else:
        rprint('[bold green]:white_check_mark: Lint passed![/bold green]')
    rprint()

    return errcount


@log_calls(level='warning', show_timing_only=True)
def run(cmd: list[str]) -> int:
    rprint()
    rprint(f'[bold green]>> {" ".join(cmd)}[/bold green]')
    errcount = 0
    try:
        subprocess.run(cmd, text=True, check=True)  # nosec B603
    except KeyboardInterrupt:
        rprint('[yellow]Keyboard interrupt - Cancelled[/yellow]')
        errcount = 1
    except subprocess.CalledProcessError as e:
        rprint(f'[bold red]Error: {e}[/bold red]')
        errcount = 1

    return errcount


if __name__ == '__main__':
    exit(main())
