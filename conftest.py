"""Make the repo root importable so `import treestoseas` works without installing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
