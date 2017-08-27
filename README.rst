=======
SQLpy
=======
|pypi| |build-status| |coverage|

TODO
=======

- clean up exception handling/raise
- Ensure Python 2/3 interop
- Add CI and test process with test queires
- Add support for other database drivers/types

Quickstart
==========

Getting started is simple! All you need is a PostgreSQL database running and accessible to you.

First install sqlpy and psycopg2
::
    $ pip install sqlpy psycopg2

Create a `queries.sql` file in your project directory, containing the following
::
    -- name: test_select
    -- test selection from database
    SELECT * FROM test

Set up the application and run
::
    from sqlpy.sqlpy import Queries, load_queires
    import psycopg2
    import psycopg2.extras

    sql = Queries()

    queries = load_queires('queries.sql')
    for name, fn in queries:
        sql.add_query(name, fn)


    def connect_db():
        db_host = <host>
        db_port = <port>
        db_user = <user>
        db_pass = <password>
        return psycopg2.connect(dbname='postgres',
                                user=db_user,
                                password=db_pass,
                                host=db_host,
                                port=db_port,
                                cursor_factory=psycopg2.extras.RealDictCursor)


    db = connect_db()

    with db:
        with db.cursor() as cur:
            output = sql.TEST_SELECT(cur, 0)

    print output

    db.close()


.. |build-status| image:: https://travis-ci.org/9fin/sqlpy.svg?branch=master
    :alt: build status
    :scale: 100%
    :target: https://travis-ci.org/9fin/sqlpy

.. |pypi| image:: https://img.shields.io/pypi/v/sqlpy.svg
    :alt: Pypi Version
    :scale: 100%
    :target: https://pypi.python.org/pypi/sqlpy

.. |coverage| image:: https://coveralls.io/repos/github/9fin/sqlpy/badge.svg?branch=master
    :alt: Pypi Version
    :scale: 100%
    :target: https://coveralls.io/github/9fin/sqlpy?branch=master
