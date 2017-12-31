.. _howitworks:

How it works
============

Python `PEP249`_ is the current standard for implementing APIs between Python and relational databases. From the PEP text
::
    This API has been defined to encourage similarity between
    the Python modules that are used to access databases.

The standard defines a number of common objects, methods and operations that any library must implement to be compliant. A slew of Python libraries exist for most if not all relational database systems, all adhering to the same specification. All of them boiling down to sending SQL commands to and returning their results from the database server to the Python runtime. 

SQLpy was written as a lightweight helper around your already existing Python DB API 2.0 library, with no assumptions made about the underlying library of choice. Essentially only wrapping the ``cur.execute()`` and ``cur.executemany()`` methods. Connection and Cursor object creation preferences are left up to you.

SQLpy leverages the powerful ``functools`` module within Python and creates prepared functions reading SQL statements by reading from a queries file(s) within your project. The SQL statements have a special form that SQLpy recognises and this determines how the statement is prepared and eventually executed. Depending on if it is a simple select, a delete or a different type of statement.

For the following sections, let's assume we have a database table ``hello`` with the following data.

====  ==========
 id    message
====  ==========
 1     hello
 2     SQLpy
 3     PostgreSQL!
====  ==========

.. _PEP249: https://www.python.org/dev/peps/pep-0249/

Executing the functions
-----------------------
To execute a SQL statement and get results, just call the method by name on the :class:`sqlpy.Queries` object. Note: The name is cast to uppercase (if this causes an uproar it can be made optional in a patch release).

.. code-block:: python
    
    sql = sqlpy.Queries('queries.sql')
    ....
    results = sql.SQL_STATEMENT(cur, fetch_n, args=None, identifiers=None, log_query_params=LOG_QUERY_PARAMS, **kwargs)

Parameters
    - :obj:`cur`: A Cursor object. Can be any cursor type you want.
    - fetch_n (:obj:`int`): How many results to fetch back. When set to ``0`` the underlying cursor performs a ``fetchall()`` and all the results are returned.
    - args (:obj:`tuple`): A sequence of positional parameters in the query.
    - identifiers (:obj:`tuple`): A sequence of positional strings to use to format the query before execution. Used with `identity strings`_. Default is ``None``.
    - log_query_params (:obj:`boolean`): A flag to enable or disable logging out of the parameters sent to the query. Some data is sensitive and should not be visible in log entries. Default is :class:`sqlpy.config.LOG_QUERY_PARAMS` which is ``True``.
    - \**kwargs (:obj:`dict`): A dictionary of named parameters to send to the query. If specified the values in ``args`` will be ignored.


Query types
-----------
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

SELECT
    There is no token at the end of the name string

INSERT/UPDATE/DELETE
    There is a ``!`` token at the end of the name string

With RETURNING
    There is a ``<!>`` token at the end of the name string

Built SQL
    There is a ``$`` token at the end of the name string
    Can only use ``pyformat`` named parameters


Built SQL
`````````
In your application you will likely want to take different paths retrieving data depending on the current values or the variables you have available. One example could be looking up values from a table, using a varying number of search parameters. Writing a separate query for each case would be repetitive, and difficult as you need to know ahead of time the possible combinations.

SQLpy offers the functionality to dynamically build SQL queries based on the query parameters passed to the prepared function. For a **BUILT SQL** query:
    - An internal lookup map is created when the query is being parsed.
    - Each line of the query is collected and inserted into a dictionary with information on its position (line number) in the overall query, and the query line itself.
    - The key for each entry is the parameter contained within that line.
    - Any lines with no parameter (most of the stuff before there ``WHERE`` clause), are collected under the same key.

When executed the query is reassembled in the correct line order, and lines containing parameters that have also been passed to the function as ``**kwargs`` are included. Then the final SQL is sent to the database driver as normal.

Example.

.. code-block:: python
    
    sql = sqlpy.Queries('queries.sql')
    ....
    kwargs = {'id_low': 1}
    results = sql.BUILT_SQL_STATEMENT(cur, 0, **kwargs)

Would execute the SQL.

.. code-block:: sql

    SELECT * FROM hello
    WHERE id = 1;

**This design leads to some minor restrictions in how to write your queries that are explained below.**

Single line per clause
    It's best to lay out queries with a newline for each filter clause you use. This is to ensure that the resulting SQL query is built with the correct lines in place, and not with extra parameters for which there are no matching function inputs for.
    
    .. code-block:: sql

        -- name: built_sql_statement$
        -- a built up sql statement
        -- newline for each parameter
        SELECT * FROM hello
        WHERE id = %(id_low)s
        OR id = %(id_high)s
        AND message = %(msg)s;    

Careful with ``WHERE``
    SQL queries are asymmetrical, you always start the filtering clauses with ``WHERE``, but after that you use ``AND`` or ``OR``. This means that if the parameter contained within the ``WHERE`` clause is not passed to the function, the query will be built without it, and that is invalid SQL. To solve this, you can use ``WHERE 1=1``. This always evaluates to ``True`` and is effectively a pass-through value, always ensuring the ``WHERE`` clause is present in your queries.

    .. code-block:: sql

        -- name: built_sql_statement$
        -- a built up sql statement
        SELECT * FROM hello
        WHERE 1=1
        AND id = %(id_low)s
        OR id = %(id_high)s
        AND message = %(msg)s;

Multiple parameters per line
    Sometimes you can not avoid multiple parameters that must be grouped together, such as in compound ``AND-OR`` clauses. Ensure you supply all the necessary argument to the function to get the correct output. 

    .. code-block:: sql

        -- name: built_sql_statement$
        -- a built up sql statement
        SELECT * FROM hello
        WHERE 1=1
        AND (id = %(id_low)s OR id = %(id_high)s);

    .. code-block:: python
        
        sql = sqlpy.Queries('queries.sql')
        ....
        kwargs = {'id_low': 1, 'id_high': 3}
        results = sql.BUILT_SQL_STATEMENT(cur, 0, **kwargs)
    
    executes...
    
    .. code-block:: sql

        SELECT * FROM hello
        WHERE 1=1
        AND (id = 1 OR id = 3);

Missing parameters
    In oder to maintain valid SQL output SQLpy will replace missing parameters with ``None``, and this usually transforms to ``NULL`` when passed to the database. In this next example the result will still be correct, as the ``id`` column would not contain any ``NULL`` values, so the ``OR`` clause has no effect.

        **Note:** PostgrSQL does not correctly evaluate the syntax ``column = NULL``, instead you should use ``column is NULL`` or ``column is not NULL``. When searching columns that could contain ``NULL`` values, it's best to use the ``ANY()`` operator, where an array of values to check is passed to it. It behaves like ``IN ()``, and it correctly handles ``NULL`` values. The added benefit is that you can test for multiple conditions in clauses too, so it's a useful pattern regardless. Check out `PostgreSQL Arrays`_ for more info.

        .. _PostgreSQL Arrays: https://www.postgresql.org/docs/current/static/arrays.html

    .. code-block:: sql

        -- name: built_sql_statement$
        -- a built up sql statement
        SELECT * FROM hello
        WHERE 1=1
        AND (id = ANY(%(id_low)s) OR id = ANY(%(id_high)s));

    .. code-block:: python
        
        sql = sqlpy.Queries('queries.sql')
        ....
        kwargs = {'id_low': [1]}
        results = sql.BUILT_SQL_STATEMENT(cur, 0, **kwargs)
    
    executes...
    
    .. code-block:: sql

        SELECT * FROM hello
        WHERE 1=1
        AND (id = ANY('{1}') OR id = ANY('{NULL}'));

Switching off parameters
    The philosophical discussion on the merits/lack of on the use of ``NULL`` in SQL systems is well known, but the value (or is it a Type?) is used everywhere. This just means you need to take this into account when writing your data retrieval queries with ``NULL`` values. 

    Following from the example above, say you have a compound ``OR`` clause on a column that can have ``NULL`` values. At certain times, you may not supply all the values required to the function, so ``None`` is substituted in its place. This is a problem because you don't want the case where extra results are returned that match the other side of the ``OR``.

    We have new data...

        ====  ============  ==========
         id    message       message2
        ====  ============  ==========
         1     hello         there
         2     SQLpy         NULL
         3     PostgreSQL!   rules!
         4     hello         friend
        ====  ============  ==========

    .. code-block:: sql

        -- name: built_sql_statement$
        -- a built up sql statement
        SELECT * FROM hello
        WHERE 1=1
        AND (message = ANY(%(msg)s) OR message2 = ANY(%(msg2)s));
    
    .. code-block:: python
        
        sql = sqlpy.Queries('queries.sql')
        ....
        kwargs = {'message': ['hello']}
        results = sql.BUILT_SQL_STATEMENT(cur, 0, **kwargs)
    
    executes...
    
    .. code-block:: sql

        SELECT * FROM hello
        WHERE 1=1
        AND (message = ANY('{"hello"}') OR message2 = ANY('{NULL}'));

    returns...

        ====  ============  ==========
         id    message       message2
        ====  ============  ==========
         1     hello         there
         2     SQLpy         NULL
         4     hello         friend
        ====  ============  ==========    

    We don't want row 2 in this case. To solve this, you can use a little SQL syntax gymnastics to write the ``OR`` clause in such a way that ``NULL`` does not bring in incorrect results.

    .. code-block:: sql

        -- name: built_sql_statement$
        -- a built up sql statement
        SELECT * FROM hello
        WHERE 1=1
        AND ((FALSE OR message = ANY(%(msg)s)) OR (FALSE OR message2 = ANY(%(msg2)s)));   

    The clauses are enclosed in a second set of parenthesis in the form ``(FALSE OR column=%(name)s)``. If the parameter is replaced with a ``NULL`` then this "switches-off" that entire check, because ``SELECT FALSE OR NULL --> NULL``. So ``(NULL OR (FALSE OR column=VALUE))`` only evaluates the right hand side of the statement. This would produce the correct output.

    executes...
    
    .. code-block:: sql

        SELECT * FROM hello
        WHERE 1=1
        AND (FALSE OR message = ANY('{"hello"}' OR (FALSE OR message2 = ANY('{NULL}')));
        -- this reduces to
        -- AND (message = ANY('{"hello"}' OR (NULL));
        -- and again to
        -- AND (message = ANY('{"hello"}'));

    returns...

        ====  ============  ==========
         id    message       message2
        ====  ============  ==========
         1     hello         there
         4     hello         friend
        ====  ============  ========== 

    **Warning: only tested in PostgreSQL**

NULL with care
    As you can see this is very tricky and also very database specific. It's probably best to avoid writing such queries in the first place, and taking a second look at your data model could also reveal a better design. 

    But you could still come across and need this pattern. However now that the problem is exposed purely as a SQL problem, you can now seek help in SQL Q&A forums in which there is about 50 years (and counting) of SQL language experience!

Strict parse
    If you don't like to live dangerously, then you can enable a safety mechanism around Built queries. If you initialise the :class:`sqlpy.Queries` object as ``sqlpy.Queries(..., strict_parse=True)``, a :class:`sqlpy.exceptions.SQLArgumentException` is raised when a named argument is supplied which does not match a SQL clause.

**Built queries are limited to only SELECT queries at the moment.** There will definitely be some interesting edge cases arising from the layout and use of Built queries! If you see anything odd and think it should be handled, then do open an issue on GitHub.

.. _identity strings:
Identity strings
````````````````

**PostgreSQL/psycopg 2.7+ Only**

Due to SQL parameter escaping (see `Bobby Tables`_), many DB API libraries won't allow you to correctly pass in variables to set ``identity`` values in your query. These are things like column names in the SELECT, or ORDER BY clauses. The psycopg libary for PostgreSQL provides the ``quote_ident()`` function to solve this. To use it, pass a tuple of strings to your SQLpy function where the SQL contains a ``{}`` replacement field for each tuple item.

.. code-block:: sql

    -- name: select_by_id
    SELECT * FROM hello
    WHERE {} = %s;

.. code-block:: python

    >> sql.SELECT_BY_ID(cur, 0, identifiers=('id',), (1,))

    [(1, u'hello')]

.. _Bobby Tables: http://bobby-tables.com/python

===========
Showing Off
===========

.. include:: ./sudoku.rst
