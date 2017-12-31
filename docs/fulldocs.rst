.. _fulldocs:

Full Documentation
==================

How it works
------------
Python PEP 249 `PEP249`_ is the current standard for implementing interoperability between Python and relational databases. From the PEP text
::
    This API has been defined to encourage similarity between
    the Python modules that are used to access databases.

The standard defines a number of common Classes, methods and operations that any library must implement to be compliant. A slew of Python libraries exist for most if not all relational database systems, all adhering to the same specification. All of them boiling down to sending SQL commands to and returning their results from the database server to the Python runtime. 

SQLpy was written as a lightweight helper around your already existing Python `DB API 2.0`_ library, with no assumptions made about the underlying library of choice. Essentially only wrapping their ``execute`` and ``executemany`` methods. Connection and Cursor object creation preferences are left up to you.

SQLpy leverages the powerful ``functools`` module within Python and creates prepared functions reading SQL statements from a queries file as directed within your project. The SQL statements have a special form that SQLpy recognises and this determines how the statement is prepared and eventually executed. Depending on if it is a simple select, a delete or a different type of statement.

For the following sections, let's assume we have a database table ```hello``` with the following data.

====  ==========
 id    message
====  ==========
 1     hello
 2     SQLpy
 3     PostgreSQL!
====  ==========

Executing the functions
```````````````````````
To execute a SQL statement and get results, just call the method by name on the :class:`Queries` object.

.. code-block:: python
    
    results = sql.SQL_STATEMENT(cur, fetch_n, args=None, identifers=None, log_query_params=LOG_QUERY_PARAMS, **kwargs)

ARGUMENTS EXPLAINED

Query types
```````````
The type of query executed is determined by a token SQLpy searches for at the end of the ``-- name:`` special comment string in the SQL file. This can be ``!``, ``<!>``, ``$`` or not present.

Comments are detected and added to the ``__doc__`` attribute of the returned function.

.. code-block:: sql

    -- name: sql_statement
    -- a regular select statement
    SELECT * FROM hello
    WHERE id = %s;

    -- name: insert_statement!
    -- an insert statement
    INSERT INTO hello (message)
    VALUES (%s);

    -- name: insert_statement2<!>
    -- an insert statement with return
    INSERT INTO hello (message)
    VALUES (%s)
    RETURNING id;

    -- name: built_sql_statement$
    -- a built up sql statement
    SELECT * FROM hello
    WHERE id = %(id_low)s
    OR id = %(id_high)s;

SELECT (not present)
    bla bla bla

INSERT/UPDATE/DELETE (``!``)
    bla bla bla

With RETURNING (``<!>``)
    bla bla bla

Built SQL (``$``)
    bla bla bla. Only kwargs


Built SQL
`````````
    - single line per clause where
    - careful with WHERE use ``WHERE 1=1``
    - multi param per line in OR clauses
    - switching off clauses with ``FALSE``

Identity strings
````````````````
**PostgreSQL/psycopg 2.7+ Only**

Due to SQL parameter escaping (see `Bobby Tables`_), many DB API libraries won't allow you to correctly pass in variables to set ``idendity`` values in your query. These are things like column names in the SELECT, or ORDER BY clauses. The psycopg libary for PostgreSQL provides the ``quote_ident()`` function to solve this. To use it, pass a tuple of strings to your SQLpy function where the SQL contains a ``{}`` replacement field for each tuple item.

.. code-block:: sql

    -- name: select_by_id
    SELECT * FROM hello
    WHERE {} = %s;

.. code-block:: python

    >> sql.SELECT_BY_ID(cur, 0, identifers=('id',), (1,))

    [(1, u'hello')]

.. _Bobby Tables: http://bobby-tables.com/python


Showing Off
===========

.. include:: ./sudoku.rst
