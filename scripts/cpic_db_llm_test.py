import psycopg2
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

cpic_wiki = open("db_docs/cpic_wiki.md").read()
cpic_schema = open("db_docs/cpic_schema.txt").read()

#llm_prompt = input("Please input prompt: ")
#llm_prompt = "Which populations have an Allele Frequency greater than 0.5 for CYP2C19*1?"
llm_prompt = "Return a list of populations that have an Allele Frequency greater than 0.5 for CYP2C19*1?"

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "You an assistant that generates sql queries for the CPIC database. You only output SQL queries and nothing else. Prepend 'cpic.' to any table names"},
        {"role": "system", "content": f"Here is a description of the CPIC database SQL schema: \n {cpic_wiki}"},
        {"role": "system", "content": f"Here is the SQL database schema dump: \n {cpic_schema}"},
        {"role": "user", "content": llm_prompt}
    ]
)
response_contents = response.choices[0].message.content

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

print(response_contents)
cursor.execute(response_contents)
rows = cursor.fetchall()

# Print out the results
for row in rows:
    print(row)

# Close the connection when finished
conn.close()



