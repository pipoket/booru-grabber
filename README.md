What is this?
=============
**I don't need fancy UI or preview. Just download'em for me already! D:**

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
- [gevent](http://www.gevent.org) for Core Download Engine
- [PySocks](https://github.com/Anorov/PySocks) for HTTP/SOCKS proxy support.
- [cx_Freeze](http://cx-freeze.sourceforge.net) for generating windows binaries.
- [UPX](http://upx.sourceforge.net) for compressing py2exe generated binaries.

You need to place upx.exe downloaded from UPX in the same directory with
setup.py script to generate your own cx_Freeze windows binary.


How do I run?
=============

On Windows
----------

1. Download Grabber as a ZIP archive from [Release page](https://github.com/pipoket/booru-grabber/releases)
2. Extract the files in the archive to the location wherever you want.
3. Run grabber.exe. Have fun!
4. If you want to delete Grabber later, simply delete the files and you're done.


On Linux like environment
-------------------------
You should probably run the grabber using raw Python script,
you would have to install all the libraries. Library installation differs from
environment to environment.

Here is an example for installing required libraries under Ubuntu 11.04.
should be executed with superuser privileges.

    (If you don't have pip installed within your environment)
    # apt-get install python-setuptools
    # easy_install pip

    (Now, here we install required libraries for gelbooru-grabber)
    # pip install wxPython
    # pip install gevent
    # pip install PySocks

Download Grabber as a ZIP archive from [Release page](https://github.com/pipoket/booru-grabber/releases).
Extract the files in the archive you downloaded to the location wherever you want.
You should extract the scripts to the location where you have permission to write.
After extraction, run the grabber.py script. Have fun!

**NOTE**
To use wxPython under Python 3.x, you must download and install the prebuilt binary provided by
[Project Pheonix](https://wiki.wxpython.org/ProjectPhoenix).


The grabber does not work! Where can I report the problem?
==========================================================
Booru Grabber is a premature program; which means there can be any kinds of bugs or problems.
If you found any bugs or problems while using the grabber, please feel free to file a new issue
using the 'Issues' menu above. Or you can send me a message if you are Github member.



Release Notes
=============

0.2.5 (2017-03-18)
------------------

Small bugfixes.

**Bug fixes**
- Grabber fails to download images with 'Error: urlopen error no host given'
- Grabber fails to launch with an error saying "DLL import failure"


0.2.4 (2017-02-13)
------------------

Yes, the project is not dead. Yes, it's lazy developer :<

**Bug fixes**
- Grabber fails to download images with 'Error: uknown url type' error
- Setting download path to non-existent one causes Grabber to malfunction
- Non-ASCII character on Grabber path causes exception
- Directory created from tag value unnecessarily uses quoted string (e.g. 'tag(a)' -> 'tag26a29')

**Updates**
- Grabber now runs under Python 3.6!
- Update proxy feature to handle HTTPS connection


0.2.2 (2015-10-20)
------------------

Sorry for the late update, but hey, I have a job and this is my free-time toy-project anyway! :3

**Bug fixes**
- Grabber does not work properly (API is blocked D:)
 - Workaround has been applied to make grabber to work properly
- Using 'Stop' button makes application unusable time to time
 - Annoying bugs such as download button becoming unresponsive, crash, etc...

**Updates**
- Slowly refactoring code structure to support more booru-ish sites

**Features**
- Make User-Agent configurable
- Grabber now remembers its last configuration (no need to type proxy repeatedly)


0.2.0 (2015-04-14)
------------------

MAJOR REFACTORING AND UPDATES! (4 years D:)

**Bug fixes**
- Grabber does not work properly (it was severely outdated)

**Updates**
- Gelbooru provides API for programs like us and Grabber takes advantage of it

**Features**
- Updated UI
 - Added download speed label which shows whether Grabber is working or not
- Added support for proxy(HTTP/SOCKS4/SOCKS5)
- Added 'Stop' button which stops download in progress

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
