import glob
import importlib.metadata
import os
import re
import site

try:
    __release__ = importlib.metadata.version("soma-base")
except importlib.metadata.PackageNotFoundError:
    __release__ = None

if __release__:
    __version__ = re.match(r"(\d+\.\d+\.\d+)[^.\d]*", __release__).group(1)
    short_version = ".".join(__version__.split(".")[:2])
else:
    __version__ = None
    short_version = None

# Enable from soma import aims
if "PIXI_PROJECT_ROOT" in os.environ:
    l = glob.glob(os.path.join(os.environ["PIXI_PROJECT_ROOT"], "build", "lib", "python*", "site-packages", "soma"))
    if l:
        __path__.append(l[0])
__path__.append(os.path.join(site.getsitepackages()[0], "soma"))
