"""Local web configurator for smlibpy model scripts.

    from printforge_configurator import serve
    serve(__file__)                # blocks, serves http://127.0.0.1:8765/

or `python -m printforge_configurator model.py`. See server.py for the API.
"""
from .server import main, parse_model, serve

__all__ = ["main", "parse_model", "serve"]
