import os
import regex
from typing import Iterator


def reglob(root: str, pattern: str) -> Iterator[str]:
    """
    Walk *root* recursively and yield absolute paths whose path
    relative to *root* satisfies a full match against *pattern*.

    Relative paths are normalized with forward slashes.
    Subdirectories whose relative path is not a valid partial match
    of the pattern are pruned — os.walk never descends into them.

    Args:
        root:    Root directory to search from.
        pattern: Regular expression matched against the normalized
                 (forward-slash) relative path of each file.

    Yields:
        Absolute paths of matching files.
    """
    compiled = regex.compile(pattern)

    for dirpath, dirnames, filenames in os.walk(root):
        # Normalized relative path of the current directory
        rel = os.path.relpath(dirpath, root).replace(os.sep, '/')
        if rel == '.':
            rel = ''

        # Yield files whose relative path fully matches the pattern
        for fname in filenames:
            frel = f"{rel}/{fname}" if rel else fname
            if compiled.fullmatch(frel):
                yield os.path.join(dirpath, fname)

        # Prune subdirectories that cannot lead to any match.
        # A subdirectory rel_dir is worth entering only if
        # rel_dir + "/" is a valid *partial* match of the pattern,
        # i.e. the regex engine can still reach an accepting state
        # by consuming more characters.
        dirnames[:] = [
            d for d in dirnames
            if compiled.match(
                (f"{rel}/{d}" if rel else d) + '/',
                partial=True
            )
        ]
