
# ----------------
ifeq ($(OS), Windows_NT)
	ifdef MSYSTEM
        HAS_UV := $(shell uv --version 2> /dev/null)
        HAS_PYTHON := $(shell py --version 2> /dev/null)
        VENV_PYTHON := .venv/Scripts/python
        CLEAN_CMD = rm -rf
    else
        HAS_UV := $(shell uv --version 2> nul)
        HAS_PYTHON := $(shell py --version 2> nul)
        VENV_PYTHON := .venv/Scripts/python
        CLEAN_CMD = powershell -Command Remove-Item -Recurse -Force
    endif
	VENV_CMD = py -m
else
	HAS_UV := $(shell uv --version 2> /dev/null)
	HAS_PYTHON := $(shell python3 --version 2> /dev/null)
    VENV_PYTHON := .venv/bin/python
	CLEAN_CMD = rm -rf
	VENV_CMD = python3 -m
endif
TOUCH_CMD = $(VENV_PYTHON) -c "import pathlib,sys; pathlib.Path(sys.argv[1]).touch()"

# ----------------
ifdef HAS_UV
	RUN_CMD = uv run
	VENV_CMD = uv
	PIP_INSTALL_CMD = $(VENV_CMD) pip install
else
	ifdef HAS_PYTHON
		RUN_CMD = $(VENV_PYTHON) -m
		PIP_INSTALL_CMD = $(RUN_CMD) pip install
	else
		$(error "Install uv or python")
	endif
endif

# ----------------
.DEFAULT_GOAL := check

## ----------------
.PHONY: venv
.venv:
	$(MAKE) venv
	$(MAKE) install

.venv/check-installed: pyproject.toml | .venv
	$(MAKE) install-check
	$(TOUCH_CMD) .venv/check-installed

.venv/test-installed: pyproject.toml | .venv
	$(MAKE) install-test
	$(TOUCH_CMD) .venv/test-installed

venv:
	$(VENV_CMD) venv .venv

## ----------------
.PHONY: install install-dev install-check install-test

install: | .venv
	$(PIP_INSTALL_CMD) -e .

install-check: | .venv
	$(PIP_INSTALL_CMD) -e ".[check]"

install-test: | .venv
	$(PIP_INSTALL_CMD) -e ".[test]"

install-dev: | .venv
	$(PIP_INSTALL_CMD) -e ".[dev,test,check]"

## ----------------
.PHONY: clean lint format-diff typecheck
check: lint format-diff typecheck

lint: .venv/check-installed
	$(RUN_CMD) ruff check .

format-diff: .venv/check-installed
	$(RUN_CMD) ruff format . --diff

typecheck: .venv/check-installed .venv/test-installed
	$(RUN_CMD) mypy

## ----------------
.PHONY: fix clean
fix: .venv/check-installed
	$(RUN_CMD) ruff check . --fix
	$(RUN_CMD) ruff format .

clean:
	$(CLEAN_CMD) .venv

## ----------------
.PHONY: test test-cov
test: .venv/test-installed
	$(RUN_CMD) pytest

test-cov: .venv/test-installed
	$(RUN_CMD) pytest --cov=src --cov-report=term --cov-report=html

## ----------------
.PHONY: coverage-report
coverage-report:
	$(RUN_CMD) coverage report --format=markdown
