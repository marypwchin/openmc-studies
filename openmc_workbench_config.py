"""Shared nuclear-data locations; importing this module performs no installation.

Install this repository into the notebook kernel's environment with pip install -e .
Edit DATA_ROOT here if your installation is outside ~/data.
"""
from pathlib import Path

DATA_ROOT = Path.home() / "data"
ENDF_B81 = DATA_ROOT / "endf-b8.1"
