# ------------------------------------------------------------------------------
# Platform Detection & Utility Setup
# ------------------------------------------------------------------------------
IS_POSIX_SHELL := $(findstring sh,$(notdir $(SHELL)))

ifeq ($(OS), Windows_NT)
    HAS_UV := $(strip $(shell uv --version))
    HAS_PYTHON := $(strip $(shell py --version))
    VENV_CMD = py -m
    ifneq ($(IS_POSIX_SHELL),)
        VENV_PYTHON := .venv/Scripts/python
        CLEAN_CMD = rm -rf
    else
        VENV_PYTHON := .venv\Scripts\python
        CLEAN_CMD = cmd /c rmdir /s /q
    endif
else
    HAS_UV := $(strip $(shell uv --version))
    HAS_PYTHON := $(strip $(shell python3 --version))
    VENV_PYTHON := .venv/bin/python
    CLEAN_CMD = rm -rf
    VENV_CMD = python3 -m
endif

TOUCH_CMD = $(VENV_PYTHON) -c "import pathlib,sys; pathlib.Path(sys.argv[1]).touch()"

# ------------------------------------------------------------------------------
# Command Routing (uv vs standard python)
# ------------------------------------------------------------------------------
ifneq ($(HAS_UV),)
    RUN_CMD = uv run --no-sync
    VENV_CMD = uv
    PIP_INSTALL_CMD = $(VENV_CMD) pip install
else ifneq ($(HAS_PYTHON),)
    RUN_CMD = $(VENV_PYTHON) -m
    PIP_INSTALL_CMD = $(RUN_CMD) pip install
else
    $(error "Neither 'uv' nor 'python/py' was found in PATH.")
endif

# ------------------------------------------------------------------------------
# Targets
# ------------------------------------------------------------------------------
.DEFAULT_GOAL := check

.PHONY: venv install install-dev install-check install-test check lint format-diff typecheck fix clean test test-cov coverage-report

# Virtual environment creation
.venv:
	$(VENV_CMD) venv .venv

venv: .venv

# Dependency installation markers
.venv/check-installed: pyproject.toml | .venv
	$(PIP_INSTALL_CMD) -e ".[check]"
	$(TOUCH_CMD) .venv/check-installed

.venv/test-installed: pyproject.toml | .venv
	$(PIP_INSTALL_CMD) -e ".[test]"
	$(TOUCH_CMD) .venv/test-installed

# Explicit install shortcuts
install: | .venv
	$(PIP_INSTALL_CMD) -e .

install-check: .venv/check-installed

install-test: .venv/test-installed

install-dev: | .venv
	$(PIP_INSTALL_CMD) -e ".[dev,test,check]"

# Code Quality Checks
check: lint format-diff typecheck

lint: .venv/check-installed
	$(RUN_CMD) ruff check .

format-diff: .venv/check-installed
	$(RUN_CMD) ruff format . --diff

typecheck: .venv/check-installed .venv/test-installed
	$(RUN_CMD) mypy

# Code Formatting & Fixes
fix: .venv/check-installed
	$(RUN_CMD) ruff check . --fix
	$(RUN_CMD) ruff format .

clean:
	$(CLEAN_CMD) .venv
	$(CLEAN_CMD) .pytest_cache || true
	$(CLEAN_CMD) .mypy_cache || true

# Testing
test: .venv/test-installed
	$(RUN_CMD) pytest

test-cov: .venv/test-installed
	$(RUN_CMD) pytest --cov=src --cov-report=term --cov-report=html

coverage-report: .venv/test-installed
	$(RUN_CMD) coverage report --format=markdown