import sys

if sys.version_info < (3, 10):
    # compatibility for python <3.10
    import importlib_metadata
else:
    from importlib import metadata as importlib_metadata

__version__ = importlib_metadata.version(__package__)
