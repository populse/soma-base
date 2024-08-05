import os

from setuptools import setup

python_dir = os.path.join(os.path.dirname(__file__), "python")
release_info = {}

with open(os.path.join(python_dir, "soma", "info.py")) as f:
    code = f.read()
    exec(code, release_info)

setup(
    name=release_info["NAME"],
    description=release_info["DESCRIPTION"],
    long_description=release_info["LONG_DESCRIPTION"],
    license=release_info["LICENSE"],
    classifiers=release_info["CLASSIFIERS"],
    author=release_info["AUTHOR"],
    author_email=release_info["AUTHOR_EMAIL"],
    version=release_info["VERSION"],
    url=release_info["URL"],
    package_dir={"": "python"},
    packages=[
        "soma",
        "soma.controller",
        "soma.minf",
        "soma.pipeline",
        "soma.plugins",
        "soma.qt_gui",
        "soma.qt_gui.controller",
        "soma.qt_gui.resources",
        "soma.sandbox",
        "soma.test_utils",
        "soma.utils",
        "soma.tests",
        "soma.controller.tests",
        "soma.minf.tests",
        "soma.qt_gui.test",
        "soma.web",
    ],
    include_package_data=True,
    package_data={"": ["*.html", "*.css", "*.js"]},
    platforms=release_info["PLATFORMS"],
    install_requires=release_info["REQUIRES"],
    extras_require=release_info["EXTRAS_REQUIRE"],
    python_requires=release_info["PYTHON_REQUIRES"],
)
