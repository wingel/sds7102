#! /usr/bin/python
def run_as_module(m):
    import sys
    import os

    print "fifo.run_as_module", (sys.argv[0], __package__)

    if not __package__:
        p = os.path.dirname(sys.argv[0])
        p = os.path.join(p, '..')
        p = os.path.abspath(p)

        os.chdir(p)

        print "reexec from", p
        print

        sys.stdout.flush()

        os.execvp('python', [ 'python', '-m', m ])

    print
    sys.stdout.flush()
