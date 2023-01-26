import pandas as pd
from pathlib import Path

Path("data/03_derived").mkdir(parents=True, exist_ok=True)


def remove_unplausible_values(df, key='vital_change'):
    
    # Remove data points where users differ more than 1E6 steps from their baseline. 
    # Happens at one single instance
    df = df[df[key] < 1E6]
    
    return df


def compute_per_user_baseline(df, min_weeks):
    
    baseline = df[df.weeks_since_test < -1].groupby(['userid', 'vitalid'])[['value']].agg(['mean', 'count'])
    baseline = baseline[baseline['value']['count'] >= min_weeks]
    
    baseline.columns = baseline.columns.get_level_values(1)
    baseline = baseline.rename(columns={'mean': 'baseline'})
    
    return baseline


def weekly_deviations(vitaldata, testdata, min_points_per_week, min_weeks_for_baseline):

    df = pd.merge(vitaldata, testdata, left_on='userid', right_on='user_id')
    
    df['weeks_since_test'] = (df.date - df.test_date).dt.days // 7
    df = df[df.weeks_since_test.between(-8, 20)]
    print('Number of users that donate at least one data point between -8 and 20 weeks around test:', len(df.userid.unique()))
    
    df = remove_unplausible_values(df, key='value')
    print('Number of users after removal of unplausible values:', len(df.userid.unique()))
    
    aggregations =  {'test_result': 'first', 'value': ['mean', 'count']}
    df = df.groupby(['userid', 'vitalid', 'weeks_since_test']).agg(aggregations)
    df = df[df['value']['count'] >= min_points_per_week]
    print(f'Number of users with at least one week of {min_points_per_week} data points:', len(df.reset_index().userid.unique()))

    # Reformat dataframe
    df.columns = df.columns.get_level_values(1)
    df.reset_index(inplace=True)
    df.rename(columns={'first': 'test_result', 'mean': 'value'}, inplace=True)
    
    baseline = compute_per_user_baseline(df, min_weeks=min_weeks_for_baseline)
    print(f'Number of users with at least {min_weeks_for_baseline} weeks of baseline data:', len(baseline.reset_index().userid.unique()))

    df = pd.merge(df, baseline, on=['userid', 'vitalid'])
    df['vital_change'] = df['value'] - df.baseline
    
    df.drop(columns=['count_x', 'count_y', 'baseline', 'value'], inplace=True)
    
    return df


def user_cohorts(metadata):

    cohorts = pd.DataFrame(metadata.user_id, columns=['user_id'])

    invalid = metadata.jansen_received == True 
    full_or_booster = metadata.status.isin(['full', 'booster'])

    print('Number of users that received jansen:', invalid.sum())

    positive = metadata.test_result == 'positive'
    negative = metadata.test_result == 'negative'

    unvaccinated = (metadata.first_dose > metadata.test_date) & positive
    vaccinated = full_or_booster & (metadata.second_dose < metadata.test_date) & positive & ~invalid

    vaccinated_delta = vaccinated & (metadata.test_date < '2021-12-15')
    vaccinated_omicron = vaccinated & (metadata.test_date >= '2021-12-15')

    total = vaccinated | unvaccinated | negative 

    cohorts.loc[cohorts.user_id.isin(metadata[positive].user_id), 'positive'] = True
    cohorts.loc[cohorts.user_id.isin(metadata[negative].user_id), 'negative'] = True

    cohorts.loc[cohorts.user_id.isin(metadata[unvaccinated].user_id), 'unvaccinated'] = True
    cohorts.loc[cohorts.user_id.isin(metadata[vaccinated].user_id), 'vaccinated'] = True

    cohorts.loc[cohorts.user_id.isin(metadata[vaccinated_delta].user_id), 'vaccinated_delta'] = True
    cohorts.loc[cohorts.user_id.isin(metadata[vaccinated_omicron].user_id), 'vaccinated_omicron'] = True

    cohorts.loc[cohorts.user_id.isin(metadata[total].user_id), 'total'] = True

    cohorts.fillna(False, inplace=True)

    return cohorts


def main():

    vitals = pd.read_feather('data/02_processed/vitals_processed.feather')
    tests = pd.read_feather('data/01_raw/tests.feather')
    vaccs = pd.read_feather('data/01_raw/vaccinations.feather')

    df = weekly_deviations(vitaldata=vitals, testdata=tests, min_points_per_week=6, min_weeks_for_baseline=3)
    df.to_feather('data/03_derived/weekly_vital_deviations_per_user.feather')

    metadata = pd.merge(vaccs, tests, on='user_id')
    df = user_cohorts(metadata)
    df.to_feather('data/03_derived/user_cohorts.feather')
    

if __name__ == "__main__":
    main()
