"""
Methods for extracting survey data from the ROCS database.
"""
from datetime import timedelta, datetime
from long_covid.load_from_db import run_query
import pandas as pd
import numpy as np


def weekly_pcr_tests(max_created_at, drop_session_id=True):

    """
    Self-reported results and dates of COVID tests from the weekly 'Erleben &
    Verhalten' study.

    Since 'Erleben & Verhalten' provides a weekly questionnaire, multiple
    test-results per user are potentially available.

    NOTE: Even though the survey also asks for antigen or antibody tests, only
    PCR-tests are considered here.

    Returns
    -------
    test_data : pd.DataFrame

    The DataFrame has three columns (user_id, test_result, test_data) and an
    integer index like so:

              user_id test_result  test_date
        0        1787    negative 2021-11-15
        1        2966    negative 2021-11-17
        ...       ...         ...        ...
        3886  1225020    negative 2021-12-20
        3887  1225119    negative 2021-12-20

    Since the survey asks whether a test was taken during the last seven days,
    the entry in test_date always corresponds to the beginning of that
    seven-day period.
    """

    query = f"""
    SELECT
        answers.user_id,
        choice.text,
        answers.question,
        answers.created_at,
        answers.questionnaire_session
    FROM
        datenspende.answers, datenspende.choice
    WHERE
        answers.question IN (91, 10) AND
        answers.created_at > 1634630400000 AND
        answers.created_at < {max_created_at} AND
        answers.element = choice.element
    """
    df = run_query(query)

    # Convert unix time step to datetime. The division ensures that times are
    # set to midnight
    df['created_at'] = pd.to_datetime(df['created_at'] // 1000 // 60 // 60 // 24, unit='d')

    # Substract one week to get the first possible date of the test
    df['created_at'] -= timedelta(days=7)

    # Query only session where users took a PCR-test
    sessions_with_pcr = df[df.text == 'PCR-Test'].questionnaire_session.unique()
    df = df[df.questionnaire_session.isin(sessions_with_pcr)]

    # Drop information on test-type, since its no longer needed
    df = df[df.question != 91]
    if drop_session_id:
        df.drop(columns=['question', 'questionnaire_session'], inplace=True)

    # Recode answers
    df.replace(
        {
            'Positiv (Infektion bestätigt)': 'positive',
            'Negativ (Infektion nicht bestätigt)': 'negative'
        },
        inplace=True
    )

    # Rename columns to match their meaning after the transformation
    df.rename(columns={'text': 'test_result', 'created_at': 'test_date'}, inplace=True)

    # Sort
    df.sort_values(by=['user_id', 'test_date'], inplace=True)

    df.reset_index(inplace=True, drop=True)

    return df


def one_off_pcr_tests(max_created_at):

    """
    Self-reported results and dates of COVID tests from the 'tests & symptoms'
    study.

    The 'test & symptoms' study is a one-off survey. So only one test-result
    per user is available.  This is either the result and date of the first
    positive test or the date and result of the first ever test if all results
    were negative.

    Note that only PCR-tests are surveyed here.

    Returns
    -------
    test_data : pd.DataFrame

    The DataFrame has three columns (user_id, test_result, test_data) and an
    integer index like so:

               user_id test_result  test_date
        0          375    negative 2021-10-11
        1          387    positive 2021-03-29
        ...        ...         ...        ...
        12329  1225273    negative 2020-08-10
        12330  1225284    negative 2021-09-13

    The entry in test_date is always the first day (monday) of the week of the
    test.
    """

    query = f"""
    SELECT
        answers.user_id,
        choice.text,
        answers.question,
        answers.questionnaire_session
    FROM
        datenspende.answers, datenspende.choice
    WHERE
        answers.question IN (83, 129) AND
        answers.created_at > 1634630400000 AND
        answers.created_at < {max_created_at} AND
        answers.element = choice.element
    """
    df = run_query(query)

    # Split dataframe in test-results and test-date
    df_results = df[df.question == 129].drop(columns='question')
    df_date = df[df.question == 83].drop(columns='question')

    # Merge on user_id and session so that user_id, result, date form one row
    df = pd.merge(df_results, df_date, on=['user_id', 'questionnaire_session'])

    # Rename columns to sth meaningful
    df.rename(columns={'text_x': 'test_result', 'text_y': 'test_date'}, inplace=True)

    # Due to a bug on thryve's end some users can submit test results multiple
    # times.  In that case we only keep the last response indicated by the
    # largest questionnaire_session.
    df.sort_values(by=['user_id', 'questionnaire_session'], inplace=True)
    df.drop_duplicates(subset='user_id', keep='last', inplace=True)
    df.drop(columns='questionnaire_session', inplace=True)

    # Rename test-results and drop entries where results are unknown
    df.test_result = df.test_result.str.replace('Ja', 'positive', regex=False)
    df.test_result = df.test_result.str.replace('Nein', 'negative', regex=False)
    df = df[df.test_result != 'nicht bekannt']

    # Reformat the date from an interval to the first day of the test week
    df.test_date = [datetime.strptime(text[:10], '%d.%m.%Y') for text in df.test_date]

    df.reset_index(inplace=True, drop=True)

    return df


def pcr_tests(max_created_at=1672527600000):

    """
    Results and dates of all self-reported PCR-tests in the 'tests & symptoms'
    AND the 'Erleben & Verhalten' study.

    Note that only one test-result per user is considered. That is either the
    first ever positive PCR-test or the first ever test if all results were
    negative.  This is to ensure consistency with how PCR-tests are surveyed in
    the 'tests & symptoms' study.

    Returns
    -------
    test_data : pd.DataFrame

    The DataFrame has three columns (user_id, test_result, test_data) and an
    integer index like so:

               user_id test_result  test_date
        0          375    negative 2021-10-11
        1          387    positive 2021-03-29
        2          494    negative 2020-04-20
        3          766    negative 2020-09-14
        4          843    negative 2020-04-06
        ...        ...         ...        ...
        13229  1225241    positive 2021-11-01
        13230  1225249    negative 2021-08-16
        13231  1225258    negative 2020-12-21
        13232  1225273    negative 2020-08-10
        13233  1225284    negative 2021-09-13

    The entry in test_date always corresponds to the beginning of a seven-day
    period during which the test was taken.
    """

    weekly_tests = weekly_pcr_tests(max_created_at=max_created_at)
    one_off_tests = one_off_pcr_tests(max_created_at=max_created_at)
    df = pd.concat([weekly_tests, one_off_tests])

    # First sort by userid and date and keep the first positive AND first
    # negative PCR tests each
    df.sort_values(by=['user_id', 'test_date'], inplace=True)
    df.drop_duplicates(subset=['user_id', 'test_result'], keep='first', inplace=True)

    # Now sort by userid and test_result. Keep only the last entry of duplicate
    # users since that corresponds to the positive result ('p' for 'positive'
    # comes after 'n' for 'negative' in the alphabet)
    df.sort_values(by=['user_id', 'test_result'], inplace=True)
    df.drop_duplicates(subset=['user_id'], keep='last', inplace=True)

    df.reset_index(inplace=True, drop=True)

    return df


def _convert_date(date):
    """
    Convert a date string to a datetime object.

    Works for german strings of the format 'MONTH YEAR', e.g., 'Mai 2020' as
    they are used in the database to indicate vaccination dates.

    Parameters:
    -----------
    date : str
        Date string (in german) of the format specified above.

    Returns:
    --------
    datetime object corresponding to the date string.
    """

    translation = {
        'Januar': 'January',
        'Februar': 'February',
        'März': 'March',
        'Mai': 'May',
        'Juni': 'June',
        'Juli': 'July',
        'Oktober': 'October',
        'Dezember': 'December'
    }

    # Sometimes nan is passed to the function. In that case simply return nan
    # back
    if isinstance(date, float):
        if np.isnan(date):
            return date

    # Split the string and translate to english
    month, year = date.split(' ')
    if month in translation.keys():
        month = translation[month]

    # Parse translated string and return datetime object
    return datetime.strptime(month + ' ' + year, '%B %Y')


def _vaccination_one_survey(questionnaire, max_created_at):
    """
    Load vaccination data from one of the two corresponding surveys.

    This helper function should not be called directly! Use vaccinations()
    instead.

    Parameters:
    -----------
    questionnaire : int
        The id of the questionnaire (either 10 or 13). 10 corresponds to the
        test & symptons survey. 13 to the vaccination update survey that was
        launched in December 2021.


    Returns:
    --------
    pandas.DataFrame of the following format (with integer index that is
    omitted here):

        user_id   status  first_dose     second_dose     third_dose
            330  booster   März 2021        Mai 2021  Dezember 2021
            457     full   Juli 2021     August 2021            NaN
            615     full  April 2021       Juni 2021            NaN
            ...      ...         ...             ...            ...
        1226668  booster    Mai 2021       Juni 2021  Dezember 2021
        1226678  booster   Juni 2021       Juli 2021  Dezember 2021
        1226696  booster    Mai 2021       Juli 2021  Dezember 2021

    If the parameter 'questionnaire' is 10 all entries in third_dose are NaN
    since that information is only surveyed in questionnaire 13.
    """

    print(f'Loading vaccination data from questionnaire {questionnaire}...')

    query = f"""
    SELECT
        answers.user_id,
        choice.text,
        answers.question,
        answers.questionnaire_session
    FROM
        datenspende.answers, datenspende.choice
    WHERE
        answers.question IN (121, 122, 130, 134, 136) AND
        answers.created_at > 1634630400000 AND
        answers.created_at < {max_created_at} AND
        answers.element = choice.element AND
        answers.questionnaire = {questionnaire}
    """

    data = run_query(query)

    # Create base data frame with the vaccination status of all users.
    # Questions 121 and 134 ask about the status. 121 is only used in
    # questionnaire 10, 134 is used in questionaire 13 and has also replaced
    # 121 in questionnaire 10 after December 2021
    df = data[data.question.isin((121, 134))].drop(columns='question')
    df.rename(columns={'text': 'status'}, inplace=True)

    # Create columns for first, second and third dose
    for question_id, label in ((122, 'first_dose'), (130, 'second_dose'), (136, 'third_dose')):
        dose_info = data[data.question == question_id].drop(columns='question')
        df = pd.merge(df, dose_info, on=['user_id', 'questionnaire_session'], how='outer')
        df.rename(columns={'text': label}, inplace=True)

    # Due to a bug on thryve's end some users can submit data multiple
    # times. Even worse, they can even respond differently accross sessions.
    # In that case we only keep each last UNIQUE response of each user
    df.sort_values(by=['user_id', 'questionnaire_session'], inplace=True)
    df.drop_duplicates(subset='user_id', keep='last', inplace=True)
    df.drop(columns='questionnaire_session', inplace=True)

    # Translate responses
    df.status.replace(
        {'Ja': 'full',
         'Nein, nur teilweise geimpft': 'partial',
         'Nein, überhaupt nicht geimpft': 'unvaccinated',
         'mit Auffrischimpfung (Booster)': 'booster',
         'vollständig erstimunisiert (zweite Dosis im Fall von Moderna, Biontech, Astra Zeneca oder erste Impfdosis im Fall von Johnson&Johnson)': 'full',
         'unvollständig erstimunisiert (nur erste Impfdosis im Fall von Moderna, Biontech, Astra Zeneca)': 'partial',
         'gar nicht geimpft': 'unvaccinated'
        }, inplace=True
    )

    # Remove implausible responses
    df = _remove_implausible_responses(df)

    return df.reset_index(drop=True)


def _remove_implausible_responses(df):
    """
    Remove implausible responses from the vaccination data.

    Implausible responses include:
        - unvaccinated users entering dates of any dose
        - partially vaccinated users entering a second or third dose
        - fully vaccinated (vollstaendig erstimmunisiert) users entering a
        third dose
        - partially vaccinated users missing a first dose
        - fully vaccinated users missing a first or second dose
        - boostered users missing any dose

    For now this also removes a small set of users that is considered boostered
    but did not receive three doses due to a previous infection or other
    reasons.

    Parameters:
    -----------
    df : pandas.DataFrame
        A dataframe of the format specified in _vaccination_one_survey()

    Returns:
    --------
    pandas.DataFrame of the same format as the input but with implausible
    responses removed.
    """

    check = [
        ('unvaccinated', 'first_dose'),
        ('unvaccinated', 'second_dose'),
        ('unvaccinated', 'third_dose'),
        ('partial', 'second_dose'),
        ('partial', 'third_dose'),
        ('full', 'third_dose'),
    ]

    for status, column in check:
        invalid = (df.status == status) & ~df[column].isna()
        if invalid.sum():
            print('Dropping', invalid.sum(), status, 'that still provide', column)
            df = df[~invalid]

    check = [
        ('partial', 'first_dose'),
        ('full', 'first_dose'),
        ('full', 'second_dose'),
        ('booster', 'first_dose'),
        ('booster', 'second_dose'),
        ('booster', 'third_dose')
    ]

    for status, column in check:
        invalid = (df.status == status) & df[column].isna()
        if invalid.sum():
            print('Dropping', invalid.sum(), status, 'with missing', column)
            df = df[~invalid]

    # Remove users where status is missing
    invalid = df.status.isna()
    if invalid.sum():
        print('Dropping', invalid.sum(), 'users with missing status.')
        df = df[~invalid]


    # TODO: Properly treat users that are considered boostered, but either
    # didn't get a second dose because of infection or because their first dose
    # with Johnson & Johnson
    invalid = (df.status == 'booster') & df.second_dose.str.contains('Ich')
    if invalid.sum():
        print('Dropping', invalid.sum(), 'users that are considered boostered despite not receiveing an official second dose.')
        df = df[~invalid]

    print(len(df), 'valid entries')

    return df


def _merged_vaccination_data(max_created_at):
    """
    Compiles merged vaccination information from questionnaire 10 and 13.

    This helper function should not be called directly! Use
    vaccinations(which='all') instead.

    Returns:
    --------
    pandas.DataFrame of the following format (with integer index that is
    omitted here):

           user_id   status    first_dose   second_dose     third_dose
               239     full    April 2021     Juni 2021            NaN
               336     full      Mai 2021     Juli 2021            NaN
               375     full      Mai 2021     Juni 2021            NaN
               401     full     Juni 2021     Juli 2021            NaN
               473     full    April 2021   August 2021            NaN
               ...      ...           ...           ...            ...
           1221451     full      Mai 2021     Juni 2021            NaN
           1221463  booster  Februar 2021  Februar 2021   Oktober 2021
           1221464     full     Juli 2021   August 2021            NaN
           1221475     full      Mai 2021     Juli 2021            NaN
           1221479  booster     Juni 2021     Juli 2021  Dezember 2021
    """
    # Load both surveys
    initial = _vaccination_one_survey(questionnaire=10, max_created_at=max_created_at)
    update = _vaccination_one_survey(questionnaire=13, max_created_at=max_created_at)

    print('Merging vaccination tables...')

    # Find users that responsed to both surveys and put all per-user
    # information in one row
    common_users = np.intersect1d(initial.user_id, update.user_id)
    overlap = pd.merge(
        initial[initial.user_id.isin(common_users)],
        update[update.user_id.isin(common_users)],
        on='user_id'
    )

    # Filter out users with inconsistent responses accross surveys. See the
    # print statements for details.
    invalid = overlap.status_x.isin(['full', 'partial']) & (overlap.first_dose_x != overlap.first_dose_y)
    print('Dropping', invalid.sum(), 'fully or partially vaccinated users with inconsistent response in first dose.')
    overlap = overlap[~invalid]

    invalid = overlap.status_x.isin(['full']) & (overlap.second_dose_x != overlap.second_dose_y)
    print('Dropping', invalid.sum(), 'fully vaccinated users with inconsistent response in second dose.')
    overlap = overlap[~invalid]

    invalid = overlap.status_x.isin(['full']) & overlap.status_y.isin(['partial', 'unvaccinated'])
    print('Dropping', invalid.sum(), 'users that went from full to partial vaccination or unvaccinated.')
    overlap = overlap[~invalid]

    invalid = overlap.status_x.isin(['partial']) & overlap.status_y.isin(['unvaccinated'])
    print('Dropping', invalid.sum(), 'users that went from partial vaccination to unvaccinated.')
    overlap = overlap[~invalid]

    # Once users are properly filtered, only keep information from survey 13
    # since that is the most recent one
    overlap.columns = overlap.columns.str.strip('_y')
    overlap.drop(columns=['status_x', 'first_dose_x', 'second_dose_x', 'third_dose_x'], inplace=True)

    # Put together unique users in questionnaire 10 and 13 as well as the
    # cleaned up overlap
    final = pd.concat([
        initial[~initial.user_id.isin(common_users)],
        update[~update.user_id.isin(common_users)],
        overlap
    ])

    return final


def vaccinations(which='all', max_created_at=1672527600000):
    """
    Get vaccination data from the ROCS database.

    Vaccination data is surveyed in two questionnaires, i.e., questionnaire 10
    (the tests & symptoms study) or questionnaire 13 (the vaccination update
    survey from December 2021).

    Allows parsing only either of the two studies or a consistently merged
    version of both.

    Parameters:
    -----------
    which : str
        Can be either of three options:
            - 'all': Load the data from both surveys (10 and 13)
            - 'initial': Loads only questionnaire 10
            - 'update': Loads only questionnaire 13

    Returns:
    --------
    pandas.DataFrame of the following format (with integer index that is
    omitted here):

       user_id   status first_dose second_dose third_dose jansen_received previously_infected
           239     full 2021-04-01  2021-06-01        NaT           False               False
           336     full 2021-05-01  2021-07-01        NaT           False               False
           375     full 2021-05-01  2021-06-01        NaT           False               False
           387     full 2021-03-01  2021-12-01        NaT           False               False
           401     full 2021-06-01  2021-07-01        NaT           False               False
           ...      ...        ...         ...        ...             ...                 ...
       1226663  booster 2021-06-01  2021-07-01 2021-12-01           False               False
       1226668  booster 2021-05-01  2021-06-01 2021-12-01           False               False
       1226678  booster 2021-06-01  2021-07-01 2021-12-01           False               False
       1226696  booster 2021-05-01  2021-07-01 2021-12-01           False               False
       1226708     full 2021-09-01         NaT        NaT            True               False

    status can be either of four options:
        - 'full', 'booster', 'unvaccinated' or 'partial'

    jansen_received indicates whether users received vaccination from Johnson &
    Johnson. In that case their status reads 'full' despite second_dose being
    NaT.

    previously_infected indicates whether users received only one dose for full
    vaccination because of 'other reasons' which we assume to mostly be
    previous infections. In that case their status reads 'full' despite
    second_dose being NaT.
    """
    if which == 'all':
        df = _merged_vaccination_data(max_created_at=max_created_at)
    elif which == 'initial':
        df = _vaccination_one_survey(10, max_created_at=max_created_at)
    elif which == 'update':
        df = _vaccination_one_survey(13, max_created_at=max_created_at)
    else:
        print("'which' must be either 'all', 'initial' or 'update'")
        return None

    # Create columns for Johnson & Johnson as well as previous infections
    df['jansen_received'] = df.second_dose.str.contains('Johnson')
    df['previously_infected'] = df.second_dose.str.contains('anderen')

    # Replace responses in second_dose with nan-values
    df.second_dose.replace(
        {
            'Ich wurde mit dem Vakzin von Johnson & Johnson geimpft und benötigte daher keine zweite Impfdosis.': np.nan,
            'Ich habe aus anderen Gründen keine zweite Dosis erhalten': np.nan
        },
        inplace=True
    )

    # Convert datestrings to datetime
    df.first_dose = df.first_dose.apply(_convert_date)
    df.second_dose = df.second_dose.apply(_convert_date)
    df.third_dose = df.third_dose.apply(_convert_date)

    # Remove users where the order of doses is incorrect
    for col1, col2 in (('first_dose', 'second_dose'), ('first_dose', 'third_dose'), ('second_dose', 'third_dose')):
        invalid = ~df[col1].isna() & ~df[col2].isna() & (df[col1] > df[col2])
        print('Dropping', invalid.sum(), 'users where', col1, 'is larger than', col2)
        df = df[~invalid]

    # Sort for better readibility
    df.sort_values(by='user_id', inplace=True)

    return df.reset_index(drop=True)
