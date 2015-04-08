Important Notes
===============
- The project is under MAJOR REFACTORING/UPDATE. IT WILL NOT FUNCTION PROPERLY until first release
- This project has been moved from [gelbooru-grabber](https://bitbucket.org/pipoket/gelbooru-grabber)
- Yes, I'm the same developer who made [gelbooru-grabber](https://bitbucket.org/pipoket/gelbooru-grabber)
- Yes, I know  [gelbooru-grabber](https://bitbucket.org/pipoket/gelbooru-grabber) sucks and does not work properly, but I had no time to fix those
- Now hereby I say, sorry for all those who were using out-dated, not-properly-functioning old gelbooru-grabber :(


What is this?
=============
Booru Image Grabber grabs images from the *-booru image sites.
site and stores the images to the disk. Downloading images one-by-one from the
website is kinda tedious work. So, why don't we make some kind of program that
does the downloading automatically?

Just type tags to the booru Image Grabber and hit the "Download" button.
The grabber will get all the images searched with given tag and download them
to the disk.

Currently, booru-grabber supports following *-booru image sites. Note that some of
these sites are NSFW(Not Safe For Work, if you know what I mean :3), so be warned!

- [Gelbooru](http://www.gelbooru.com/)

What do I need?
===============
Gelbooru Image Grabber is written in Python_. The grabber uses following
libraries.

- [wxPython](http://www.wxpython.org) for GUI
- [Twisted](http://www.wxpython.org) for Core Download Engine
- [py2exe](http://www.py2exe.org) for generating windows binaries.
- [UPX](http://up.sourceforge.net) for compressing py2exe generated binaries.

You need to place upx.exe downloaded from UPX_ in the same directory with
setup.py script to generate your own py2exe windows binary.


How do I run?
=============

On Windows
----------
Download the executable files from the Downloads section. Extract the files in
the archive you downloaded to the location wherever you want.
After extraction, run grabber.exe. Have fun!


On Linux like environment
-------------------------
You should probably run the grabber using raw Python script,
you would have to install all the libraries. Library installation differs from
environment to environment.

Here is an example for installing required libraries under Ubuntu 11.04. Every command
should be executed with superuser privileges. (Hey, you are installing libraries and
superuser privileges do count) ::

    (If you don't have pip installed within your environment)
    # apt-get install python-setuptools
    # easy_install pip

    (Now, here we install required libraries for gelbooru-grabber)
    # pip install wxPython
    # pip install twisted



Download the tar gzipped files from the Downloads section. Extract the files in
the archive you downloaded to the location wherever you want. You should
extract the scripts to the location where you have permission to write.
After extraction, run the grabber.py script. Have fun!



The grabber does not work! Where can I report the problem?
==========================================================
Booru Grabber is a premature program; which means there can be any kinds of bugs or problems.
If you found any bugs or problems while using the grabber, please feel free to file a new issue
using the 'Issues' menu above. Or you can send me a message if you are Github member.



Release Notes
=============

0.1.8 (2011-12-04)
------------------

**Bug fixes**

- Grabber hangs after printing out "Last page is ..." message.
- UI becomes unresponsive or download freezes time to time.
- Grabber hangs if the directory with the name of tag to be downloaded exists.

0.1.7 (2011-10-29)
------------------

**Bug fixes**

- Grabber only retrieves the images on the first page of given search result.


0.1.6 (2011-07-27)
------------------

**Features**

- Updated UI to support various options
- User can specify how many files to be downloaded simultaneously
- User can specify the directory(folder) to which the grabber should download the images
- User can choose whether the grabber should make subdirectory(subfolder) with the tagname
- User can choose whether the grabber should overwrite the existing file or not

**Bug fixes**

- Removed meaningless "Overwriting may happen" message
- Error while 'Getting Last Page...' makes the grabber to hang 


0.1.1 (2011-04-20)
------------------

**Features**

- The grabber skips the already existing file


0.1.0 (2011-03-29)
------------------

**Bug fixes**

- The grabber crashes randomly due to the major bug within core download code
- Reset download counter if new download starts
- Trying to download tagname with only one page on gelbooru made the grabber to hang



Release Plan
============

0.2.0
-----

- Support all the booru-like image boards. (danbooru, oreno.imouto and you name it!)

