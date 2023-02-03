import pandas as pd
from pathlib import Path
import numpy as np

Path("data/02_processed").mkdir(parents=True, exist_ok=True)


def drop_apple_sleep(df):
    """Remove apple users after 2021 October update that messes with sleep data.

    Args:
        df (pandas.DataFrame): The data frame containing the vital data.

    Returns:
        pandas.DataFrame: Vital data without corrupt apple data.
    """
    # 
    invalid = (df.deviceid == 6) & (df.vitalid == 43) & (df.date >= '2021-10-20')
    df = df[~invalid]
    print("Number of users after removing invalid apple users:", len(df.userid.unique()))

    return df


def normalize(df, by=['vitalid', 'date', 'deviceid']):
    
    norm = df.groupby(by)[['value']].mean().rename(columns={'value': 'daily_mean'})
    norm.reset_index(inplace=True)
    df = pd.merge(df, norm, on=by)
    df['normalized_value'] = df['value'] - df['daily_mean']
    df.rename(columns={'value': 'raw_value'}, inplace=True)
    df.rename(columns={'normalized_value': 'value'}, inplace=True)

    return df #.drop(columns='daily_mean') 


def drop_devides_with_low_numbers(df):

    print('Dropping some devices...')
    invalid = df.deviceid.isin([19, 46, 48])
    df = df[~invalid]

    return df


def preprocess_vital_data(input_file):

    df = pd.read_feather(input_file)

    df = drop_devides_with_low_numbers(df)
    df = drop_apple_sleep(df)
    df = normalize(df)

    df.to_feather('data/02_processed/vitals_processed.feather')


def add_user_age(df):
    
    df['age'] = np.floor((2022 + 4 / 12) - df['birth_date'] + 2.5)
    return df


def preprocess_user_data(input_file):

    df = pd.read_feather(input_file)

    df = add_user_age(df)

    df.to_feather('data/02_processed/users_processed.feather')


def main():

    preprocess_vital_data('data/01_raw/vitals.feather')
    preprocess_user_data('data/01_raw/users.feather')

if __name__ == "__main__":
    main()