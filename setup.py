from __future__ import print_function
from setuptools import setup
import os
import sys

VERSION = '0.1.0'

if sys.argv[-1] == 'build':
    os.system("python setup.py bdist_wheel")


if sys.argv[-1] == 'publish':
    os.system("twine upload -r pypi dist/*")
    args = {'version': VERSION}
    print("You probably want to also tag the version now:")
    print("  git tag -a %(version)s -m 'version %(version)s' && git push --tags" % args)
    sys.exit()


if sys.argv[-1] == 'test_publish':
    os.system("twine upload -r testpypi dist/*")
    sys.exit()


setup(
  name='sqlpy',
  packages=['sqlpy'],
  version=VERSION,
  description='Write actual SQL to retrieve your data.',
  author='9fin',
  author_email='oss@9fin.com',
  license='MIT',
  url='https://github.com/9fin/sqlpy',
  download_url='https://github.com/9fin/sqlpy/archive/0.1.tar.gz',
  keywords=['sql', 'python', 'postgres'],
  classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 3'
  ],
  entry_points={'console_scripts': ['sqlpy=sqlpy.sqlpy:main']}
)
