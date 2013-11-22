#!/usr/bin/env python

import model
import config

from sqlalchemy import and_, cast
from sqlalchemy.dialects.postgresql import BIGINT

db = model.SymbolDB()

def get_module_id(debug_file, debug_id):
    res = db.session.query(model.Module.id).filter(
        and_(model.Module.debug_file == debug_file,
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
    # TODO in load_symbols.py Move file.name into Line table
    res = db.session.query(model.File.name, model.Line.line).filter(
        and_(model.Line.file_number == model.File.number,
             model.Line.module == module_id,
             model.Line.module == module_id,
             model.Line.address_range.op("@>")(cast(address, BIGINT)))
        ).first()
    if res:
        return res
    return None


def get_public_at_address(module_id, address):
    res = db.session.query(model.Public.name).filter(
        and_(model.Public.module == module_id,
             model.Public.address < address)
        ).order_by(model.Public.address.desc()).limit(1).first()
    if res:
        return res[0]
    return None


def get_stack_data_at_address(module_id, type, address):
    res = db.session.query(model.Stackdata.data).filter(
        and_(model.Stackdata.module == module_id,
             model.Stackdata.type == type,
             model.Stackdata.address_range.op("@>")(cast(address, BIGINT)))
        ).first()
    if res:
        return res[0]
    return None


def get_stack_cfi_data_in_range(module_id, start_address, end_address):
    res = db.session.query(model.Stackdata.data).filter(
        and_(model.Stackdata.module == module_id,
             model.Stackdata.type == 'CFI',
             model.Stackdata.address >= start_address,
             model.Stackdata.address < end_address)
        ).order_by(model.Stackdata.address).all()
    if res:
        return res
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
            debug_file, debug_id, address = rest.split(",")
            pub = get_public_at_address(modules[debug_file + debug_id], int(address, 16))
            if pub:
                print "PUBLIC %s" % pub
        elif what == "getstackwin":
            debug_file, debug_id, address = rest.split(",")
            stack = get_stack_data_at_address(modules[debug_file + debug_id], 'WIN', int(address, 16))
            if stack:
                print "STACK WIN ..."
        elif what == "getstackcfiinit":
            debug_file, debug_id, address = rest.split(",")
            stack = get_stack_data_at_address(modules[debug_file + debug_id], 'CFI INIT', int(address, 16))
            if stack:
                print "STACK CFI INIT ..."
        elif what == "getstackcfi":
            debug_file, debug_id, start_address, end_address = rest.split(",")
            stacks = get_stack_cfi_data_in_range(modules[debug_file + debug_id], int(start_address, 16), int(end_address, 16))
            if stacks:
                print "STACK CFI (%d) ..." % len(stacks)

if __name__ == "__main__":
    main()
