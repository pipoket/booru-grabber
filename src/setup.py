# -*- coding: cp949 -*-
import os
import sys
import glob
import py2exe
import subprocess

from distutils.core import setup
from cx_Freeze import setup, Executable


if sys.platform != "win32":
    print("This script is only for Win32 build as of now!")
    sys.exit(1)

base = "Win32GUI"

setup(
        name = "booru-grabber",
        version = "0.2.4",
        description = "Booru Grabber",
        options = {
            "build_exe": {
                "includes": ["os"],
                "excludes": ["doctest", "pdb", "unittest", "difflib",
                    "optparse", "_gtkagg", "_tkagg", "Tkconstants", "Tkinter",
                    "bsddb", "curses", "pywin.debugger", "tcl"],
                "optimize": 2,
                "zip_include_packages": "*",
                "zip_exclude_packages": None,
                "include_msvcr": True,
            },
        },
        executables = [Executable("grabber.py", base=base)],
)


# Compress the files with UPX
output_path = os.path.join("build", "exe.win32-3.6")
upx_base_args = ["upx", '--best', '--no-progress']

# FIXME: These DLLs MUST NOT be compressed for Grabber to run properly.
#        It is not known why UPX compression causes such error.
upx_exclude_compress = [
        "vcruntime140.dll",
        "wxbase30u_net_vc140.dll",
        "wxbase30u_vc140.dll",
        "wxmsw30u_core_vc140.dll",
]


for filename in os.listdir(output_path):
    if (filename == "grabber.exe" or
            os.path.splitext(filename)[1].lower() in ('.exe','.dll','.pyd', '.so')):
        if filename.lower() in upx_exclude_compress:
            print("Skip UPX compression of {}".format(filename))
            continue
        filepath = os.path.join(output_path, filename)
        args = ["upx", "--best", filepath]
        subprocess.call(args)
