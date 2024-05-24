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

cursor.execute("""select * from cpic.pair_view p where cpiclevel='A';""")
rows = cursor.fetchall()

colnames = [desc[0] for desc in cursor.description]

# Print out the results
print(colnames)
for row in rows:
    print(row)

# Close the connection when finished
conn.close()
