import openai
import os

client = openai.OpenAI(
    api_key='EMPTY',
    base_url="http://localhost:8000/v1",
)

llm_prompt = input("Please input prompt: ")

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    messages=[
        {"role": "system", "content": "You are an expert on pharmacogenomics. You answer questions about pharmacogenomics using evidence. If you do not know the answer to something, you will say so."},
        {"role": "user", "content": llm_prompt}
    ]
)


print(response.choices[0].message.content)
