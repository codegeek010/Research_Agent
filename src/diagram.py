import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from graph import get_mermaid

if __name__ == "__main__":
    print(get_mermaid())
