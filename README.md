# Installation

The package requires [poetry](https://python-poetry.org/). Make sure to have it installed and run `make install` after cloning this repository to install all dependencies.

# Setup

In order to interact with the database create a file named `.env` in the root of the repository using the following template and filling in your credentials. Do not add this file to git.

```
HOST = 
PORT = 
DBNAME = 
DBUSER = 
PASSWORD = 
```

# Usage

You can run the entire analysis pipeline using `make pipeline` which executes the following commands in order:

1. `make download` which downloads all required input data from the database (make sure you have your credentials set as explained above). See `long_covid/load_raw_data.py` for details.
2. `make preprocess` which performs the necessary preprocessing steps for later analysing the data. This includes dropping apple users with invalid sleep data or certain devices with only few users as well as computing the age of all users from their approximate birth year. See `long_covid/preprocess.py` for details.
3. `make compute` which computes all final data that is required for plotting figures. This includes the computation of all baselines and the corresponding weekly deviations inv vital data. See `long_covid/compute.py` for details.
4. `make output` which executes all `jupyter`-notebooks in the `notebooks` folder that create figures for the final paper. Each notebook creates one specific (set of) figure(s). See the content of `notebooks` for details. 

Afterwards all figures that are necessary to reproduce the paper should be places in `output` and all corresponding input and processed data can be found in `data`. 