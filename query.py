#!/usr/bin/env python

import model
import config

from sqlalchemy import and_, cast
from sqlalchemy.dialects.postgresql import BIGINT

db = model.SymbolDB()

def get_module_id(debug_file, debug_id):
    res = db.session.query(model.Module.id).filter(
        and_(model.Module.name == debug_file,
             model.Module.debug_id == debug_id)).first()
    if res:
        return res[0]
    return None

def get_function_at_address(module_id, address):
    """
    Returns function name, or None if no function was found.
    """
    res = db.session.query(model.Function.name).filter(
        and_(model.Function.module == module_id,
             model.Function.address_range.op("@>")(cast(address, BIGINT)))
        ).first()
    if res:
        return res[0]
    return None

def get_line_at_address(module_id, address):
    """
    Returns (file name, line number), or None if no line data was found.
    """
    res = db.session.query(model.File.name, model.Line.line).filter(
        and_(model.Line.file == model.File.number,
             model.Line.module == module_id,
             model.File.module == module_id,
             model.Line.address_range.op("@>")(cast(address, BIGINT)))
        ).first()
    if res:
        return res
    return None

def get_public_at_address(module_id, address):
    # TODO
    return None

def get_stack_data_at_address(module_id, address):
    # TODO
    # TODO: distinguish between STACK WIN and STACK CFI
    return None

def main():
    import fileinput
    modules = {}
    for line in fileinput.input():
        line = line.rstrip()
        ts, what, rest = line.split(",", 2)
        if what == "getsymbolfile":
            debug_file, debug_id, found = rest.split(",")
            if found == "1":
                module_id = get_module_id(debug_file, debug_id)
                modules[debug_file + debug_id] = module_id
        elif what == "getfunc":
            debug_file, debug_id, address = rest.split(",")
            func = get_function_at_address(modules[debug_file + debug_id], int(address, 16))
            if func:
                print "FUNC %s" % func
        elif what == "getline":
            debug_file, debug_id, address = rest.split(",")
            res = get_line_at_address(modules[debug_file + debug_id], int(address, 16))
            if res:
                print "LINE %s:%d" % res
        elif what == "getpublic":
            pass
        elif what == "getstackwin":
            pass
        elif what == "getstackcfi":
            pass

if __name__ == "__main__":
    main()
