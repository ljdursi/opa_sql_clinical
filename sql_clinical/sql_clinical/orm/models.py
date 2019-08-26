"""
SQLAlchemy models for the database
"""
from sqlalchemy import Column, String, Boolean
from sqlalchemy import UniqueConstraint, ForeignKey
from sql_clinical.orm import Base


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
    consent = Column(Boolean, primary_key=True)
    # (id, project) must be unique
    __table_args__ = (
        UniqueConstraint("id", "project"),
    )
