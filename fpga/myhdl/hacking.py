#! /usr/bin/python
def reexec(p):
    import sys
    import os
    if not sys.argv[0]:
        os.execvp('python', [ 'python', p ])

def run_as_module(m):
    import sys

    print "run_as_module", (sys.argv[0], __package__)
    print
    sys.stdout.flush()
