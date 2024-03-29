from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd
import numpy as np


def connector():
    """
    Establish connection to the ROCS data base.

    Requires that all environment variables are set in .env in the root of this repository.

    Returns:
        connection: The data base connector.
    """
    load_dotenv()
    
    conn = psycopg2.connect(**{
        "database": os.getenv("DBNAME"),
        "user": os.getenv("DBUSER"),
        "port": os.getenv("PORT"),
        "host": os.getenv("HOST"),
        "password": os.getenv("PASSWORD")
        }
    )
    
    return conn


def run_query(query):
    """
    Run an SQL query against the ROCS postgres database.

    Args:
        query (str): the SQL query to execute.

    Returns:
        pandas.DataFrame: The query results.
    """
    conn = connector()
    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def tuple_of_user_ids(user_ids):
    """
    Converts a given user id or list of user id's to a format that can be
    inserted into IN statements of an SQL query.

    Ensures that the IN-condition for SQL queries either takes the form
    '(userid)' in the case of a single requested user id or '(userid1, userid2,
    ..., useridN)' in the case of multiple requested user ids.

    Args:
        user_ids (int, list, or array): User ids that are inserted into the SQL
        queries.

    Returns:
        tuple or string: Tuple containing all user ids.
    """
    if isinstance(user_ids, int) or isinstance(user_ids, np.int64):
        formatter = f'({user_ids})'
    elif len(user_ids) == 1:
        formatter = f'({user_ids[0]})'
    else:
        formatter = tuple(user_ids)
    
    return formatter


def get_vitals(user_ids, max_date="2022-04-03"):
    """
    Get vital data from the data base. 

    Loads data for sleep duration, resting heart rate and step count up to a given date.

    Args:
        user_ids (int or list/array of int): User ids for which to retrieve the vital data.
        max_date (str, optional): The maximum allowed data of vital data. Defaults to "2022-04-03".

    Returns:
        pandas.DataFrame: The vital data.
    """    
    user_ids = tuple_of_user_ids(user_ids)

    query = f"""
    SELECT 
        user_id AS userid, date, type AS vitalid, value, source AS deviceid
    FROM 
        datenspende.vitaldata
    WHERE 
        vitaldata.user_id IN {user_ids}
    AND
        vitaldata.type IN (9, 65, 43)
    AND
        vitaldata.date <= '{max_date}'
    """

    vitals = run_query(query)
    vitals.date = pd.to_datetime(vitals.date)    

    return vitals


def get_user_data(user_ids):
    """
    Get user data from the data base.

    Args:
        user_ids (int or list/array of int): User ids for which to retrieve the vital data.

    Returns:
        _pandas.DataFrame: The user data data.
    """    
    user_ids = tuple_of_user_ids(user_ids)

    query = """SELECT * FROM datenspende.users WHERE user_id IN {0}""".format(user_ids)
    
    users = run_query(query)
    users.salutation = users.salutation.fillna(30.0)

    return users


def get_all_valid_datenspende_user():
    
    query = """SELECT DISTINCT user_id FROM datenspende.vitaldata"""
    unique_users_vitals = run_query(query)

    query = """SELECT * FROM datenspende.users WHERE user_id IN {0}""".format(tuple(unique_users_vitals.user_id.values))
    all_user = run_query(query)
    
    all_user = all_user.drop(columns=['source', 'creation_timestamp', 'height', 'weight', 'plz']).dropna()
    all_user['age'] = np.floor((2022 + 4 / 12) - all_user['birth_date'] + 2.5)
    
    all_user.reset_index(inplace=True, drop=True)
    
    return all_user