import openai
import os
import pandas as pd
import re

client = openai.OpenAI(
    organization=os.environ.get("KIMLAB_OAI_ID"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="http://oai.hconeai.com/v1",
    default_headers={
        "Helicone-Auth": f"Bearer {os.environ.get('HELICONE_API_KEY')}",
        "Helicone-Cache-Enabled": "true",
    },
)


def query_llm(llm_prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant that provides evidence-based responses to pharmacogenomics questions. Please respond to the following query, or just say “IDK” if you do not know the answer to something."},
            {"role": "user", "content": llm_prompt}
        ]
    )
    return response.choices[0].message.content

def score_response(llm_answer, ref_answer):
    precision = 0
    recall = 0

    llm_list = list(set(re.findall(r'rs[0-9]+', llm_answer)))
    ref_list = list(set(ref_answer.split(";")))
    
    for rsid in llm_list:
        if rsid in ref_list:
            precision += 1
    precision = precision / len(llm_list) if len(llm_list) > 0 else 0

    for rsid in ref_list:
        if rsid in llm_list:
            recall += 1
    recall = recall / len(ref_list)
    
    return precision, recall

allele_definitions = pd.read_csv("../../test_queries/allele_def_queries.txt", sep="\t", header=0)
allele_definitions = allele_definitions.sample(150)

allele_definitions["llm_answer"] = allele_definitions["question"].apply(query_llm)

allele_definitions[["precision","recall"]] = allele_definitions.apply(lambda x: score_response(llm_answer=x["llm_answer"], ref_answer=x["answer"]), axis=1, result_type="expand")
allele_definitions.to_csv("allele_definition_score_test.txt", sep="\t", index=False)

print(f"Mean precision: {allele_definitions['precision'].mean()}")
print(f"Mean recall: {allele_definitions['recall'].mean()}")