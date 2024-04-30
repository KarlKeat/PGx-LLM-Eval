import openai
import os
import pandas as pd
import re

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

allele_definitions = pd.read_csv("../../test_queries/recommendation_category_for_pheno_queries.txt", sep="\t", header=0)
allele_definitions = allele_definitions.sample(50)

allele_definitions["llm_answer"] = allele_definitions["question"].apply(query_llm)
allele_definitions["score"] = allele_definitions.apply(lambda x: x["answer"] == x["llm_answer"], axis = 1)

allele_definitions.to_csv("rec_to_category_score_test.txt", sep="\t", index=False)

print(f"Accuracy: {allele_definitions['score'].mean()}")