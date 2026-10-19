# conftest.py – makes dashboard/ the root for test imports
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
