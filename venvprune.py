#!/usr/bin/env python3

import argparse
import os
import shutil
from pathlib import Path

import questionary


SKIP_DIRS = {
    ".git", "node_modules", ".Trash",
    ".cache", "Library", ".npm",
    ".next", ".venv", "venv", "__pycache__",
}


def format_size(size):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def get_size(path):
    total = 0
    for root, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = [
            d for d in dirs
            if not (Path(root) / d).is_symlink()
        ]
        for name in files:
            try:
                total += (Path(root) / name).lstat().st_size
            except OSError:
                continue
    return total


def find_venvs(start):
    results = []

    for root, dirs, files in os.walk(start, followlinks=False):
        current = Path(root)

        if "pyvenv.cfg" in files:
            size = get_size(current)
            results.append((current, size))
            dirs[:] = []
            continue

        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS
            and not (current / d).is_symlink()
        ]

        # Check excluded directory names that could be venvs.
        for name in (".venv", "venv"):
            candidate = current / name
            if (
                candidate.is_dir()
                and not candidate.is_symlink()
                and (candidate / "pyvenv.cfg").is_file()
            ):
                results.append((candidate, get_size(candidate)))

    return sorted(results, key=lambda x: x[1], reverse=True)


def main():
    parser = argparse.ArgumentParser(
        description="Interactively find and remove Python venvs"
    )
    parser.add_argument(
        "directory", nargs="?", default=".",
        help="Directory to scan (default: current directory)"
    )
    args = parser.parse_args()

    start = Path(args.directory).expanduser().resolve()

    if not start.is_dir():
        print(f"Not a directory: {start}")
        return

    print(f"\nScanning {start} for Python environments...\n")

    while True:
        venvs = find_venvs(start)

        if not venvs:
            print("No virtual environments found.")
            return

        total = sum(size for _, size in venvs)

        choices = [
            questionary.Choice(
                title=f"{format_size(size):>10}   {path}",
                value=str(path),
            )
            for path, size in venvs
        ]

        print(
            f"\nFound {len(venvs)} environments "
            f"({format_size(total)} total)\n"
        )

        selected = questionary.checkbox(
            "Select environments to delete:",
            choices=choices,
            instruction=(
                "↑↓ navigate, Space select, "
                "A toggle all, Enter confirm"
            ),
        ).ask()

        if selected is None or not selected:
            print("No environments deleted.")
            return

        selected_set = set(selected)
        selected_size = sum(
            size for path, size in venvs
            if str(path) in selected_set
        )

        print(
            f"\nSelected {len(selected)} environments "
            f"({format_size(selected_size)}):"
        )

        for path in selected:
            print(f"  {path}")

        confirm = questionary.confirm(
            f"Delete these environments permanently?",
            default=False,
        ).ask()

        if not confirm:
            again = questionary.confirm(
                "Return to selection?", default=True
            ).ask()
            if not again:
                return
            continue

        for path_string in selected:
            path = Path(path_string)

            try:
                # Revalidate before destructive operation.
                if (
                    path.is_symlink()
                    or not path.is_dir()
                    or not (path / "pyvenv.cfg").is_file()
                    or not path.resolve().is_relative_to(start)
                    or path.resolve() == start
                ):
                    print(f"Skipped unsafe path: {path}")
                    continue

                shutil.rmtree(path)
                print(f"Deleted: {path}")

            except OSError as exc:
                print(f"Failed: {path}: {exc}")

        if not questionary.confirm(
            "Scan again?", default=False
        ).ask():
            return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
