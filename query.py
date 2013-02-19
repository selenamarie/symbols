#!/usr/bin/env python

import model
import config

from sqlalchemy import and_, cast
from sqlalchemy.dialects.postgresql import BIGINT

def get_module_id(debug_file, debug_id):
    db = model.SymbolDB()
    res = db.session.query(model.Module.id).filter(
        and_(model.Module.name == debug_file,
             model.Module.debug_id == debug_id)).one()
    return res[0]

def get_function_at_address(module_id, address):
    db = model.SymbolDB()
    res = db.session.query(model.Function.name).filter(
        and_(model.Function.module == module_id,
             model.Function.address_range.op("@>")(cast(address, BIGINT)))
        ).first() # should be one(), but data may be screwy?
    if res:
        return res[0]
    return None
