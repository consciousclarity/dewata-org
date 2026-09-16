.PHONY: venv install build serve strict-build check clean

# Reproducible local build (see README.md for the policy).
VENV ?= /tmp/wiki-venv
PY  ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
MK  ?= $(VENV)/bin/mkdocs
PYTEST ?= $(VENV)/bin/pytest

# Build the static site into ./site (sibling of this Makefile).
CONFIG  := mkdocs.yml
SITE    := site

# Pre-build coverage and source register; downstream targets
# depend on them so a stale build never lands.
ARTIFACTS := build-artifacts

venv:
	test -d "$(VENV)" || python3 -m venv "$(VENV)"

install: venv
	"$(PIP)" install --quiet --upgrade pip
	"$(PIP)" install --quiet -r requirements.txt

build: install artifacts
	"$(PY)" scripts/build_mkdocs_config.py
	"$(MK)" build --config-file "$(CONFIG)" --site-dir "$(SITE)" --strict

serve: install artifacts
	"$(MK)" serve --config-file "$(CONFIG)"

strict-build: build
	@echo "static site built at $(SITE)"
	@echo "$$ ls -la"

# artifacts only — useful when reviewing without rebuilding site.
artifacts: install
	"$(PY)" scripts/build_source_register.py
	"$(PY)" scripts/build_coverage_report.py

check: install
	"$(PYTEST)" tests -q

clean:
	rm -rf "$(SITE)" "$(ARTIFACTS)"
	rm -rf .pytest_cache tests/.pytest_cache
	find . -name __pycache__ -prune -exec rm -rf {} +
