.PHONY: install test lint run clean bench verify

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short

test-stats:
	python -m pytest tests/test_bb84_statistics.py -v

test-security:
	python -m pytest tests/test_kms_security.py -v

lint:
	ruff check . --fix
	ruff format .

run:
	python start_all.py

run-demo:
	python run_demo.bat

bench:
	python benchmarks/run_benchmarks.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache

verify:
	python verify_all.py
	@echo "✅ All verifications passed"
