from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd
import numpy as np


def connector():
    
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
    
    conn = connector()
    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def tuple_of_user_ids(user_ids):
    
    if isinstance(user_ids, int) or isinstance(user_ids, np.int64):
        formatter = f'({user_ids})'
    elif len(user_ids) == 1:
        formatter = f'({user_ids[0]})'
    else:
        formatter = tuple(user_ids)
    
    return formatter


def get_vitals(user_ids, max_date="2022-04-03"):
    
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

    user_ids = tuple_of_user_ids(user_ids)

    query = """SELECT * FROM datenspende.users WHERE user_id IN {0}""".format(user_ids)
    
    users = run_query(query)
    users.salutation = users.salutation.fillna(30.0)

    return users
