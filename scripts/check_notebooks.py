"""Validate notebook schemas without executing cells."""
import sys
import nbformat

for filename in sys.argv[1:]:
    with open(filename) as stream:
        notebook = nbformat.read(stream, as_version=nbformat.NO_CONVERT)
    nbformat.validate(notebook)
    print(f'Valid: {filename}')
