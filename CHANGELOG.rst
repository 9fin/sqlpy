=========
Changelog
=========

Current release
===============

0.3.0
-----
Breaking Changes
	- updated API design for the query function #15

Major Updates
	- add separated ``cur.fetchone`` cursor method #15
	- add ``cur.callproc`` #12
	- transparently switch to using the more efficient ``execute_values`` with Psycopg2 #16
	- updated docs

Minor Fixes
	- fix type in ``load_queries`` #14
	- intial strip of whitespace on input query files
	- ensure multi-file queries joined correctly with double newline #10
	- make uppercase of function name optional
	- moved logging helper back into main module #8

0.2.0
-----
Major update
    - Remove coupling to PostgreSQL and psycopg2 by conditionally importing from psycopg2
    - Changed the logger to add ``NullHandler()`` by default
    - Changed ``fetchone()`` to ``fetchmany()``
    - Improved exception handling with better Exceptions
    - A lot of internal code refactoring
    - Documentation, a lot of Documentation

Previous releases
=================

0.1.0
-----
First pypi upload of the project. Lacking good documentation and behavior was tied to PostgreSQL and psycopg2.
