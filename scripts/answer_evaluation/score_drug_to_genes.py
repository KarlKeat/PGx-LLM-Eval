import openai
import os
import pandas as pd
import sys

gpt_client = openai.OpenAI(
    organization=os.environ.get("KIMLAB_OAI_ID"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="http://oai.hconeai.com/v1",
    default_headers={
        "Helicone-Auth": f"Bearer {os.environ.get('HELICONE_API_KEY')}",
        "Helicone-Cache-Enabled": "true",
    },
)

llama_client = openai.OpenAI(
    api_key='EMPTY',
    base_url="http://localhost:8000/v1",
)

def query_llm(llm_prompt, model="gpt-3.5-turbo"):
    if "llama" in model:
        client = llama_client
    elif "gpt" in model:
        client = gpt_client
    else:
        raise ValueError(f"Unsupported model: {model}")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an AI assistant that provides evidence-based responses to pharmacogenomics questions. Please respond to the following query."},
            {"role": "user", "content": llm_prompt}
        ]
    )
    return response.choices[0].message.content.replace("\n","  ")

def extract_genes(llm_answer):
    return [x.strip() for x in llm_answer.split(";")]

def score_response(llm_genes, ref_answer):
    precision = 0
    recall = 0

    ref_list = list(set(ref_answer.split(";")))
    
    for gene in llm_genes:
        if gene in ref_list:
            precision += 1
    precision = precision / len(llm_genes) if len(llm_genes) > 0 else 0

    for gene in ref_list:
        if gene in llm_genes:
            recall += 1
    recall = recall / len(ref_list)
    
    return precision, recall

allele_definitions = pd.read_csv("../../test_queries/drug_to_genes_queries.txt", sep="\t", header=0)
allele_definitions = allele_definitions.sample(20)

allele_definitions["llm_answer"] = allele_definitions["question"].apply(query_llm)
allele_definitions["llm_genes"] = allele_definitions["llm_answer"].apply(extract_genes)


allele_definitions[["precision","recall"]] = allele_definitions.apply(lambda x: score_response(llm_genes=x["llm_genes"], ref_answer=x["answer"]), axis=1, result_type="expand")
allele_definitions.to_csv("drug_to_genes_score_test.txt", sep="\t", index=False)

print(f"Mean precision: {allele_definitions['precision'].mean()}")
print(f"Mean recall: {allele_definitions['recall'].mean()}")