import psycopg2
import json


conn = None
try:
    conn = psycopg2.connect(
        dbname='cpic_db',
        host='localhost',
    )
except:
    print("I am unable to connect to the database")


# Get a cursor and execute select statement
cursor = conn.cursor()

cursor.execute("""SELECT * from cpic.gene where symbol='CYP2C19'""")
rows = cursor.fetchall()

# Print out the results
for row in rows:
    print(row)

# Close the connection when finished
conn.close()
