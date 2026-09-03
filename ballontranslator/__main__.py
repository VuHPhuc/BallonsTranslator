import sys
from .launch import main


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code if isinstance(exit_code, int) else 0)
