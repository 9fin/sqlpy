"""
SQLpy - it's just SQL
---------------------

With SQLpy you can work directly with advanced SQL from the comfort of your Python code. Write SQL in `.sql` files and Python in `.py` files, with all the correct highlighting, linting and maintainability that comes with it.
    - Write and run the *exact* SQL code you want
    - Use advanced SQL techniques such as
        - CTEs
        - subqueries
        - recursion
        - distinct on, partition over (), etc...
    - Dynamically build SQL queries for different purposes
    - Use the latest features available in your database system

Links
`````
  - `documentation <https://sqlpy.readthedocs.io>`_
  - `development <https://github.com/9fin/sqlpy>`_
"""
from __future__ import print_function
from setuptools import setup
import os
import sys

VERSION = '0.3.4'

if sys.argv[-1] == 'build':
    os.system("python setup.py bdist_wheel")


if sys.argv[-1] == 'publish':
    os.system("twine upload -r pypi dist/*")
    args = {'version': VERSION}
    print("You probably want to also tag the version now:")
    print("  git tag -a %(version)s -m 'version %(version)s' && git push --tags" % args)
    sys.exit()


if sys.argv[-1] == 'test_publish':
    os.system("twine upload --skip-existing -r testpypi dist/*")
    sys.exit()


setup(
  name='sqlpy',
  packages=['sqlpy'],
  version=VERSION,
  description='Write actual SQL to retrieve your data.',
  long_description=__doc__,
  author='9fin',
  author_email='oss@9fin.com',
  license='MIT',
  url='https://github.com/9fin/sqlpy',
  download_url='https://github.com/9fin/sqlpy/archive/0.1.tar.gz',
  keywords=['sql', 'python', 'postgres', 'postgresql', 'mysql', 'sqlite'],
  classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 3'
  ],
  entry_points={'console_scripts': ['sqlpy=sqlpy:main']}
)
