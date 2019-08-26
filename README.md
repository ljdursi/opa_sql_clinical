# Demo OPA-enabled clinical data service

## Stack

- Docker Compose
- [Connexion](https://github.com/zalando/connexion) for implementing the API
- [SQLAlchemy](http://sqlalchemy.org), using [Sqlite3](https://www.sqlite.org/index.html) for ORM
- [Bravado-core](https://github.com/Yelp/bravado-core) for Python classes from the spec
- Python 3
- Pytest, tox
- Travis-CI

## Running

This can be run by starting

```
docker-compose up
```

and querying the individuals API at `http://localhost:3000/v1/ui`
