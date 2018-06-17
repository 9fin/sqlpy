=====================
SQLpy - it's just SQL
=====================
|pypi| |build-status| |coverage| |versions|


With SQLpy you can work directly with advanced SQL from the comfort of your Python code. Write SQL in `.sql` files and Python in `.py` files, with all the correct highlighting, linting and maintainability that comes with it.

    - Write and run the *exact* SQL code you want
    - Use advanced SQL techniques such as
        - CTEs
        - subqueries
        - recursion
        - distinct on, partition over (), etc...
    - Dynamically build SQL queries for different purposes
    - Use the latest features available in your database system

Party like it's ANSI 1999!
==========================
SQL has been around since the mid 1970's in RDMS systems as the bedrock of many critical systems and applications. SQL is easy to start with but is quickly perceived as complex when you go beyond ``"SELECT * FROM table;"``. Especially in the age of web applications where the persistence layer (both relational and No-SQL) have been treated as simple stores of data, and are often behind abstraction to bring data in and out of your application. But when you need to do something a bit more custom with your data, you often find yourself reaching to SQL.  

However there has not really been a simple and straightforward way to do this directly from the application code itself for large projects. Having SQL strings dotted all over source files does not help maintainability or readability. 

The solution to using SQL directly from your application code is to... *use SQL directly from your application code!* Following from the original insight of `YeSQL`_, and learning from `anosql`_, SQLpy is the solution for working directly with SQL in Python projects.

Why SQLpy? Read more on background here: `SQLpy Blog`_

.. _YeSQL: https://github.com/krisajenkins/yesql/
.. _anosql: https://github.com/honza/anosql
.. _SQLpy Blog: https://blog.9fin.com/post/sqlpy-0-2-0-is-here/

Installation
============

.. code-block:: none
   
    $ pip install sqlpy

You'll also need a Database DBAPI driver. See `compatibility`_.

Quickstart
==========
Full documentation can be found at `readthedocs <https://sqlpy.readthedocs.io>`_.

Getting started is simple! All you need is a SQL database running and accessible to you. Let's assume a PostgreSQL database for our example.

Assume we have a database table ``hello`` with the following data.

====  ==========
 id    message
====  ==========
 1     hello
 2     SQLpy
 3     PostgreSQL!
====  ==========

First install **sqlpy** and **psycopg2**

.. code-block:: none

    $ pip install sqlpy psycopg2

Create a `queries.sql` file in your project directory, containing the following. (The name of the SQL snippet is how to link the query to the Python code.)

.. code-block:: sql

    -- name: test_select
    -- selection from database
    SELECT * FROM hello

Set up the application and run

.. code-block:: python
    
    from __future__ import print_function  # Python 2-3 compatibility
    from sqlpy import Queries
    import psycopg2

    sql = Queries('queries.sql')


    def connect_db():
        return psycopg2.connect(dbname='postgres',
                user=<user>,
                password=<password>,
                host=<host>,
                port=<port>)


    db = connect_db()

    with db:
        with db.cursor() as cur:
            output = sql.TEST_SELECT(cur)

    print(output)

    db.close()

\...prints

.. code-block:: none

    [(1, u'hello'), (2, u'SQLpy'), (3, u'PostgreSQL!')]

You can also pass variables to the query via format strings ``%s`` or pyformat strings ``%(name)s`` and an argument tuple or dictionary respectively.

.. code-block:: sql

    -- name: select_by_id
    SELECT * FROM hello
    WHERE id = %s;

    -- name: select_by_msg
    SELECT * FROM hello
    WHERE id = %(msg)s;

.. code-block:: python

    >> sql.SELECT_BY_ID(cur, (1,))

    [(1, u'hello')]

    >> kwargs = {'msg': 'SQLpy'}
    >> sql.SELECT_BY_MSG(cur, kwargs)

    [(2, u'SQLpy')]

.. _compatibility:

Database Compatibility/Limitations
==================================
SQLpy was written as a lightweight helper around your already existing Python `DB API 2.0`_ library, with no assumptions made about the underlying library of choice.

As long as you write valid SQL for *your* database system and Python DB API library, then you should have no problems.
    
    For example PostgreSQL implements the ``RETURNING`` clause, this may be called something else or not implemented in a different system. So if you are using a With RETURNING query, then make sure you have the correct SQL syntax for your system.

Other explicit compatibility points detailed below.

paramstyle
----------

The Python DB API specifies 5 types of `parameter style`_
    - qmark: Question mark style, e.g. ...WHERE name=?
    - numeric: Numeric, positional style, e.g. ...WHERE name=:1
    - named: Named style, e.g. ...WHERE name=:name
    - format: ANSI C printf format codes, e.g. ...WHERE name=%s
    - pyformat: Python extended format codes, e.g. ...WHERE name=%(name)s

SQLpy supports all of the *positional* paramstyles, for all query types other than ``BUILT``, since the SQL code is simply passed straight through to the DB API library.

As of version 0.2.0 SQLpy only supports ``pyformat`` as the named paramstyle for ``BUILT`` query types.

Below is a non-exhaustive, possibly incomplete, probably out of date list, of popular Python DB API libaries and their paramstyle support.

================   ==================
paramstyle          library
================   ==================
format, pyformat    `psycopg2`_
format, pyformat    `pg8000`_
format, pyformat    `mysqldb`_
format, pyformat    `mysqlconnector`_
format, pyformat    `pymssql`_
qmark               `oursql`_
qmark               `pyodbc`_
qmark               `sqlite3`_
numeric, named      `cx_oracle`_
================   ==================

.. _DB API 2\.0: https://www.python.org/dev/peps/pep-0249/
.. _parameter style: https://www.python.org/dev/peps/pep-0249/#paramstyle
.. _psycopg2: http://initd.org/psycopg/docs/
.. _pg8000: http://pythonhosted.org/pg8000/
.. _mysqldb: http://mysql-python.sourceforge.net/MySQLdb.html
.. _mysqlconnector: https://dev.mysql.com/doc/connector-python/en/
.. _pymssql: http://pymssql.org/en/stable/migrate_1_x_to_2_x.html?highlight=paramstyle#parameter-substitution
.. _oursql: https://pythonhosted.org/oursql/index.html
.. _pyodbc: https://github.com/mkleehammer/pyodbc/wiki
.. _sqlite3: https://docs.python.org/3.6/library/sqlite3.html
.. _cx_oracle: http://cx-oracle.readthedocs.io/en/latest/index.html

quote_ident
-----------
**PostgreSQL/psycopg 2.7+ Only**

Due to SQL parameter escaping (see `Bobby Tables`_), many DB API libraries won't allow you to correctly pass in variables to set ``idendity`` values in your query. These are things like column names in the SELECT, or ORDER BY clauses. The psycopg libary for PostgreSQL provides the ``quote_ident()`` function to solve this. To use it, pass a tuple of strings to your SQLpy function where the SQL contains a ``{}`` replacement field for each tuple item.

.. code-block:: sql

    -- name: select_by_id
    SELECT * FROM hello
    WHERE {} = %s;

.. code-block:: python

    >> sql.SELECT_BY_ID(cur, identifiers=('id',), (1,))

    [(1, u'hello')]

.. _Bobby Tables: http://bobby-tables.com/python

Tests
=====
Tests are provided through the excellent `pytest`_, and CI via `Travis CI`_. SQLpy is tested against a real PostgreSQL database loaded with the `pagila`_ dataset.

To run the test suite locally without a database, simply run ``make test`` from the root of the project. To run with a database (given you have one accessible to you):
    - load the pagila data by copying the commands in the ``before_script`` block in the ``.travis.yml`` file.
    - modify the ``test_sqlpy.py`` file to enable running of the skipped test blocks and add any credentials to the ``db_cur()`` fixture.
    - run with ``make test`` as before

.. _pytest: https://docs.pytest.org/en/latest/
.. _Travis CI: https://travis-ci.org/9fin/sqlpy
.. _pagila: https://github.com/devrimgunduz/pagila

Development
===========

Team work makes the dream work!

We welcome contributions! You can open an Issue to report a bug or ask a question. If you would like to submit changes for review, please follow these steps:

    1. Fork the repository
    2. Make your changes
    3. Install the requirements in ``dev-requirements.txt``
    4. Submit a pull request after running ``make check`` (ensure it does not error!)


License
=======
MIT


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

.. |versions| image:: https://img.shields.io/pypi/pyversions/sqlpy.svg
    :alt: Python Versions
    :scale: 100%
    :target: https://pypi.python.org/pypi/sqlpy
