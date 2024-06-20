import openai
import pandas as pd 
import os
import sys

from random import random
from tqdm.auto import tqdm

SYSTEM_PROMPT = "You are an AI assistant that provides evidence-based responses to pharmacogenomics questions. Please respond to the following query."

gpt_client = openai.OpenAI(
    organization=os.environ.get("KIMLAB_OAI_ID"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="https://oai.hconeai.com/v1",
    default_headers={
        "Helicone-Auth": f"Bearer {os.environ.get('HELICONE_API_KEY')}",
        "Helicone-Cache-Enabled": "true",
    },
)

def query_llm(self, llm_prompt):
    response = gpt_client.chat.completions.create(
       model = 'gpt-4o',
       messages = [
           {'role': 'system', 'content': SYSTEM_PROMPT},
           {'role': 'user', 'content': llm_prompt}
       ]
    )
    return response.choices[0].message.content.replace("\n", "  ")

df = pd.read_csv('../../test_queries/expert_review_human_answers.tsv', sep='\t', header=0)

# Generate GPT-4o responses to questions
gpt_responses = []
for question in tqdm(df['question']):
    response = query_llm(gpt_client, question)
    gpt_responses.append(response)
df['gpt4o_answer'] = gpt_responses

# Rename human and GPT-4o columns and shuffle
df = df.rename(columns={"human_answer": "answer_1", "gpt4o_answer": "answer_2"}) 
df['answer_1_answerer'] = 'human'
# randomly swap answer 1 and answer 2
for i in range(len(df)):
    if random() > 0.5:
        temp = df.at[i, 'answer_1']
        df.at[i, 'answer_1'] = df.at[i, 'answer_2']
        df.at[i, 'answer_2'] = temp
        df.at[i, 'answer_1_answerer'] = 'gpt-4o'

df.to_csv('../../test_queries/expert_review_questions.tsv', sep='\t', index=False)
