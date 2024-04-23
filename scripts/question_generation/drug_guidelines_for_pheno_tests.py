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
SELECT dr.name,rec.implications,rec.drugrecommendation,rec.phenotypes,rec.activityscore, rec.allelestatus
from cpic.recommendation rec 
join cpic.drug dr on rec.drugid = dr.drugid;
"""

cursor.execute(query)
colnames = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()
conn.close()

df = pd.DataFrame(rows, columns=colnames)

def get_actionable(row):
    if len(row["allelestatus"]) > 0:
        return row["allelestatus"]
    elif len(row["activityscore"]) > 0:
        new_rec = copy.deepcopy(row["phenotypes"])
        for gene in row["activityscore"]:
            if row['activityscore'][gene] != 'n/a':
                new_rec[gene] = f"{new_rec[gene]} and activity score = {row['activityscore'][gene]}"
        return new_rec
    else:
        return row["phenotypes"]
    
def assemble_guideline(row):
    implications = row["implications"]
    implications_str = " ".join([implications[gene] for gene in implications])

    return f"{implications_str} {row['drugrecommendation']}"

def generate_question(row):
    drug = row["name"]
    phenos = row["actionable_indication"]
    pheno_string = " and ".join([f"{phenos[gene]} for {gene}" for gene in phenos])
    return f"What would be the clinical guidance for someone who is {pheno_string} with regards to taking {drug}?"

df["actionable_indication"] = df.apply(get_actionable, axis=1)
df["guideline"] = df.apply(assemble_guideline, axis=1)
df["genes"] = df["actionable_indication"].apply(lambda x: ";".join(x.keys()))
df["question"] = df.apply(generate_question, axis=1)
df["answer"] = df["drugrecommendation"]
df["drug"] = df["name"]
df = df[["drug", "genes", "question", "answer"]]
df.to_csv("../../test_queries/drug_guidelines_for_pheno_queries.txt", index=False, sep="\t")