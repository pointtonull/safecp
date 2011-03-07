#!/usr/bin/env python
#-*- coding: UTF-8 -*-
from subprocess import Popen, PIPE
import os
import optparse
import sys

class Verbose:
    def __init__(self, verbosity, prefix="", ident=True):
        self.verbosity = False if verbosity < 0 else True
        self.prefix = prefix
        self.ident = ident

    def __call__(self, *args):
        if self.verbosity:
            message = " ".join((unicode(e) for e in args))
            sys.stderr.write("%s%s%s\n" % ("  " * self.get_depth(), self.prefix,
                message))

    def get_depth(self):
        if not self.ident:
            return 0
        else:
            def exist_frame(n):
                try:
                    if sys._getframe(n):
                        return True
                except ValueError:
                    return False

            now = 0
            maxn = 1
            minn = 0

            while exist_frame(maxn):
                minn = maxn
                maxn *= 2

            # minn =< depth < maxn
            middle = (minn + maxn) / 2

            while minn < middle:
                if exist_frame(middle):
                    minn = middle
                else:
                    maxn = middle

                middle = (minn + maxn) / 2

            return max(minn - 3, 0) #4 == len(main, Verbose, get_depth)


def get_options():
    # Instance the parser and define the usage message
    optparser = optparse.OptionParser(usage="""
    %prog [-vq] [-t timeout] [host[:port]]...
    """, version="%prog .1")

    # Define the options and the actions of each one
    optparser.add_option("-v", "--verbose", action="count", dest="verbose",
        help="increase verbosity")
    optparser.add_option("-q", "--quiet", action="count", dest="quiet",
        help="decrease verbosity")
#    optparser.add_option("-t", "--timeout", help=("Timeout in seconds. Can"
#        " be float."), action="store", dest="timeout", type="float")
    optparser.add_option("-r", "--recursive", help=("copy directories"
        " recursively"), action="store_true", dest="recursive")

    # Define the default options
    optparser.set_defaults(verbose=0, quiet=0, timeout=0, recursive=False)

    # Process the options
    return optparser.parse_args()


def safecopy(*args):
    debug(args)
    proc = Popen(["/usr/bin/safecopy"] + list(args), stdout=PIPE, stderr=PIPE)
    proc.wait()
    return proc


def safecp(source, dest):
    def cleanfiles(verbose=debug):
        for file in ("stage3.badblocks", "stage2.badblocks",
            "stage1.badblocks"):
            if os.path.exists(file):
                verbose("%s: exist, removing" % file)
                os.remove(file)

    cleanfiles(warning)

    if not os.path.exists(source):
        error("%s: the file or directory does not exist!")
        return 1

    if os.path.isfile(source):
        if os.path.exists(dest):
            if os.path.isfile(dest):
                info("No dest will be overwrited.")
                return 6
            elif os.path.isdir(dest):
                dest = os.path.join(dest, os.path.basename(source))
                moreinfo("New dest will be %s" % dest)

        info("Coping %s to %s" % (source, dest))
        for stage in (1, 2, 3):
            moreinfo("Starting stage%d" % stage)
            proc = safecopy("--stage%d" % stage, source, dest)
            debug("safecopy stdout:\n%s" % "".join(proc.stdout.readlines()))
            moreinfo("safecopy stderr:\n%s" % "".join(proc.stderr.readlines()))
            if proc.returncode:
                error("safecopy returned %d" % proc.returncode)
                cleanfiles()
                return proc.returncode
        cleanfiles()
        return 0

    elif os.path.isdir(source):
        if not options.recursive:
            error("Omiting the directory: %s" % source)
            return 3
        else:

            result = 0
            for subsource in os.listdir(source):
                complete_subsource = os.path.join(source, subsource)
                subdest = os.path.join(dest, os.path.basename(subsource))
                if not os.path.isdir(subdest):
                    if os.path.isfile(subdest):
                        warning("omiting file: %s" % source)
                        return 4
                    os.mkdir(subdest)
                result += safecp(complete_subsource, subdest)
            return result

    else:
        raise NotImplementedError("Falta escribir esta caracteristica")


def main(options, args):
    if safecopy("--help").returncode:
        error("safecopy executable couldnt be found!")
        return 2
    else:
        if len(args) < 2:
            error("missing file operand. Invoque -h option.")
            return 3
        else:
            sources = args[:-1]
            dest = args[-1]
            if len(sources) > 1 and not os.path.isdir(dest):
                error('%s: target is not a directory' % dest)
                return 4
            else:
                for source in sources:
                    safecp(source, dest)
                return 0


if __name__ == "__main__":
    # == Reading the options of the execution ==
    options, args = get_options()

    error = Verbose(options.verbose - options.quiet + 2, "E: ")
    warning = Verbose(options.verbose - options.quiet + 1, "W: ")
    info = Verbose(options.verbose - options.quiet + 0)
    moreinfo = Verbose(options.verbose - options.quiet -1)
    debug = Verbose(options.verbose - options.quiet - 2, "D: ")

    debug("""Options: '%s', args: '%s'""" % (options, args))

    exit(main(options, args))
