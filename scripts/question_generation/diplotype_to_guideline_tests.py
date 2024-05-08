import psycopg2
import pandas as pd
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
SELECT * from cpic.diplotype;
"""

cursor.execute(query)
colnames = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

gene_phenotypes = {}
diplotype_to_phenotype = {}
for row in rows:
    gene = row[0]
    diplotype = row[1]
    phenotype = row[9]
    if gene not in gene_phenotypes:
        gene_phenotypes[gene] = set()
    gene_phenotypes[gene].add(phenotype)

    allele_key = f"{gene}\t{diplotype}"
    diplotype_to_phenotype[allele_key] = phenotype

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
    return f"What would be the clinical guidance for someone who is {pheno_string} with regards to taking {drug}? Please respond with just 'Avoid' if the guidance is to avoid the drug or take an alternate drug, 'Alter dose' if the guideline is to raise, lower, or start with a specific dose, or 'Unchanged', if there are no clinical recommendations or there is no deviation from standard care for this phenotype and drug."

with open("rec_to_category.txt",'r') as infile:
    rec_to_category = dict([(line.split("\t")[0], line.split("\t")[1].strip()) for line in infile.readlines()])

df["actionable_indication"] = df.apply(get_actionable, axis=1)
df["guideline"] = df.apply(assemble_guideline, axis=1)
df["genes"] = df["actionable_indication"].apply(lambda x: ";".join(x.keys()))
df["question"] = df.apply(generate_question, axis=1)
df["answer"] = df["drugrecommendation"].apply(lambda x: rec_to_category[x.replace("\n", "").replace("\"", "")])
df["drug"] = df["name"]

for allele_key in diplotype_to_phenotype:
    gene = allele_key.split("\t")[0]
    diplotype = allele_key.split("\t")[0]
    phenotype = diplotype_to_phenotype["allele_key"]
    