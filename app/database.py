import sqlite3
from os.path import exists
from os import environ
from sqlite3 import Error
import pathlib
from dotenv import load_dotenv

load_dotenv()


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file, timeout=1)
        return conn
    except Error as e:
        print(e)
        exit()

    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def db_conn():
    database = str(pathlib.Path(__file__).parent.resolve()) + "/../database/data/" + environ["DB_NAME"] + ".sqlite"

    db_file_exists = exists(database)
    # create a database connection
    conn = create_connection(database)

    if db_file_exists is False:
        db_init_tables(conn)

    return conn


def db_init_tables(conn):

    sql_create_items_table = """ CREATE TABLE IF NOT EXISTS  "jobs" (
                                    "id"	INTEGER NOT NULL,
                                    "status"	TEXT NOT NULL,
                                    "type"	TEXT NOT NULL,
                                    "size"	INTEGER,
                                    "created_at"	datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                    PRIMARY KEY("id" AUTOINCREMENT)
                                ); """

    sql_create_jobs_table = """CREATE TABLE IF NOT EXISTS  "items" (
                                    "id"	INTEGER NOT NULL,
                                    "job_id"	INTEGER NOT NULL,
                                    "request_id"	INTEGER NOT NULL,
                                    "status"	INTEGER,
                                    "created_at"	datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                    PRIMARY KEY("id" AUTOINCREMENT)
                                );"""
    # create tables
    if conn is not None:
        # create jobs table
        create_table(conn, sql_create_jobs_table)

        # create tasks table
        create_table(conn, sql_create_items_table)

        # commit the changes to db
        conn.commit()
    else:
        print("Error! cannot create the database connection.")


def create_job(conn, job):
    """
    Create a new jobs into the jobs table
    :param conn:
    :param job:
    :return: job id
    """
    task = (job['status'], job['type'], job['size'])

    sql = ''' INSERT INTO jobs(status, type, size)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_job_status(conn, job):
    """
    Update job status
    :param conn:
    :param job:
    :return job id
    """
    task = (job['status'], job['id'])
    sql = ''' UPDATE jobs SET status = ? WHERE id = ? '''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()
    conn.close()
    return cur.lastrowid


def get_job(conn, job):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :param job: job details
    :return:
    """
    sql = ''' SELECT * FROM jobs WHERE id = ? '''
    task = [job["id"]]
    cur = conn.cursor()
    cur.execute(sql, task)
    rows = cur.fetchone()
    conn.close()
    return rows


def get_job_items(conn, job):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :param job: job details
    :return:
    """
    sql = """
        select *
        from items
        where
            (?1 is null or job_id = ?1)
            and
            (?2 is null or status = ?2 )
            and
            (?3 is null or status <> ?3 )
    """

    parameters = [job['id'],
                  None if 'response_code' not in job else job['response_code'],
                  None if 'non_response_code' not in job else job['non_response_code']
                  ]

    cur = conn.cursor()
    cur.execute(sql, parameters)
    rows = cur.fetchall()
    conn.close()

    return rows


def get_unfinished_jobs(conn, variables):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :param variables:
    :return:
    """

    params = [variables['type']]
    sql = ''' SELECT id, status, size FROM jobs WHERE status IN ('new', 'running', 'paused') AND type = ? '''
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchone()
    conn.close()
    return rows


def create_items(conn, job):
    """
    Create a new items into the items table
    :param conn:
    :param job:
    :return: job id
    """

    rows = (job['job_id'], job['page'], job['status'])
    sql = ''' INSERT INTO items(job_id, request_id, status)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, rows)
    conn.commit()
    conn.close()
    return cur.lastrowid


def clean_failed_items(conn, variables):
    """
    Create a new items into the items table
    :param conn:
    :param variables:
    :return: job id
    """

    rows = [variables['id']]
    sql = ''' DELETE FROM items WHERE job_id = ? AND status <> 200 '''
    cur = conn.cursor()
    cur.execute(sql, rows)
    conn.commit()
    conn.close()
    return cur.lastrowid
