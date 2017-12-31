=========
Changelog
=========

Current release
===============

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
