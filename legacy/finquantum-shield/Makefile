.PHONY: install test lint run bench clean

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short

lint:
	ruff check . --fix

run:
	python start_all.py

bench:
	python benchmarks/run_benchmarks.py

analysis:
	python analysis/qber_comparison.py
	python analysis/run_attack_scenarios.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
