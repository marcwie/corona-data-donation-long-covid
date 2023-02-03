from long_covid import load_from_db
from long_covid.surveydataIO import vaccinations, pcr_tests
from pathlib import Path
import pandas as pd


Path("data/01_raw").mkdir(parents=True, exist_ok=True)

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
    vacc = vaccinations(max_created_at=1649023200000)
    tests = pcr_tests(max_created_at=1649023200000)
    metadata = pd.merge(vacc, tests, on='user_id')

    vitals = load_from_db.get_vitals(metadata.user_id.unique())
    users = load_from_db.get_user_data(metadata.user_id.unique())

    vacc.to_feather("data/01_raw/vaccinations.feather")
    tests.to_feather("data/01_raw/tests.feather")
    
    vitals.to_feather('data/01_raw/vitals.feather')
    users.to_feather('data/01_raw/users.feather')

    all_user = load_from_db.get_all_valid_datenspende_user()
    all_user.to_feather('data/01_raw/all_datenspende_users.feather')

if __name__ == '__main__':
    main()