#!/usr/bin/env python

import sys
import re
import logging

import psycopg2
import psycopg2.extensions
import sqlalchemy.types as types
from psycopg2 import ProgrammingError
from sqlalchemy import Column, Integer, String, ForeignKey, Index, Text, \
    DateTime, BigInteger, Enum, create_engine, event, Sequence
from sqlalchemy.dialects.postgresql import INT8RANGE
from sqlalchemy.ext import compiler
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table

from config import sa_url

#######################################

DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata

#################################


class Route(DeclarativeBase):
    __tablename__ = 'routes'

    # mod % X on buildid
    shard = Column('shard', Integer())
    connection_id = Column('connection_id', Integer())


class Connection(DeclarativeBase):
    __tablename__ = 'connections'

    id = Column('id', Integer(), primary_key=True)
    hostname = Column('hostname', Text())
    port = Column('port', Integer())
    username = Column('username', Text())
    password = Column('password', Text())
    database = Column('database', Text())


class RoutingDB():

    def __init__(self):
        self.dropdb = True
        self.createdb = True
        self.db = "routing"

        sa_url_db = sa_url + db

        engine = create_engine(sa_url_db, implicit_returning=False)
        self.engine = engine

        session = sessionmaker(bind=engine)()
        self.session = session

    def main(self):
        sa_url_db = sa_url + "template1"
        engine = create_engine(sa_url_db, implicit_returning=False)
        self.engine = engine

        session = sessionmaker(bind=engine)()
        self.session = session

        if self.dropdb:
            try:
                session.connection().connection.set_isolation_level(0)
                session.execute('DROP DATABASE IF EXISTS %s' % self.db)
                session.connection().connection.set_isolation_level(1)
            except ProgrammingError, e:
                if re.match(
                       'database "%s" could not be dropped' % self.db,
                       e.pgerror.strip().split('ERROR:  ')[1]):
                    # already done, no need to rerun
                    print "The DB %s could not be dropped" % self.db
                    return 0

        if self.createdb:
            try:
                session.connection().connection.set_isolation_level(0)
                session.execute('CREATE DATABASE %s' % self.db)
                session.connection().connection.set_isolation_level(1)
            except ProgrammingError, e:
                if re.match(
                       'database "%s" already exists' % self.db,
                       e.pgerror.strip().split('ERROR:  ')[1]):
                    # already done, no need to rerun
                    print "The DB %s already exists" % self.db
                    return 0
                raise

        sa_url_db = sa_url + self.db
        self.engine = create_engine(sa_url_db, implicit_returning=False)

        self.metadata = DeclarativeBase.metadata
        self.metadata.bind = self.engine
        status = self.metadata.create_all()
        self.session.commit()

        return 0

if __name__ == "__main__":
    newthing = SymbolDB()
    newthing.main()
