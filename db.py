from flask import request, abort
from sqlalchemy import create_engine
from config import CLIENTS

_engines = {}

def get_db_engine():
    host = request.host.split(":")[0]

    if host not in CLIENTS:
        abort(403, description="Cliente no autorizado")

    if host not in _engines:
        _engines[host] = create_engine(
            CLIENTS[host]["db_uri"],
            pool_pre_ping=True
        )

    return _engines[host]
