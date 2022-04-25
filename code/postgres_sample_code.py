import psycopg2

conn = None
cur = None

try:
    conn = psycopg2.connect(
        host="dbcourse2022.cs.aalto.fi",
        dbname="test_db",
        user="test_user",
        password="password",
        port="5432",
    )

    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS employee")
    create_script = """ CREATE TABLE IF NOT EXISTS employee (
                            id      int PRIMARY KEY,
                            name    varchar(40) NOT NULL,
                            salary  int,
                            dept_id varchar(30)); """

    cur.execute(create_script)

    insert_script = (
        "INSERT INTO employee (id , name, salary, dept_id) VALUES (%s, %s, %s, %s)"
    )
    insert_value = (1, "James", 12000, "D1")

    cur.execute(insert_script, insert_value)
    conn.commit()

except Exception as error:
    print(error)
finally:
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()
