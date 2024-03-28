import openai
import os

client = openai.OpenAI(
    organization=os.environ.get("KIMLAB_OAI_ID"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="http://oai.hconeai.com/v1",
    default_headers={
        "Helicone-Auth": f"Bearer {os.environ.get('HELICONE_API_KEY')}",
        "Helicone-Cache-Enabled": "true",
    },
)

llm_prompt = input("Please input prompt: ")

response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {"role": "system", "content": "You are an expert on pharmacogenomics. You answer questions about pharmacogenomics using evidence. If you do not know the answer to something, you will say so."},
        {"role": "user", "content": llm_prompt}
    ]
)


print(response.choices[0].message.content)
