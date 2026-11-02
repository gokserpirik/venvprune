# venvprune

An interactive command-line tool for finding Python virtual environments and removing the ones you no longer need.

## Requirements and installation

Python 3.9 or newer and an interactive terminal are required. Install from PyPI with:

```sh
python -m pip install venvprune
```

This installs the `venvprune` command and its `questionary` dependency.

## Usage

```sh
venvprune                 # scan the current directory
venvprune ~/projects      # scan a specific directory
venvprune --help
```

Environments are identified by a `pyvenv.cfg` file and displayed largest first. Use the arrow keys to navigate, Space to select, A to toggle all, and Enter to continue. Review the selected paths and confirm before deletion. Declining confirmation lets you return to selection or exit.

**Deletion is permanent.** Selected environment directories and all their contents are removed, not moved to the trash. Review paths carefully and back up anything important. The scan root itself is never deleted, even if it is detected as an environment.

The scan skips symlinked directories and common large or system directories (`.git`, `node_modules`, `.Trash`, `.cache`, `Library`, `.npm`, `.next`, and `__pycache__`). Directories named `.venv` and `venv` are checked as environment candidates but are not otherwise traversed. The size shown is an estimate based on file sizes, not necessarily disk space that will be reclaimed; inaccessible files may be omitted. Inaccessible directories may also be omitted from scan results.

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
```

## License

MIT. The full license is included in the distribution.
