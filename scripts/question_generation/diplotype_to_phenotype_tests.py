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
SELECT * from cpic.diplotype;
"""

cursor.execute(query)
colnames = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

gene_dict = {}
allele_dict = {}
for row in rows:
    gene = row[0]
    diplotype = row[1]
    phenotype = row[9]
    if gene not in gene_dict:
        gene_dict[gene] = set()
    gene_dict[gene].add(phenotype)

    allele_key = f"{gene}\t{diplotype}"
    allele_dict[allele_key] = phenotype

# Print out the results
answer_str = ["gene\tallele\tquestion\tanswer"]
for key in allele_dict:
    gene_allele = key.replace('\t', ' ')
    answer_choices = gene_dict[key.split('\t')[0]]
    question = f"What is the pharmacogenetic phenotype for {gene_allele}? Please select the answer from the following choices: {answer_choices}, and respond with only your selection."
    answer = allele_dict[key]
    answer_str.append(f"{key}\t{question}\t{answer}")

with open("../../test_queries/diplotype_to_phenotype_queries.txt", "w") as outfile:
    outfile.write("\n".join(answer_str))

# Close the connection when finished
conn.close()