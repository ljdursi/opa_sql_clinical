# pylint: disable=redefined-outer-name
"""
Tests for ORM module
"""
import os

import pytest

from . import dump, init_db, get_session, Individual, Consent


def are_equivalent(ormobj1, ormobj2):
    """
    Are dict representations of two objects equal?
    """
    return dump(ormobj1, nonulls=True) == dump(ormobj2, nonulls=True)


@pytest.fixture(scope="module")
def simple_db(db_filename="./sql_clinical.sqlite"):
    """
    Create a DB with a small number of objects for testing
    """
    # delete db if already exists
    try:
        os.remove(db_filename)
    except OSError:
        pass

    init_db('sqlite:///'+db_filename)
    session = get_session(expire_on_commit=False)

    ind_ids = ["P001", "P002", "P003", "P004", "P005", "P006"]
    statuses = ["Healthy", "Sick", "Healthy", "Sick", "Healthy", "Sick"]

    individuals = [Individual(id=id, status=st)
                   for (id, st) in zip(ind_ids, statuses)]
    session.add_all(individuals)
    session.commit()

    projects = ["profyle_member", "tf4cn_member"]
    consents = []
    consents = consents + [Consent(id=id, project=projects[0], consent=True) for id in ind_ids[:3]]
    consents = consents + [Consent(id=id, project=projects[1], consent=True) for id in ind_ids[3:6]]

    session.add_all(consents)
    session.commit()

    session.expunge_all()
    session.close()
    return individuals, consents, projects, db_filename


def test_search_individuals(simple_db):
    """
    Perform simple individual searches on the DB fixture
    """
    inds, _, _, _ = simple_db
    db_session = get_session()

    # Test simple individual queries
    # By ID:
    for ind in inds:
        indquery = db_session.query(Individual).filter(Individual.id == ind.id).all()
        assert len(indquery) == 1
        assert are_equivalent(indquery[0], ind)

    nhealthy = len([i for i in inds if i.status == "Healthy"])
    nsick = len([i for i in inds if i.status == "Sick"])

    # By Status:
    healthyquery = db_session.query(Individual).filter(Individual.status == "Healthy").all()
    assert len(healthyquery) == nhealthy

    sickquery = db_session.query(Individual).filter(Individual.status == "Sick").all()
    assert len(sickquery) == nsick

    db_session.close()


def test_search_consents(simple_db):
    """
    Test the consents
    """
    _, consents, projects, _ = simple_db
    db_session = get_session()

    # note: currenly only testing relationship outwards from call
    # TODO: add testing starting from individual and variant
    for proj in projects:
        nconsented = len([c for c in consents if c.consent and c.project == proj])
        ormproj = db_session.query(Consent).filter_by(project=proj, consent=True).all()
        assert len(ormproj) == nconsented

    db_session.close()


if __name__ == "__main__":
    test_search_individuals(simple_db)
    test_search_consents(simple_db)