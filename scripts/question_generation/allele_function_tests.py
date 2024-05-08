import psycopg2
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

query = """
SELECT * from cpic.allele;
"""

cursor.execute(query)
colnames = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

df = pd.DataFrame(rows, columns=colnames)
conn.close()

df["gene"] = df["genesymbol"]
df["allele"] = df["name"]
df["answer"] = df["clinicalfunctionalstatus"]
df = df.dropna(subset=["answer"],axis=0)

answer_options = {}
for idx, row in df.iterrows():
    gene = row["gene"]
    func = row["answer"]
    if gene not in answer_options:
        answer_options[gene] = set()
    answer_options[gene].add(func)

df["choices"] = df["gene"].apply(lambda x: answer_options[x])

def generate_question(row):
    gene = row["gene"]
    allele = row["allele"]
    options = row["choices"]

    query_str = f"What is the allele functionality of {gene} {allele}? Please select the answer from the following choices: {options}, and respond with only your selection."
    return query_str

df["question"] = df.apply(generate_question, axis=1)

df = df[["gene", "allele", "question", "answer"]]
df.to_csv("../../test_queries/allele_function_queries.txt", index=False, sep="\t")