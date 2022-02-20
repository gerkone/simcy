from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "simcy.*",
        ["simcy/*.pyx"]
    ),
    Extension(
        "simcy.resources.*",
        ["simcy/resources/*.pyx"],
    ),
]

setup(
    name="simcy",
    version="0.0.6",
    author="gerkone",
    author_email="ggalletti@tutanota.com",
    url="https://github.com/gerkone/simcy",
    packages=find_packages(exclude=["test*"]),
    ext_modules=cythonize(extensions)
)
