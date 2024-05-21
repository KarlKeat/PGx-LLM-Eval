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

def generate_question(row):
    mode=row["mode"]
    drug=row["drug"]
    if mode == "clinician":
        question = f"I want to give my patient {drug}. What genes should I include in a pharmacogenetics panel?"
    else:
        question = f"What genes have actionable pharmacogenetic guidelines for {drug}?"
    
    question += " Please respond with nothing but a list of gene symbols delimited by ';'."
    return question

    
df["drug"] = df["name"]
df["genes"] = df["implications"].apply(lambda x: ";".join(x.keys()))

df2 = copy.deepcopy(df)
df["mode"] = ["clinician"]*len(df)
df2["mode"] = ["researcher"]*len(df2)

df = pd.concat([df,df2], ignore_index=True)

df["question"] = df.apply(generate_question, axis=1)
df["answer"] = df["genes"]

df = df.drop_duplicates(subset=["drug", "genes", "mode"])

df = df[["drug", "genes", "mode", "question", "answer"]]
df.to_csv("../../test_queries/drug_to_genes_queries.txt", index=False, sep="\t")