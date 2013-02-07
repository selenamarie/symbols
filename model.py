#!/usr/bin/env python

import sys
import psycopg2
import psycopg2.extensions
from psycopg2 import ProgrammingError
import re
import logging

from sqlalchemy import Column, Integer, String

from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.ext import compiler
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table
import sqlalchemy.types as types
try:
    from sqlalchemy.dialects.postgresql import *
except ImportError:
    from sqlalchemy.databases.postgres import *

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


class INT8RANGE(types.UserDefinedType):

    def get_col_spec(self):
        return 'INT8RANGE'

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

    moz_app_name = Column(u'moz_app_name', Text())
    moz_app_version = Column(u'moz_app_version', Text())
    os_target = Column(u'os_target', Text())
    buildid = Column(u'buildid', Text())
    cpu_arch_and_buildid = Column(u'cpu_arch_and_buildid', Text())

class Module(DeclarativeBase):
    __tablename__ = 'modules'

    id = Column(u'id', Integer(), primary_key=True)
    # These are a key
    debug_id = Column('debug_id', Text())
    name = Column('name', Text())
    # remaining attributes
    os = Column('os', Text())
    arch = Column('arch', Text())
    idx_unique_module = Index('idx_unique_module', debug_id, name)
    build = column(u'build', Integer()) # FK to Builds

class File(DeclarativeBase):
    __tablename__ = 'files'

    id = Column(u'id', Integer(), primary_key=True)
    number = Column('number', Integer())
    name = Column('name', Text())
    module = Column('module', Integer())

class Function(DeclarativeBase):
    __tablename__ = 'functions'

    id = Column(u'id', Integer(), primary_key=True)
    address = Column('address', BigInteger())
    size    = Column('size', Text())
    address_range = Column('address_range', INT8RANGE())
    parameter_size   = Column('parameter_size', Text())
    name    = Column('name', Text())
    module = Column('module', Integer())

class Public(DeclarativeBase):
    __tablename__ = 'publics'

    id = Column(u'id', Integer(), primary_key=True)
    address = Column('address', BigInteger())
    size = Column('size', Text())
    address_range = Column('address_range', INT8RANGE())
    name = Column('filenum', Integer())
    module = Column('module', Integer())

class Line(DeclarativeBase):
    __tablename__ = 'lines'

    id = Column(u'id', Integer(), primary_key=True)
    address = Column('address', BigInteger())
    size = Column('size', Text())
    address_range = Column('address_range', INT8RANGE())
    line = Column('line', Integer())
    filenum = Column('filenum', Integer())
    file = Column('file', Integer())

class Stackwalk(DeclarativeBase):
    __tablename__ = 'stackwalks'

    id = Column(u'id', Integer(), primary_key=True)
    address = Column('address', BigInteger())
    #address_range = Column('address_range', INT8RANGE())
    stackwalk_data = Column('stackwalk_data', Text())
    module = Column('module', Integer())

class SymbolDB():

    def __init__(self):
        dropdb = True
        createdb = True
        db = "symbols"
        sa_url = 'postgresql://selena@localhost/%s' % db

        engine = create_engine(sa_url, implicit_returning=False)
        self.engine = engine

        session = sessionmaker(bind=engine)()
        self.session = session

    def main(self):
        dropdb = True
        createdb = True
        db = "symbols"
        sa_url = 'postgresql://selena@localhost/'

        dsn = 'postgresql://selena@localhost/template1'

        engine = create_engine(sa_url, implicit_returning=False)
        self.engine = engine

        session = sessionmaker(bind=engine)()
        self.session = session

        if dropdb:
            try:
                session.connection().connection.set_isolation_level(0)
                session.execute('DROP DATABASE %s' % db)
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

        #sa_url = url_template + '/%s' % db
        sa_url = sa_url + '%s' % db
        self.engine = create_engine(sa_url, implicit_returning=False)

        self.metadata = DeclarativeBase.metadata
        self.metadata.bind = self.engine
        status = self.metadata.create_all()
        self.session.commit()

        return 0

if __name__ == "__main__":
    newthing = SymbolDB()
    newthing.main()
