# pipeline/daemon/__init__.py
from .controller import main_cli

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m pipeline.daemon -start | -stop | -status")
    else:
        main_cli(sys.argv[1])
