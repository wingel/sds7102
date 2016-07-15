#! /usr/bin/python
import sys

# Set up paths to myhdl and rhea
paths = [
    '../../../myhdl',
    '../../../rhea',
    ]
for path in paths:
    if path not in sys.path:
        sys.path.append(path)

# I'm using an ancient python-mode in Emacs to edit Python code.  It
# runs directly out of the edit buffer and sys.argv[0] is empty.
# MyHDL needs to reread and parse the source code, so use the filename
# passed to this function to reexecute python if needed.
def reexec_if_needed(fn):
    if not sys.argv[0]:
        import os
        os.execvp('python', [ 'python', fn ])

