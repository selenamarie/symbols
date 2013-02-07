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

#######################################

DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata


#################################
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

class File(DeclarativeBase):
    __tablename__ = 'files'

    id = Column(u'id', Integer(), primary_key=True)
    number = Column('number', Integer())
    name = Column('name', Text())
    module = Column('module', ForeignKey('modules.id'))

class Function(DeclarativeBase):
    __tablename__ = 'functions'

    id = Column(u'id', Integer(), primary_key=True)
    address = Column('address', BigInteger())
    size    = Column('size', Text())
    parameter_size   = Column('parameter_size', Text())
    name    = Column('name', Text())
    module = Column('module', ForeignKey('modules.id'))

class Line(DeclarativeBase):
    __tablename__ = 'lines'

    id = Column(u'id', Integer(), primary_key=True)
    address = Column('address', BigInteger())
    size = Column('size', Text())
    line = Column('line', Integer())
    filenum = Column('filenum', Integer())
    file = Column('file', ForeignKey('files.id'))

class Stackwalk(DeclarativeBase):
    __tablename__ = 'stackwalks'

    id = Column(u'id', Integer(), primary_key=True)
    address = Column('address', BigInteger())
    stackwalk_data = Column('stackwalk_data', Text())
    module = Column('module', ForeignKey('modules.id'))

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
