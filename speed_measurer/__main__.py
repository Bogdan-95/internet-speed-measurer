"""Точка входа для запуска пакета через python -m speed_measurer."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
