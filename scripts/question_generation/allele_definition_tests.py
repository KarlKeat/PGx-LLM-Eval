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

query = """
select d.genesymbol, d.name, sl.dbsnpid 
from cpic.allele_definition d 
join cpic.allele_location_value alv on d.id = alv.alleledefinitionid 
join cpic.sequence_location sl on alv.locationid = sl.id  
"""

cursor.execute(query)
colnames = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

allele_dict = {}
for row in rows:
    allele_key = f"{row[0]}\t{row[1]}"
    if allele_key not in allele_dict:
        allele_dict[allele_key] = []
    allele_dict[allele_key].append(row[2])

# Print out the results
print("gene\tallele\tquestion\tanswer")
for key in allele_dict:
    if None not in allele_dict[key]:
        gene_allele = key.replace('\t', ' ')
        question = f"What SNPs are in the allele definition for {gene_allele}? Provide a dbSNP ID (also known as an rsID, starting with rs) when available."
        answer = ";".join(list(set(allele_dict[key])))
        print(f"{key}\t{question}\t{answer}")

# Close the connection when finished
conn.close()