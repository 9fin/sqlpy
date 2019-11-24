=========
Changelog
=========

Current release
===============

0.3.4 0.3.5
-----
Bugfix
    - use a more broad import for ``quote_ident`` function, to allow instrumentation libraries to correctly use the patched version `#24 <https://github.com/9fin/sqlpy/issues/24>`_

Previous releases
=================

0.3.3
-----
Bugfix
    - identifier formatting in built sql not happening `#21 <https://github.com/9fin/sqlpy/issues/21>`_

0.3.2
-----
Major Updates
    - Support sets of identifier groups and using named parameters `#20 <https://github.com/9fin/sqlpy/issues/20>`_

0.3.1
-----
Breaking Changes
    - revert returning cursor as part of query execution `#17 <https://github.com/9fin/sqlpy/issues/17>`_

Major Updates
    - expose logging query args configuration in Queries object initialisation `#18 <https://github.com/9fin/sqlpy/issues/18>`_


0.3.0
-----
Breaking Changes
	- updated API design for the query function `#15 <https://github.com/9fin/sqlpy/issues/15>`_

Major Updates
	- add separated ``cur.fetchone`` cursor method `#15 <https://github.com/9fin/sqlpy/issues/15>`_
	- add ``cur.callproc`` `#12 <https://github.com/9fin/sqlpy/issues/12>`_
	- transparently switch to using the more efficient ``execute_values`` with Psycopg2 `#16 <https://github.com/9fin/sqlpy/issues/16>`_
	- updated docs

Minor Fixes
	- fix type in ``load_queries`` `#14 <https://github.com/9fin/sqlpy/issues/14>`_
	- initial strip of whitespace on input query files
	- ensure multi-file queries joined correctly with double newline `#10 <https://github.com/9fin/sqlpy/issues/10>`_
	- make uppercase of function name optional
	- moved logging helper back into main module `#8 <https://github.com/9fin/sqlpy/issues/8>`_

0.2.0
-----
Major update
    - Remove coupling to PostgreSQL and psycopg2 by conditionally importing from psycopg2
    - Changed the logger to add ``NullHandler()`` by default
    - Changed ``fetchone()`` to ``fetchmany()``
    - Improved exception handling with better Exceptions
    - A lot of internal code refactoring
    - Documentation, a lot of Documentation

0.1.0
-----
First pypi upload of the project. Lacking good documentation and behavior was tied to PostgreSQL and psycopg2.
