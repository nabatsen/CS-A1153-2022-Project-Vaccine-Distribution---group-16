from sqlalchemy import create_engine
import pandas as pd


def main():
    try:
        DIALECT = "postgresql+psycopg2://"
        database = "grp16_vaccinedist"
        user = "grp16"
        host = "dbcourse2022.cs.aalto.fi"
        password = input("Enter password:")
        uri = "%s:%s@%s/%s".format(user, password, host, database)
        engine = create_engine(DIALECT + uri)
        conn = engine.connect()

    except Exception as e:
        print(e)

    main()
