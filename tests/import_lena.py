import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lena

# Then, within the individual test modules, import the module like so:
# 
# from .import_lena import lena
## from https://docs.python-guide.org/writing/structure/#test-suite
