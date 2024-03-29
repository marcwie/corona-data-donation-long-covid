install:
	poetry install

activate:
	poetry shell

download:
	poetry run python long_covid/load_raw_data.py

preprocess:
	poetry run python long_covid/preprocess.py

compute:
	poetry run python long_covid/compute.py

pipeline: download preprocess compute output

setup: install download

output:
	sh scripts/execute_notebooks.sh

.PHONY: output
