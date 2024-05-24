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

query = """select * from cpic.pair_view p where cpiclevel='A';"""

cursor.execute(query)
colnames = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()
conn.close()

df = pd.DataFrame(rows, columns=colnames)
drug_to_genes = {}
for idx, row in df.iterrows():
    drug = row["drugname"]
    gene = row["genesymbol"]
    if drug not in drug_to_genes:
        drug_to_genes[drug] = set()
    drug_to_genes[drug].add(gene)

for drug in drug_to_genes:
    drug_to_genes[drug] = ";".join(list(drug_to_genes[drug]))

df = pd.DataFrame.from_dict({
    "drug": [drug for drug in sorted(drug_to_genes.keys())],
    "genes": [drug_to_genes[drug] for drug in sorted(drug_to_genes.keys())]
                             })

df2 = copy.deepcopy(df)
df["mode"] = ["clinician"]*len(df)
df2["mode"] = ["researcher"]*len(df2)

df = pd.concat([df,df2], ignore_index=True)

def generate_question(row):
    mode=row["mode"]
    drug=row["drug"]
    if mode == "clinician":
        question = f"I want to give my patient {drug}. What genes should I include in a pharmacogenetics panel?"
    else:
        question = f"What genes have actionable pharmacogenetic guidelines for {drug}?"
    
    question += " Please respond with nothing but a list of gene symbols delimited by ';'."
    return question

df["question"] = df.apply(generate_question, axis=1)
df["answer"] = df["genes"]

df = df.drop_duplicates(subset=["drug", "genes", "mode"])

df = df[["drug", "genes", "mode", "question", "answer"]]
df.to_csv("../../test_queries/drug_to_genes_queries.txt", index=False, sep="\t")