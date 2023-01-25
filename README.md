# Installation

Run `poetry install` after cloning this repository to install all dependencies.

# Setup

In order to interact with the database create a file named `.env` in the root of the repository using the following template and filling in your credentials. Do not add this file to git.

```
HOST = 
PORT = 
DBNAME = 
DBUSER = 
PASSWORD = 
```

# Download raw data

Use `poetry run python long_covid/load_raw_data.py` to download all required input data.