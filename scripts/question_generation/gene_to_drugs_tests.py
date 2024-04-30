import psycopg2
import json
import pandas as pd
import sys
import copy


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
SELECT dr.name,rec.implications from cpic.drug dr 
join cpic.recommendation rec on dr.guidelineid = rec.guidelineid;
"""

cursor.execute(query)
colnames = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()
conn.close()

df = pd.DataFrame(rows, columns=colnames)
gene_to_drugs = {}
for idx, row in df.iterrows():
    drug = row["name"]
    genes = row["implications"].keys()
    for gene in genes:
        if gene not in gene_to_drugs:
            gene_to_drugs[gene] = set()
        gene_to_drugs[gene].add(drug)

for gene in gene_to_drugs:
    gene_to_drugs[gene] = ";".join(list(gene_to_drugs[gene]))

df = pd.DataFrame.from_dict({
    "gene": [gene for gene in sorted(gene_to_drugs.keys())],
    "drugs": [gene_to_drugs[gene] for gene in sorted(gene_to_drugs.keys())]
                             })


def generate_question(row):
    gene=row["gene"]
    question = f"Which drugs have actionable CPIC guidelines for {gene}?"
    question += " Please respond with nothing but a list of generic drug names delimited by ';'."
    return question

df["question"] = df.apply(generate_question, axis=1)
df["answer"] = df["drugs"]

df = df[["gene", "drugs", "question", "answer"]]
df.to_csv("../../test_queries/gene_to_drugs_queries.txt", index=False, sep="\t")