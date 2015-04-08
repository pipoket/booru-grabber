# -*- coding: cp949 -*-
import os
import glob

from distutils.core import setup
from py2exe.build_exe import py2exe


#--------------------------------------------------------------------------
#
# Define our own command class based on py2exe so we can perform some
# customizations, and in particular support UPXing the binary files.
#
#--------------------------------------------------------------------------

class Py2exe(py2exe):

    def initialize_options(self):
        # Add a new "upx" option for compression with upx
        py2exe.initialize_options(self)
        self.upx = 1

    def copy_file(self, *args, **kwargs):
        # Override to UPX copied binaries.
        (fname, copied) = result = py2exe.copy_file(self, *args, **kwargs)

        basename = os.path.basename(fname)
        if (copied and self.upx and
            (basename[:6]+basename[-4:]).lower() != 'python.dll' and
            fname[-4:].lower() in ('.pyd', '.dll')):
            os.system('upx --best "%s"' % os.path.normpath(fname))
        return result

    def patch_python_dll_winver(self, dll_name, new_winver=None):
        # Override this to first check if the file is upx'd and skip if so
        if not self.dry_run:
            if not os.system('upx -qt "%s" >nul' % dll_name):
                if self.verbose:
                    print "Skipping setting sys.winver for '%s' (UPX'd)" % \
                          dll_name
            else:
                py2exe.patch_python_dll_winver(self, dll_name, new_winver)
                # We UPX this one file here rather than in copy_file so
                # the version adjustment can be successful
                if self.upx:
                    os.system('upx --best "%s"' % os.path.normpath(dll_name))


setup(windows=[{"script": "grabber.py"}],
      options={
          "py2exe": {
              "compressed": True,
              "optimize": 2,
              "bundle_files": 3,
              "packages": ["twisted.internet", "twisted.web", "zope.interface"],
              "excludes": ["_ssl", "doctest", "pdb", "unittest", "difflib",
                           "optparse", "_gtkagg", "_tkagg",
                           "bsddb", "curses", "email", "pywin.debugger", "tcl",
                           "pywin.debugger.dbgcon", "pywin.dialogs", "Tkconstants",
                           "Tkinter"],
              "dll_excludes": ['libgdk-win32-2.0-0.dll',  'libgobject-2.0-0.dll', 
                               'tcl84.dll', 'tk84.dll', 'mswsock.dll',
                               'powrprof.dll'],
              }
          },
      cmdclass={"py2exe": Py2exe},
)
