import pandas as pd
import shutil

RANDOM_SEED=42

# Allele Definition
df = pd.read_csv("../test_queries/allele_def_queries.txt", sep="\t", header=0)
gene_options = set(df["gene"])
subsets = []
for gene in sorted(list(gene_options)):
    subset = df[df["gene"] == gene]
    sample_size = 5
    if sample_size > len(subset):
        sample_size = len(subset)
    subset = subset.sample(n=sample_size, random_state=RANDOM_SEED)
    subsets.append(subset)

df = pd.concat(subsets)
df.to_csv("../test_queries/subsets/allele_def_subset.txt", index=False, sep="\t")

# Allele Frequency
df = pd.read_csv("../test_queries/allele_freq_queries.txt", sep="\t", header=0)
gene_options = set(df["gene"])
pop_group_options = set(df["pop_group"])
subsets = []
for gene in sorted(list(gene_options)):
    for pop_group in pop_group_options:
        subset = df[df.apply(lambda x: x["gene"] == gene and x["pop_group"] == pop_group, axis=1)]
        sample_size = 5
        if sample_size > len(subset):
            sample_size = len(subset)
        subset = subset.sample(n=sample_size, random_state=RANDOM_SEED)
        subsets.append(subset)

df = pd.concat(subsets)
df.to_csv("../test_queries/subsets/allele_freq_subset.txt", index=False, sep="\t")

# Allele Function
df = pd.read_csv("../test_queries/allele_function_queries.txt", sep="\t", header=0)
gene_options = set(df["gene"])
subsets = []
for gene in sorted(list(gene_options)):
    gene_subset = df[df["gene"] == gene]
    phenotypes = set(gene_subset["answer"])
    for phenotype in phenotypes:
        subset = gene_subset[gene_subset["answer"] == phenotype]
        sample_size = 3
        if sample_size > len(subset):
            sample_size = len(subset)
        subset = subset.sample(n=sample_size, random_state=RANDOM_SEED)
        subsets.append(subset)

df = pd.concat(subsets)
df.to_csv("../test_queries/subsets/allele_function_subset.txt", index=False, sep="\t")

# Diplotype to Phenotype
df = pd.read_csv("../test_queries/diplotype_to_phenotype_queries.txt", sep="\t", header=0)
gene_options = set(df["gene"])
subsets = []
for gene in sorted(list(gene_options)):
    gene_subset = df[df["gene"] == gene]
    phenotypes = set(gene_subset["answer"])
    for phenotype in phenotypes:
        subset = gene_subset[gene_subset["answer"] == phenotype]
        sample_size = 3
        if sample_size > len(subset):
            sample_size = len(subset)
        subset = subset.sample(n=sample_size, random_state=RANDOM_SEED)
        subsets.append(subset)

df = pd.concat(subsets)
df.to_csv("../test_queries/subsets/diplotype_to_phenotype_subset.txt", index=False, sep="\t")

# Drug to PGx Genes
df = pd.read_csv("../test_queries/drug_to_genes_queries.txt", sep="\t", header=0)
drug_options = set(df["drug"])
subsets = []
for drug in sorted(list(drug_options)):
    drug_subset = df[df["drug"] == drug]
    query_classes = ["clinician", "researcher"]
    for mode in query_classes:
        subset = drug_subset[drug_subset["mode"] == mode]
        sample_size = 3
        if sample_size > len(subset):
            sample_size = len(subset)
        subset = subset.sample(n=sample_size, random_state=RANDOM_SEED)
        subsets.append(subset)

df = pd.concat(subsets)
df.to_csv("../test_queries/subsets/drug_to_genes_subset.txt", index=False, sep="\t")

# PGx Gene to Drugs (keep all)
shutil.copyfile("../test_queries/gene_to_drugs_queries.txt", "../test_queries/subsets/gene_to_drugs_subset.txt")

# Recommmendation category 
df = pd.read_csv("../test_queries/recommendation_category_for_pheno_queries.txt", sep="\t", header=0, keep_default_na=False)
drug_options = set(df["drug"])
subsets = []
for drug in sorted(list(drug_options)):
    drug_subset = df[df["drug"] == drug]
    phenotypes = set(drug_subset["answer"])
    for phenotype in phenotypes:
        subset = drug_subset[drug_subset["answer"] == phenotype]
        sample_size = 3
        if sample_size > len(subset):
            sample_size = len(subset)
        subset = subset.sample(n=sample_size, random_state=RANDOM_SEED)
        subsets.append(subset)

df = pd.concat(subsets)
df.to_csv("../test_queries/subsets/recommendation_category_for_pheno_subset.txt", index=False, sep="\t")

# Pheno to guideline 
df = pd.read_csv("../test_queries/drug_guidelines_for_pheno_queries.txt", sep="\t", header=0, keep_default_na=False)

drug_options = set(df["drug"])
subsets = []
for drug in sorted(list(drug_options)):
    subset = df[df["drug"] == drug]
    sample_size = 4
    if sample_size > len(subset):
        sample_size = len(subset)
    subset = subset.sample(n=sample_size, random_state=RANDOM_SEED)
    subsets.append(subset)

df = pd.concat(subsets)
df.to_csv("../test_queries/subsets/drug_guidelines_for_pheno_subset.txt", index=False, sep="\t")