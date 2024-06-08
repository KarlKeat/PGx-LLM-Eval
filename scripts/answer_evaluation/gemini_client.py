import os
import requests

class GeminiClient:
    def __init__(self):
        pass

    def send_query(self, model, sys_prompt, llm_prompt):
        response = requests.post(
            url=f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent",
            headers={
                "x-goog-api-key": os.environ.get("GOOGLE_API_KEY")
            },
            json={"contents":[ 
                    {"role": "model", "parts":[{"text": sys_prompt}]},
                    {"role": "user", "parts":[{"text": llm_prompt}]}
                ]
            }
        )
        return response