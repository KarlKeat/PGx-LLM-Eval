import pandas as pd

druglist = [drug.strip() for drug in open("avoid_list.txt", "r").readlines()]
df = pd.DataFrame(druglist, columns=["drug"])


def generate_question(drug):
    query_str = f"If my patient cannot take {drug} due to their pharmacogenetics, what are all of the alternative drugs they can take? Please respond with nothing but drug names, separated by only ';'. For example: Aspirin;Ibuprofen. No additional text is needed"
    return query_str

df["question"] = df["drug"].apply(generate_question)

import openai
import os

SYSTEM_PROMPT = "You are an AI assistant that provides evidence-based responses to pharmacogenomics questions. Please respond to the following query."

gpt_client = openai.OpenAI(
    organization=os.environ.get("KIMLAB_OAI_ID"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="http://oai.hconeai.com/v1",
    default_headers={
        "Helicone-Auth": f"Bearer {os.environ.get('HELICONE_API_KEY')}",
        "Helicone-Cache-Enabled": "true",
    },
)

def query_llm(llm_prompt, n_iter=5):
    chat_log = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": llm_prompt}
        ]
    response = gpt_client.chat.completions.create(
        model="gpt-4o",
        messages=chat_log
    )
    llm_reply = response.choices[0].message.content.replace("\n","  ")
    chat_log.append({"role": "assistant", "content": llm_reply})
    
    for _ in range(1,n_iter):
        chat_log.append({"role": "user", "content": "Are there any more drugs you missed?"})
        llm_reply = response.choices[0].message.content.replace("\n","  ")
        chat_log.append({"role": "assistant", "content": llm_reply})
    
    chat_log.append({"role": "user", "content": "Now take the entire list of drugs and format it as just drug names delimited with a ';'"})
    llm_reply = response.choices[0].message.content.replace("\n","  ")

    return llm_reply

df["answer"] = df["question"].apply(lambda x: query_llm(x, 5))

df = df[["drug", "question","answer"]]
df.to_csv("../../test_queries/alternative_therapy_queries.txt", index=False, sep="\t")