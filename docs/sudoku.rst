Sudoku
======

SQL is more than just a declarative data retrieval language, it's a fully Turing complete language in its own right. So it should be able to compute anything that a more typical application language could...although it may not be the most syntactically concise bit of code out there. SQL does shine in performing set operations, that is evaluating functions over groups (sets) of data (relations/tables) all at once.

Sets of data...numbers...grids. Did someone say Sudoku solver? A 9x9 `Sudoku`_ solving SQL snippet was recently added to the postgresql wiki page. Using a recursive window function, it implements a brute-force backtracking algorithm to solve the puzzle. Taking up only 32 lines, it could be less as SQL does not depend on whitespace heavily, it solves the example puzzle in under 10 seconds on a mid-range quad-core laptop from 2014 running postgres 9.6.

.. _Sudoku: https://wiki.postgresql.org/wiki/Sudoku_solver

Imagine trying to program this to be done in SQL in a similar way but via an ORM!? With SQLpy it wold be easy. (let's gloss over the amount of energy that went into writing the SQL in the first place!)

.. code-block:: sql

    -- name: sudoku_solver
    -- a sudoku solver
    -- in SQL why not
    -- note the query param %s 3 lines below
    WITH recursive board(b, p) AS (
      -- sudoku board expressed in column-major order, so substr() can be used to fetch a column
      VALUES (%s::CHAR(81), 0)
      UNION ALL SELECT b, p FROM (
        -- generate boards:
        SELECT overlay(b placing new_char FROM strpos(b, '_') FOR 1)::CHAR(81), strpos(b, '_'), new_char
        FROM board, (SELECT chr(n+ascii('b')) FROM generate_series(0, 8) n) new_char_table(new_char)
        WHERE strpos(b, '_') > 0
      ) r(b, p, new_char) WHERE
        -- make sure the new_char doesn't appear twice in its column
        -- (there are two checks because we are excluding p itself):
        strpos(substr(b, 1+(p-1)/9*9, (p-1)%9), new_char) = 0 AND
        strpos(substr(b, p+1, 8-(p-1)%9), new_char) = 0 AND
        -- make sure the new_char doesn't appear twice in its row:
        new_char NOT IN (SELECT substr(b, 1+i*9+(p-1)%9, 1)
                         FROM generate_series(0, 8) i
                         WHERE p <> 1+i*9+(p-1)%9) AND
        -- make sure the new_char doesn't appear twice in its 3x3 block:
        new_char NOT IN (SELECT substr(b, 1+i%3+i/3*9+(p-1)/27*27+(p-1)%9/3*3, 1)
                         FROM generate_series(0, 8) i
                         WHERE p <> 1+i%3+i/3*9+(p-1)/27*27+(p-1)%9/3*3)
    ) SELECT
        -- the following subquery is used to represent the board in a '\n' separated human-readable form:
        ( SELECT string_agg((
            SELECT string_agg(chr(ascii('1')+ascii(substr(b, 1+y+x*9, 1))-ascii('b')), '') r
            FROM generate_series(0, 8) x), E'\n')
          FROM generate_series(0, 8) y
        ) human_readable,
        b board,
        p depth,
        (SELECT COUNT(*) FROM board) steps
      FROM board WHERE strpos(b,'_') = 0 LIMIT 5000;

.. code-block:: python
    
    board = '__g_cd__bf_____j____c__e___c__i___jd__b__h___id____e__g__b__f_e_f____g____j_h__c_'
    results = sql.SUDOKU_SOLVER(cur, 1, (board,))

    print(results[0][0])

.. code-block:: none
    
    457298631
    819763254
    632415879
    975832146
    261549387
    384671925
    798124563
    543986712
    126357498
