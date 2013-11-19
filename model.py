#!/usr/bin/env python

import sys
import re
import logging

import psycopg2
import psycopg2.extensions
import sqlalchemy.types as types
from psycopg2 import ProgrammingError
from sqlalchemy import Column, Integer, String, ForeignKey, Index, Text, \
    DateTime, BigInteger, Enum, create_engine, event
from sqlalchemy.dialects.postgresql import INT8RANGE
from sqlalchemy.ext import compiler
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table

from config import sa_url

class CITEXT(types.UserDefinedType):

    def get_col_spec(self):
        return 'CITEXT'

    def bind_processor(self, dialect):
        def process(value):
            return value
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return value
        return process


#######################################

DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata


#################################
class Build(DeclarativeBase):
    __tablename__ = 'builds'

    # http://mxr.mozilla.org/mozilla-central/source/Makefile.in#149
    # $(MOZ_APP_NAME)-$(MOZ_APP_VERSION)-$(OS_TARGET)-$(BUILDID)-$(CPU_ARCH)$(EXTRA_BUILDID)-symbols.txt
    id = Column(u'id', Integer(), primary_key=True)
    filename = Column(u'filename', Text())

    moz_app_name = Column(u'moz_app_name', Text())
    moz_app_version = Column(u'moz_app_version', Text())
    os_target = Column(u'os_target', Text())
    buildid = Column(u'buildid', Text())
    cpu_arch_and_buildid = Column(u'cpu_arch_and_buildid', Text())
    # adding fields based on cleanup-breakpad-symbols.py

    build_date = Column(u'build_date', DateTime(timezone=True))


class BuildSymbol(DeclarativeBase):
    __tablename__ = 'build_symbols'

    build_id = Column(u'build_id', Integer(), ForeignKey('builds.id'), primary_key=True)
    symbol_id = Column(u'build_id', Integer(), ForeignKey('symbols.id'), primary_key=True)


class Symbol(DeclarativeBase):
    __tablename__ = 'symbols'

    """ Files contained in a build file """
    id = Column(u'id', Integer(), primary_key=True)
    filename = Column(u'filename', Text(), unique=True)
    full_path = Column(u'full_path', Text(), unique=True)


class Module(DeclarativeBase):
    __tablename__ = 'modules'

    id = Column(u'id', Integer(), primary_key=True)
    # These are a key
    debug_id = Column('debug_id', Text())
    debug_file = Column('debug_file', Text())
    # remaining attributes
    os = Column('os', Text())
    arch = Column('arch', Text())
    build_id = Column(u'build_id', Integer(), ForeignKey('builds.id')) # FK to Builds

    __table_args__ = (
        Index('idx_unique_module', debug_id, debug_file),
    )


class File(DeclarativeBase):
    __tablename__ = 'files'

    id = Column(u'id', Integer(), primary_key=True)
    module = Column('module', Integer(), autoincrement=False)
    number = Column('number', Integer(), autoincrement=False)
    name = Column('name', Text())


class Function(DeclarativeBase):
    __tablename__ = 'functions'

    id = Column(u'id', Integer(), primary_key=True)
    module = Column(u'module', Integer())
    name    = Column(u'name', Text())
    address_range = Column(u'address_range', INT8RANGE())
    parameter_size   = Column(u'parameter_size', Integer())

    __table_args__ = (
        Index(u'idx_function_address_range',
            address_range, postgresql_using='gist'),
        Index('idx_function_module', module, postgresql_using='btree')
    )


class Public(DeclarativeBase):
    __tablename__ = 'publics'

    id = Column(u'id', Integer(), primary_key=True)
    module = Column('module', Integer())
    name = Column('name', Text())
    address = Column('address', BigInteger())
    parameter_size = Column('parameter_size', Integer())


class Line(DeclarativeBase):
    __tablename__ = 'lines'

    id = Column(u'id', Integer(), primary_key=True)
    file_id = Column('file', Integer(), ForeignKey('files.id'))
    module = Column('module', Integer(), ForeignKey('modules.id'))
    address_range = Column('address_range', INT8RANGE())
    line = Column('line', Integer())


class Stackdata(DeclarativeBase):
    __tablename__ = 'stackdata'

    id = Column(u'id', Integer(), primary_key=True)
    module = Column('module', Integer())
    type = Column(Enum("WIN", "CFI INIT", "CFI", name="stack_type"))
    address = Column('address', BigInteger())
    address_range = Column('address_range', INT8RANGE())
    data = Column('data', Text())


class SymbolDB():

    def __init__(self):
        dropdb = True
        createdb = True
        db = "symbols"
        sa_url_db = sa_url + db

        engine = create_engine(sa_url_db, implicit_returning=False)
        self.engine = engine

        session = sessionmaker(bind=engine)()
        self.session = session

    def main(self):
        dropdb = True
        createdb = True
        db = "symbols"

        sa_url_db = sa_url + "template1"
        engine = create_engine(sa_url_db, implicit_returning=False)
        self.engine = engine

        session = sessionmaker(bind=engine)()
        self.session = session

        if dropdb:
            try:
                session.connection().connection.set_isolation_level(0)
                session.execute('DROP DATABASE IF EXISTS %s' % db)
                session.connection().connection.set_isolation_level(1)
            except ProgrammingError, e:
                if re.match(
                       'database "%s" could not be dropped' % db,
                       e.pgerror.strip().split('ERROR:  ')[1]):
                    # already done, no need to rerun
                    print "The DB %s could not be dropped" % db
                    return 0

        if createdb:
            try:
                session.connection().connection.set_isolation_level(0)
                session.execute('CREATE DATABASE %s' % db)
                session.connection().connection.set_isolation_level(1)
            except ProgrammingError, e:
                if re.match(
                       'database "%s" already exists' % db,
                       e.pgerror.strip().split('ERROR:  ')[1]):
                    # already done, no need to rerun
                    print "The DB %s already exists" % db
                    return 0
                raise

        sa_url_db = sa_url + db
        self.engine = create_engine(sa_url_db, implicit_returning=False)

        self.metadata = DeclarativeBase.metadata
        self.metadata.bind = self.engine
        status = self.metadata.create_all()
        self.session.commit()

        return 0

if __name__ == "__main__":
    newthing = SymbolDB()
    newthing.main()
