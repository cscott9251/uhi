### Python script to download the 3D Building

import requests
from bs4 import BeautifulSoup
import wget
import os

## Logic to ensure proper functionality of aria2

import signal
import subprocess
import sys
from subprocess import Popen
from typing import TypedDict


class Win32PopenKwargs(TypedDict):
    """Popen kwargs for Windows."""

    creationflags: int


class UnixPopenKwargs(TypedDict):
    """Popen kwargs for Unix."""

    start_new_session: bool


popen_kwargs = (
    UnixPopenKwargs(start_new_session=True)
    if sys.platform != "win32"
    else Win32PopenKwargs(creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
)


with Popen(args=("aria2c", "--enable-rpc"), **popen_kwargs) as p:
    try:
        # Do whatever you want here.
        ...
    finally:
        # following code can shutdown the subprocess gracefully.
        if sys.platform == "win32":
            # https://stackoverflow.com/questions/44124338/trying-to-implement-signal-ctrl-c-event-in-python3-6
            os.kill(p.pid, signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(p.pid), signal.SIGINT)

## End of Logic to ensure proper functionality of aria2

# URLs for download of LoD2, building footprints, and DGM data from Geodata Bayern

urllist = ["https://geodaten.bayern.de/odd/a/lod2/citygml/meta/metalink/09463.meta4",
           "https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/094_Oberfranken_Hausumringe.zip",
           "https://geodaten.bayern.de/odd/a/dgm/dgm1/meta/metalink/09463000.meta4"]

## Download LoD2 data for Coburg

# Download Metalink file for Coburg from Geodaten Bayern

# url = "https://geodaten.bayern.de/odd/a/lod2/citygml/meta/metalink/09463.meta4"
# path = "data/LoD2/"
#
# wget.download(url, out=path)
#
# os.system("aria2c -c data/09463.meta4 -d data/LoD2/")

## Download building footprints for Oberfranken (clip to Coburg boundary later)

# Download shapefiles

# url = "https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/094_Oberfranken_Hausumringe.zip"
# path = "data/Building_footprints/"
#
# wget.download(url, out=path)

res = {}

for url in urllist:
    if "lod2" in url:
        res.update({"data/LoD2/":url})
    elif "dgm" in url:
        res.update({"data/DGM/":url})
    elif "hausumringe" in url:
        res.update({"data/Building_footprints/":url})

for key, value in res.items():
    wget.download(value, out=key)
    if ".meta4" in value:
        f = value.rsplit('/', 1)[-1]
        print(f)
        os.system(f"aria2c -c {key}/{f} -d {key}")









