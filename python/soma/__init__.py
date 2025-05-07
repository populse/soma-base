import importlib.metadata
import re

try:
    __release__ = importlib.metadata.version("soma-base")
except importlib.metadata.PackageNotFoundError:
    __release__ = None

if __release__:
    __version__ = re.match(r"(\d+\.\d+\.\d+)[^.\d]*", __release__).group(1)
else:
    __version__ = None
