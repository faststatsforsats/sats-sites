#!/usr/bin/env python3
"""Build one of the three sites, or all of them.

    python3 build.py stats          -> sites/stats/dist/
    python3 build.py facts          -> sites/facts/dist/
    python3 build.py acts           -> sites/acts/dist/
    python3 build.py all            -> all three
    python3 build.py stats out/     -> a different output folder
    python3 build.py all --strict   -> warnings count as errors (the pull request check uses this)

Exit code 0 means the build is clean; 1 means at least one ERROR line was printed.
"""

import sys

from lib.site import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
