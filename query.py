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

def get_line_at_address(module_id, address):
    db = model.SymbolDB()
    res = db.session.query(model.Line.line, model.Line.file).filter(
        and_(model.Line.module == module_id,
             model.Line.address_range.op("@>")(cast(address, BIGINT)))
        ).first()
    if res:
        return res
    return None

def get_file_by_number(module_id, filenum):
    db = model.SymbolDB()
    res = db.session.query(model.File.number).filter(
        model.File.module == module_id)).first()
    if res:
        return res[0]
    return None

def get_public_at_address(module_id, address):
    # TODO
    return None

def get_stack_data_at_address(module_id, address):
    # TODO
    # TODO: distinguish between STACK WIN and STACK CFI
    return None
