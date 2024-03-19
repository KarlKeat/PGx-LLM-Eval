import psycopg2
import json
import pandas as pd


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


cursor.execute("""SELECT * from cpic.population_frequency_view""")
rows = cursor.fetchall()

# Print out the results
colnames = [desc[0] for desc in cursor.description]
freq_df = pd.DataFrame(rows, columns=colnames)

# Close the connection when finished
conn.close()

with open("../test_queries/allele_freq_queries.txt", 'w') as outfile:
    lines = []
    for idx, row in freq_df.iterrows():
        gene = row["genesymbol"]
        variant = row["name"]
        pop_group = row["population_group"]
        frequency = round(row["freq_weighted_avg"],4)
        lines.append(f"\"What is the allele frequency of {gene} {variant} in the {pop_group} population? Respond with just a number, rounded to 4 decimal places, with no additional text.\",{frequency}\n")
    outfile.writelines(lines)