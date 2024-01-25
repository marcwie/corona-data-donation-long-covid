# Premise

Contains all software and notebooks to reproduce the figures in [Wiedermann et al., (2023)](https://academic.oup.com/pnasnexus/article/2/7/pgad223/7225910). Unfortunately, the input data is not yet publicly available. Please see the *data availability statement* in the aforementioned paper for details. Package structure is based on an earlier version of my personal [data science template](https://github.com/marcwie/datascience-template).

# Purpose

Parse wearable sensors and survey data collected within the Corona Data Donation project (*Corona Datenspende*, click [here](https://corona-datenspende.github.io/en/) for more information). The Corona Data Donation Project is one of the largest citizen science initiatives worldwide. From 2020 to 2022, more than 120,000 German residents donated continuous daily measurements of resting heart rate, physical activity and sleep timing for the advancement of public health research. These data streams were collected passively through a dedicated smartphone app, seamlessly connecting with participants’ fitness trackers and smartwatches. Additionally, participants actively engaged in regular surveys, sharing insights into their health and well-being during the COVID-19 pandemic. 

This package analyzes the positive effects of vaccinations against COVID-19 for mitigating long-term effects of an infection with SARS-CoV-2. For this purpose, it parses daily resting hearte rate, step count and sleep duration measured from wearable devices (e.g, Apple Watch, Fitbit, Garmin) and survey data on COVID-19 test results, test dates and vaccination status.  

# Installation

The package requires [poetry](https://python-poetry.org/). Make sure to have it installed and run `make install` after cloning this repository to install all dependencies.

# Setup

After gaining data access you will receive instructions for setting up a VPN. You can then interact with the database by creating a file named `.env` in the root of the repository using the following template and filling in your credentials. Do not add this file to your git repository.

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

# External data

The package relies on some external that ships with this repository. All such data is found in `data/00_external/`. This folder holds one file `statistic_id1365_bevoelkerung-deutschlands-nach-relevanten-altersgruppen-2020.xlsx`. It contains the age distribution of the German population as of December 2020 and was downloaded from `https://de.statista.com/statistik/daten/studie/1365/umfrage/bevoelkerung-deutschlands-nach-altersgruppen/`. 

If one now opens the aforementioned website and downloads the data again one is provided with a newer estimate from December 2022 so that the old file shipped with this repository is no longer officially available. For the sake of reproducibility with the paper we refrain from updating the file to the new version and stick with the estimates from December 2020. 
