test:
	@ pytest --cov-report term-missing --cov=./sqlpy

flake8:
	@ flake8 --ignore=E501,F401,E128,E402,E731,F821 ./sqlpy

pyflakes:
	@ pyflakes ./sqlpy

check: flake8 pyflakes test
