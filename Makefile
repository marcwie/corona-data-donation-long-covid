install:
	poetry install

activate:
	poetry shell

download:
	poetry run python long_covid/load_raw_data.py

setup: install download