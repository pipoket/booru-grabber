# -*- coding: cp949 -*-
import os
import sys
import glob
import py2exe
import subprocess

from distutils.core import setup
from cx_Freeze import setup, Executable


if sys.platform != "win32":
    print "This script is only for Win32 build as of now!"
    sys.exit(1)

base = "Win32GUI"

setup(
        name = "booru-grabber",
        version = "0.2.2",
        description = "Booru Grabber",
        options = {
            "build_exe": {
                "includes": ["os"],
                "excludes": ["doctest", "pdb", "unittest", "difflib",
                    "optparse", "_gtkagg", "_tkagg",
                    "bsddb", "curses", "email", "pywin.debugger", "tcl"],
                "compressed": True,
                "optimize": 1,
                "create_shared_zip": True,
                "include_msvcr": True,
            },
        },
        executables = [Executable("grabber.py", base=base)],
)


# Compress the files with UPX
output_path = os.path.join("build", "exe.win32-2.7")
upx_base_args = ["upx", '--best', '--no-progress']

for filename in os.listdir(output_path):
    if (filename == "grabber.exe" or
            os.path.splitext(filename)[1].lower() in ('.exe','.dll','.pyd', '.so')):
        filepath = os.path.join(output_path, filename)
        args = ["upx", "--best", filepath]
        subprocess.call(args)
