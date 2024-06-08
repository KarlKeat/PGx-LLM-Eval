import os
import requests


system_prompt = "You are an AI assistant that provides evidence-based responses to pharmacogenomics questions. Please respond to the following query."
llm_prompt = input("Please input prompt: ")
response = requests.post(
    url="https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent",
    headers={
        "x-goog-api-key": os.environ.get("GOOGLE_API_KEY")
    },
    json={
        "contents":[ 
            {"role": "model", "parts":[{"text": system_prompt}]},
            {"role": "user", "parts":[{"text": llm_prompt}]}
        ],
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ]
    }
)

result = response.json()["candidates"][0]["finishReason"]
retries = 3
while retries > 0 and result == "SAFETY":
    retries = retries - 1
    response = requests.post(
        url="https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent",
        headers={
            "x-goog-api-key": os.environ.get("GOOGLE_API_KEY")
        },
        json={
            "contents":[ 
                {"role": "model", "parts":[{"text": system_prompt}]},
                {"role": "user", "parts":[{"text": llm_prompt}]}
            ],
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
        }
    )
    result = response.json()["candidates"][0]["finishReason"]
if result == "SAFETY":
    print("No reponse (safety)")
else:
    print(response.json()["candidates"][0]["content"]["parts"][0]["text"])