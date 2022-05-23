from importlib.metadata import version

__version__ = version(__package__)

del version  # optional, avoids polluting the results of dir(__package__)
