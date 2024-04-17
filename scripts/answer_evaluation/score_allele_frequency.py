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
    llm_freq = round(float(re.search(r'[0-9]\.[0-9]{4}', llm_answer).group(0)), 4) if llm_answer is not None and "IDK" not in llm_answer else 0.2500
    
    return abs(ref_answer - llm_freq)

allele_definitions = pd.read_csv("../../test_queries/allele_freq_queries.txt", sep="\t", header=0)
allele_definitions = allele_definitions.sample(10)

allele_definitions["llm_answer"] = allele_definitions["question"].apply(query_llm)

allele_definitions["score"] = allele_definitions.apply(lambda x: score_response(llm_answer=x["llm_answer"], ref_answer=x["answer"]), axis=1)
allele_definitions.to_csv("allele_frequency_score_test.txt", sep="\t", index=False)

print(f"Mean absolute deviationn: {allele_definitions['score'].mean()}")