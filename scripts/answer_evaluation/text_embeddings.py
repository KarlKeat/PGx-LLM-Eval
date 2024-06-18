from sentence_transformers import SentenceTransformer, util
from functools import partial
from transformers import pipeline
import openai
import os

# Using a SentenceTransformer model to compute similarity between two sentences
def st_model(sentences, model_name,trust_remote_code=False):
    model = SentenceTransformer(model_name, trust_remote_code=trust_remote_code)
    embeddings = model.encode(sentences, convert_to_numpy=True)
    return embeddings


negation_mpnet = partial(st_model, model_name='dmlls/all-mpnet-base-v2-negation')

base_mpnet = partial(st_model, model_name='sentence-transformers/all-mpnet-base-v2')

roberta = partial(st_model, model_name='sentence-transformers/all-distilroberta-v1')

# NOTE: trusting remote code sounds scary, and it is.
# Consider avoiding using models that need this, though this one does because it's not
# available via the transformers library (or some nuances like that, not 100% clear on this)
gte = partial(st_model, model_name='Alibaba-NLP/gte-base-en-v1.5', trust_remote_code=True)


"""
Can define the other metrics in the same way, with different models as needed
using partial functions around the st_model_similarity function
"""


# Using a negation-aware BLEURT metric
# This takes in pairs and outputs a "score" that I don't fully understand
# but that supposedly represents the similarity between the two sentences
def negbleurt_model_similarity(sentence1, sentence2):

    model_name = 'tum-nlp/NegBLEURT'
    pipe = pipeline("text-classification", model=model_name, function_to_apply="none")

    pairwise_input = [[[sentence1, sentence2]]]

    return pipe(pairwise_input)

def oai_embedding(sentences, model="text-embedding-3-small"):
        client = openai.OpenAI(
            organization=os.environ.get("KIMLAB_OAI_ID"),
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://oai.helicone.ai/v1",
            default_headers={
                "Helicone-Auth": f"Bearer {os.environ.get('HELICONE_API_KEY')}",
                "Helicone-Cache-Enabled": "true",
            },
        )

        return [client.embeddings.create(input=sentence,model=model).data[0].embedding for sentence in sentences]
