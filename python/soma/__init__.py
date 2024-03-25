from .info import __version__  # noqa: F401
import os


def root_path():
    """Return the path of the base directory where software is installed. In a
    developpement environment this corresponds to the build directory. In
    user environments this corresponds to the install directory (which is
    $CONDA_PREFIX in the case of a Conda, Mamba or Pixi environment)
    """
    root_path = os.environ.get("SOMA_ROOT")
    if not root_path:
        root_path = os.environ.get("CASA_BUILD")
        if not root_path:
            root_path = os.environ.get("CONDA_PREFIX")
            if not root_path:
                raise EnvironmentError("cannot find soma root path")
    return root_path
