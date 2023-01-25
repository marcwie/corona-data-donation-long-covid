from long_covid import load_from_db
from datenspende.surveydataIO import vaccinations, pcr_tests
from pathlib import Path
import pandas as pd


Path("data/raw").mkdir(parents=True, exist_ok=True)

def main():
    """
    Load all raw input data.

    Specifically this includes:
    - Vaccination dates
    - Test results and dates
    - Vital data
    - User data

    All data is stored under data/raw/ for later preprocessing.    
    """
    vacc = vaccinations()
    tests = pcr_tests()
    metadata = pd.merge(vacc, tests, on='user_id')

    vitals = load_from_db.get_vitals(metadata.user_id.unique())
    users = load_from_db.get_user_data(metadata.user_id.unique())

    vacc.to_feather("data/raw/vaccinations.feather")
    tests.to_feather("data/raw/tests.feather")
    
    vitals.to_feather('data/raw/vitals.feather')
    users.to_feather('data/raw/users.feather')

if __name__ == '__main__':
    main()