"""
ORM module for service
"""
import os
import warnings
from sqlalchemy import event, create_engine, exc
from sqlalchemy import Column, String, Boolean
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

ORMException = SQLAlchemyError

Base = declarative_base()
_ENGINE = None
_DB_SESSION = None


class Individual(Base):
    """
    SQLAlchemy class/table representing an individual
    """
    __tablename__ = 'individuals'
    id = Column(String(100), primary_key=True)
    status = Column(String(100))


class Consent(Base):
    """
    SQLAlchemy class/table representing a Variant
    """
    __tablename__ = 'consents'
    id = Column(String(100), ForeignKey('individuals.id'), primary_key=True)
    project = Column(String(10), primary_key=True)
    consent = Column(Boolean)
    # (id, project) must be unique: individual can't have two consents for the same project
    __table_args__ = (
        UniqueConstraint("id", "project"),
    )


# From http://docs.sqlalchemy.org/en/latest/faq/connections.html
def add_engine_pidguard(engine):
    """Add multiprocessing guards.

    Forces a connection to be reconnected if it is detected
    as having been shared to a sub-process.

    """
    @event.listens_for(engine, "connect")
    def connect(_dbapi_connection, connection_record):  # pylint:disable=unused-variable
        """Get PID at connect time"""
        connection_record.info['pid'] = os.getpid()

    @event.listens_for(engine, "checkout")
    def checkout(_dbapi_connection, connection_record, connection_proxy):  # pylint:disable=unused-variable
        """Disconnect and raise error if not same PID"""
        pid = os.getpid()
        if connection_record.info['pid'] != pid:
            # substitute log.debug() or similar here as desired
            warnings.warn(
                "Parent process %(orig)s forked (%(newproc)s) with an open "
                "database connection, "
                "which is being discarded and recreated." %
                {"newproc": pid, "orig": connection_record.info['pid']})
            connection_record.connection = connection_proxy.connection = None
            raise exc.DisconnectionError(
                "Connection record belongs to pid %s, "
                "attempting to check out in pid %s" %
                (connection_record.info['pid'], pid)
            )


def init_db(uri):
    """
    Creates the DB engine + ORM
    """
    global _ENGINE
    _ENGINE = create_engine(uri)
    add_engine_pidguard(_ENGINE)
    Base.metadata.create_all(bind=_ENGINE)


def get_session(**kwargs):
    """
    Start the database session
    """
    global _DB_SESSION
    if not _DB_SESSION:
        _DB_SESSION = scoped_session(sessionmaker(autocommit=False,
                                                  autoflush=False,
                                                  bind=_ENGINE, **kwargs))
        Base.query = _DB_SESSION.query_property()
    return _DB_SESSION


def dump(obj, nonulls=False):
    """
    Generate dictionary  of fields without SQLAlchemy internal fields
    & relationships
    """
    rels = ["individual"]
    if not nonulls:
        return {k: v for k, v in vars(obj).items()
                if not k.startswith('_') and k not in rels}

    return {k: v for k, v in vars(obj).items()
            if not k.startswith('_') and k not in rels and v}