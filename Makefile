help:
	@cat make-usage

install: build
	@doas mv dist/ormgenerator /usr/local/bin

test:
	@poetry run pytest -vv -n auto --disable-socket --cov=. --cov-report html tests

qa: test
	@echo
	@echo "=========================="
	@echo "=== Checking main code ==="
	@echo "=========================="
	@echo
	@echo "=== pylint ==="
	-@poetry run pylint ormgenerator
	@echo "=== ruff ==="
	-@poetry run ruff check ormgenerator
	@echo "=== pyright ==="
	-@poetry run pyright ormgenerator
	@echo "=== checking types with mypy ==="
	-@poetry run mypy --strict ormgenerator
	@echo "=== checking formatting with black ==="
	-@poetry run black -l 79 --check ormgenerator
	@echo
	@echo "======================"
	@echo "=== Checking tests ==="
	@echo "======================"
	@echo
	@echo "=== pylint ==="
	-@poetry run pylint tests
	@echo "=== ruff ==="
	-@poetry run ruff check tests
	@echo "=== pyright ==="
	-@poetry run pyright tests
	@echo "=== checking types with mypy ==="
	-@poetry run mypy --strict tests
	@echo "=== checking formatting with black ==="
	-@poetry run black -l 79 --check tests
	@echo "========================================"
	@echo "=== Checking import order with isort ==="
	@echo "========================================"
	@PATCH="$$(poetry run isort ormgenerator tests --diff)" && echo $$PATCH &&test -z "$$PATCH"

format:
	@poetry run black -l 79 ormgenerator
	@poetry run black -l 79 tests
	@poetry run isort ormgenerator tests

.PHONY: format help qa test
