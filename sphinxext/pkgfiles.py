# -*- coding: utf-8 -*-
"""
Autorun-related directives with ``pkg_examples`` as the default directory
"""

from autorun import RunBlock, AddVars
from writefile import WriteFile

class PkgRun(RunBlock):
    default_cwd = 'pkg_examples'


class PkgWrite(WriteFile):
    default_cwd = 'pkg_examples'


class PkgVars(AddVars):
    default_cwd = 'pkg_examples'


def setup(app):
    app.add_directive('pkgrun', PkgRun)
    app.add_directive('pkgwrite', PkgWrite)
    app.add_directive('pkgvars', PkgVars)

# vim: set expandtab shiftwidth=4 softtabstop=4 :
