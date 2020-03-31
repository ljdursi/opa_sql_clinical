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


Generate the initial database from running 
`pytest sql_clinical/orm/test.py` in the `sql` directory.

From the root directory, generate the tokens - ID and claim tokens - 
by running `python tokens/generate_tokens.py`.  Then get them in
environment variables by running `source tokens/token_envs.sh`

Now you can test the clinical endpoint listing individuals with
Alice (who has authorization for both cohorts) and Bob (who has
authorization for just one):

```
curl localhost:4000/clinical/v1/individuals \
     -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ${ALICE_ID}" \
     -H "X-Claim-Profyle-Member: ${ALICE_PROFYLE}"
``` 

```
curl localhost:4000/clinical/v1/individuals \
     -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ${BOB_ID}" \
     -H "X-Claim-Profyle-Member: ${BOB_PROFYLE}"
```

You can also try querying just `individuals/P001` for both.

The analytics service queries the same database; you can query
the endpoints at `localhost:5000/analytics/v1/n` and 
`localhost:5000/analytics/v1/healthy_fraction`.
