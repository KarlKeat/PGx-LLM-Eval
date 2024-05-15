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

with open("rec_to_category.txt",'r') as infile:
    rec_to_category = dict([(line.split("\t")[0], line.split("\t")[1].strip()) for line in infile.readlines()])

df["actionable_indication"] = df.apply(get_actionable, axis=1)
df["guideline"] = df.apply(assemble_guideline, axis=1)
df["genes"] = df["actionable_indication"].apply(lambda x: ";".join(x.keys()))
df["question"] = df.apply(generate_question, axis=1)
df["answer"] = df["drugrecommendation"].apply(lambda x: x.replace("\n", "").replace("\"", ""))
df["answer_category"] = df["drugrecommendation"].apply(lambda x: rec_to_category[x.replace("\n", "").replace("\"", "")])
df["drug"] = df["name"]

incorrect_recommendations = {}
concurring_recommendation = {}
for idx, row in df.iterrows():
    drug = row["drug"]
    if drug not in incorrect_recommendations:
        incorrect_recommendations[drug] = {}
        concurring_recommendation[drug] = {}
    answer_category = row["answer_category"]
    if answer_category not in incorrect_recommendations[drug]:
        #drug_subset = df[df["drug"] == drug]
        #answer_subset = drug_subset[drug_subset["answer_category"] != answer_category]
        #incorrect_recommendations[drug][answer_category] = list(set(answer_subset["answer"]))
        incorrect_recommendations[drug][answer_category] = []
        
        if answer_category == "Avoid":
            incorrect_recommendations[drug][answer_category].append(f"Proceed taking {drug} as normal. There is no recommendation.")
            incorrect_recommendations[drug][answer_category].append(f"Take {drug} with a reduced dose.")
            incorrect_recommendations[drug][answer_category].append(f"Take {drug} with an increased dose.")
            concurring_recommendation[drug][answer_category] = f"Avoid {drug}. Take an alternate therapy."
        elif answer_category == "Alter dose":
            incorrect_recommendations[drug][answer_category].append(f"Proceed taking {drug} as normal. There is no recommendation.")
            incorrect_recommendations[drug][answer_category].append(f"Avoid {drug}. Take an alternate therapy.")
            concurring_recommendation[drug][answer_category] = f"Take {drug} with an altered dose."
        elif answer_category == "Unchanged":
            incorrect_recommendations[drug][answer_category].append(f"Avoid {drug}. Take an alternate therapy.")
            incorrect_recommendations[drug][answer_category].append(f"Take {drug} with a reduced dose.")
            incorrect_recommendations[drug][answer_category].append(f"Take {drug} with an increased dose.")
            concurring_recommendation[drug][answer_category] = f"Proceed taking {drug} as normal. There is no recommendation."


df["incorrect_recommendations"] = df.apply(lambda x: "|".join(incorrect_recommendations[x["drug"]][x["answer_category"]]), axis=1)
df["concurring_recommendation"] = df.apply(lambda x: concurring_recommendation[x["drug"]][x["answer_category"]], axis=1)

df = df[["drug", "genes", "question", "answer", "incorrect_recommendations", "concurring_recommendation"]]
df.to_csv("../../test_queries/drug_guidelines_for_pheno_queries.txt", index=False, sep="\t")