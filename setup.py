import setuptools

options = {
    "name": "StreamPlotter",
    "version": "0.0.0",
    "python_requires": ">=3.7",
    "install_requires": open("requirements.txt").read().splitlines(),
    "packages": setuptools.find_packages()
}
setuptools.setup(**options)
