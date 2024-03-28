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

cursor.execute("""select d.*, sl.*, alv.variantallele
from cpic.allele_definition d
join cpic.allele_location_value alv on d.id = alv.alleledefinitionid
join cpic.sequence_location sl on alv.locationid = sl.id""")
colnames = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

# Print out the results
print(colnames)
for row in rows:
    print(row)

# Close the connection when finished
conn.close()
