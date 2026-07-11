PYTHON ?= python

.PHONY: install migrate run test check

install:
	cd web && $(PYTHON) -m pip install -r requirements/dev.txt

migrate:
	cd web && $(PYTHON) manage.py migrate

run:
	cd web && $(PYTHON) manage.py runserver

test:
	cd web && $(PYTHON) manage.py test

check:
	cd web && $(PYTHON) manage.py check
