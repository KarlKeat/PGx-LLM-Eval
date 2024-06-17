import pandas as pd
import re
import os
import openai
import itertools
from tqdm import tqdm
from numpy import dot, mean
from numpy.linalg import norm
from bert_score import BERTScorer
from text_embeddings import *
from gemini_client import GeminiClient

tqdm.pandas()

# Superclass (All test runner classes are subclasses of this)
class TestRunner:
    # Accepts an openai.OpenAI() object, the name of the model ("gpt-4-turbo", "gpt3.5-turbo", "llama-3", etc), and a system prompt for the LLM
    def __init__(self, llm_client, model_name, system_prompt):
        self.client = llm_client
        self.model = model_name
        self.sys_prompt = system_prompt

    # Class method inherited by all test runners. Takes the provided llm client and queries it with a specified prompt.
    def query_llm(self, llm_prompt):
        if type(self.client) == GeminiClient:
            response = self.client.send_query(self.model, self.sys_prompt, llm_prompt)
            result = response.json()["candidates"][0]["finishReason"]
            if result == "SAFETY":
                answer = "No response (safety filter)"
            else:
                answer = response.json()["candidates"][0]["content"]["parts"][0]["text"].replace("\n","  ")
            return answer
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.sys_prompt},
                    {"role": "user", "content": llm_prompt}
                ]
            )
            return response.choices[0].message.content.replace("\n","  ")
    
    # An empty method to be overloaded by subclasses. in_path is a path to a .txt file containing the tests, and out_path is a path to a .txt file containing the answers and scores
    def run_tests(self, in_path, out_path): # Returns a dictionary with summary metrics {"metric_name": value}
        pass

# Tests for allele definition task (for this gene and allele, what are the rsIDs associated?)
class AlleleDefinitionTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)

    # Regex search for valid rsIDs in a given string
    @staticmethod
    def extract_rsids(llm_answer):
        llm_list = list(set(re.findall(r'rs[0-9]+', llm_answer)))
        return llm_list

    # Given a reference list of rsIDs and an LLM-derived list of rsIDs, calculate the precision and recall
    @staticmethod
    def score_response(llm_rsids, ref_answer):
        precision = 0
        recall = 0

        ref_list = list(set(ref_answer.split(";"))) # Convert the ';'-delimited reference string into a list object

        for rsid in llm_rsids:
            if rsid in ref_list:
                precision += 1
        precision = precision / len(llm_rsids) if len(llm_rsids) > 0 else 0 # if llm produces no rsIDs, precision is 0

        for rsid in ref_list:
            if rsid in llm_rsids:
                recall += 1
        recall = recall / len(ref_list)

        return precision, recall

    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["llm_rsids"] = tests["llm_answer"].apply(self.extract_rsids)

        tests[["precision","recall"]] = tests.apply(lambda x: self.score_response(llm_rsids=x["llm_rsids"], ref_answer=x["answer"]), axis=1, result_type="expand")

        tests.to_csv(out_path, sep="\t", index=False)
        return {"Mean precision": tests['precision'].mean(),
                "Mean recall": tests['recall'].mean()}

# How frequent is a specific allele in a specific population?
class AlleleFrequencyTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)

    # Search the answer for numbers and return the difference between the LLM answer and the true answer
    @staticmethod
    def score_response(llm_answer, ref_answer):
        search_result = re.search(r'[0-9]\.[0-9]{4}', llm_answer)
        if search_result is None:
            return 0.5
        else:
            llm_freq = round(float(search_result.group(0)), 4)

        return abs(ref_answer - llm_freq)

    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)
        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["score"] = tests.apply(lambda x: self.score_response(llm_answer=x["llm_answer"], ref_answer=x["answer"]), axis=1)
        tests.to_csv(out_path, sep="\t", index=False)
        return {"Mean absolute deviation": tests['score'].mean()}

# What is the CPIC functional classification of this allele?
class AlleleFunctionTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)

    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["score"] = tests.apply(lambda x: x["answer"].lower() == x["llm_answer"].lower().strip("'"), axis = 1)

        tests.to_csv(out_path, sep="\t", index=False)
        return {"Accuracy": tests['score'].mean()}

# For a given gene and diplotype, what is the CPIC phenotype?
class DiplotypeToPhenotypeTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)

    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["score"] = tests.apply(lambda x: x["answer"].lower() == x["llm_answer"].lower().strip("'"), axis = 1)

        tests.to_csv(out_path, sep="\t", index=False)
        return {"Accuracy": tests['score'].mean()}

# For a given drug, what CPIC genes have pharmacogenetic associations
class DrugToGenesTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)

    # Take the answer and extract the genes
    @staticmethod
    def extract_genes(llm_answer):
        return [x.strip() for x in llm_answer.split(";")]

    # Calculate precision and recall
    @staticmethod
    def score_response(llm_genes, ref_answer):
        precision = 0
        recall = 0

        ref_list = list(set(ref_answer.split(";")))

        for gene in llm_genes:
            if gene in ref_list:
                precision += 1
        precision = precision / len(llm_genes) if len(llm_genes) > 0 else 0

        for gene in ref_list:
            if gene in llm_genes:
                recall += 1
        recall = recall / len(ref_list)

        return precision, recall

    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["llm_genes"] = tests["llm_answer"].apply(self.extract_genes)

        tests[["precision","recall"]] = tests.apply(lambda x: self.score_response(llm_genes=x["llm_genes"], ref_answer=x["answer"]), axis=1, result_type="expand")
        tests.to_csv(out_path, sep="\t", index=False)
        return {"Mean precision": tests['precision'].mean(),
                "Mean recall": tests['recall'].mean()}

# For a given CPIC gene, what drugs have guidelines including it?
class GeneToDrugsTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)

    # Calculate precision and recall
    @staticmethod
    def score_response(llm_drugs, ref_answer):
        precision = 0
        recall = 0

        ref_list = list(set(ref_answer.split(";")))

        for drug in llm_drugs:
            if drug in ref_list:
                precision += 1
        precision = precision / len(llm_drugs) if len(llm_drugs) > 0 else 0

        for drug in ref_list:
            if drug in llm_drugs:
                recall += 1
        recall = recall / len(ref_list)

        return precision, recall

    @staticmethod
    def extract_drugs(llm_answer):
        return [x.strip().lower() for x in llm_answer.split(";")]

    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["llm_drugs"] = tests["llm_answer"].apply(self.extract_drugs)


        tests[["precision","recall"]] = tests.apply(lambda x: self.score_response(llm_drugs=x["llm_drugs"], ref_answer=x["answer"]), axis=1, result_type="expand")
        tests.to_csv(out_path, sep="\t", index=False)

        return {"Mean precision": tests['precision'].mean(),
                "Mean recall": tests['recall'].mean()}

# For a given pharmacogenetic phenotype and drug, what class of guidelines would be recommended? (Alter dose, Avoid, or No change)
class PhenoToCategoryTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)

    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0, keep_default_na=False)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["score"] = tests.apply(lambda x: x["answer"] == x["llm_answer"], axis = 1)

        tests.to_csv(out_path, sep="\t", index=False)
        return {"Accuracy": tests['score'].mean()}

# For a given pharmacogenetic phenotype and drug, what is the guideline? (short answer)
class PhenoToGuidelineTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
        self.embedding_cache = {} # precompute embeddings to prevent redundancy
        self.embedding_funcs = { # embedding functions from text_embeddings.py
            'oai_embedding': oai_embedding,
            'negation_mpnet': negation_mpnet,
            'base_mpnet': base_mpnet,
            'roberta': roberta,
            'gte': gte,
        }
        self.bert_scorer = BERTScorer(
            model_type='allenai/scibert_scivocab_uncased',
            lang='en-sci',
            rescale_with_baseline=True,
            device='cuda:1',
        )

    # calculate cosine similarity between two vectors
    @staticmethod
    def cosine_sim(vector1, vector2):
        return dot(vector1, vector2)/(norm(vector1)*norm(vector2))

    # computes embeddings for all strings and adds them to embedding cache
    def precompute_embeddings(self, strings):
        queries = sorted(list(set(strings)))
        for func_name in self.embedding_funcs:
            func = self.embedding_funcs[func_name]

            if func not in self.embedding_cache:
                self.embedding_cache[func] = {}

            embeddings = func(queries)
            self.embedding_cache[func] = self.embedding_cache[func] | dict(zip(queries, embeddings))

    # Calls an embedding function and returns the cosine similarity between two strings in a specific embedding space
    def embedding_similarity(self, ref_answer, comparison_answer, embedding_func):
        ref_embedding = self.embedding_cache[embedding_func][ref_answer]
        comparison_embedding = self.embedding_cache[embedding_func][comparison_answer]

        return self.cosine_sim(ref_embedding, comparison_embedding)

    # Returns the mean similarity between a string and a set of other strings
    def mean_similarity_score(self, ref_answer, comparison_answers, embedding_func):
        comparisons = []
        for answer in comparison_answers:
            comparisons.append(self.embedding_similarity(ref_answer, answer, embedding_func))

        return mean(comparisons)

    # Similarity metric based on LLM prompting
    def oai_llm_similarity(self, sentence1, sentence2, model="gpt-4o"):
        gpt_client = openai.OpenAI(
            organization=os.environ.get("KIMLAB_OAI_ID"),
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://oai.hconeai.com/v1",
            default_headers={
                "Helicone-Auth": f"Bearer {os.environ.get('HELICONE_API_KEY')}",
                "Helicone-Cache-Enabled": "true",
                "Cache-Control": "max-age=2592000", # Set cache to 30 days
            },
        )

        prompt = f"These two passages are providing pharmacogenetic recommendations based on the same drug and pharmacogenetic phenotype. Do the passages recommend the same clinical action? Respond with 'yes' or 'no' only, with no added context. Passage 1: '{sentence1}'. Passage 2: '{sentence2}'"
        response = gpt_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a model that inteprets pharmacogenetic recommendations."},
                {"role": "user", "content": prompt}
            ]
        ).choices[0].message.content
        if 'yes' in response.lower():
            return 1
        if 'no' in response.lower():
            return 0
        else:
            raise Exception

    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0, keep_default_na=False)

        tests["question"] = tests["question"].progress_apply(lambda x: x + " Give a 2-3 sentence summary.")
        tests["llm_answer"] = tests["question"].progress_apply(self.query_llm)
        tests["incorrect_recommendations"] = tests["incorrect_recommendations"].progress_apply(lambda x: x.split("|"))

        # Precompute embeddings for all strings
        self.precompute_embeddings(tests["answer"])
        self.precompute_embeddings(tests["llm_answer"])
        self.precompute_embeddings(tests["concurring_recommendation"])
        self.precompute_embeddings(itertools.chain.from_iterable(tests["incorrect_recommendations"]))

        # Compute BERTScore precision, recall, and F1
        P, R, F1 = self.bert_scorer.score(tests['llm_answer'], tests['answer'])

        out_dict = {} # store output in a dictionary
        tests['bert_score_precision'] = P
        tests['bert_score_recall'] = R
        tests['bert_score_f1'] = F1
        out_dict['bert_score_precision'] = tests['bert_score_precision'].mean()
        out_dict['bert_score_recall'] = tests['bert_score_recall'].mean()
        out_dict['bert_score_f1'] = tests['bert_score_f1'].mean()
        for func_name in self.embedding_funcs:
            func = self.embedding_funcs[func_name]
            tests[f"{func_name}_ref_vs_llm"] = tests.apply(lambda x: self.embedding_similarity(x["answer"], x["llm_answer"], func), axis = 1)
            tests[f"{func_name}_ref_vs_concurring"] = tests.apply(lambda x: self.embedding_similarity(x["answer"], x["concurring_recommendation"], func), axis = 1)
            tests[f"{func_name}_adversarial_vs_llm"] = tests.apply(lambda x: self.mean_similarity_score(x["answer"], x["incorrect_recommendations"], func), axis = 1)
            tests[f"{func_name}_concurring_vs_llm"] = tests.apply(lambda x: self.embedding_similarity(x["llm_answer"], x["concurring_recommendation"], func), axis = 1)
            out_dict[f"{func_name}_ref_vs_llm"] = tests[f"{func_name}_ref_vs_llm"].mean()
            out_dict[f"{func_name}_ref_vs_concurring"] = tests[f"{func_name}_ref_vs_concurring"].mean()
            out_dict[f"{func_name}_adversarial_vs_llm"] = tests[f"{func_name}_adversarial_vs_llm"].mean()
            out_dict[f"{func_name}_concurring_vs_llm"] = tests[f"{func_name}_concurring_vs_llm"].mean()
        tests[f"gpt4_ref_vs_llm"] = tests.progress_apply(lambda x: self.oai_llm_similarity(x["answer"], x["llm_answer"]), axis = 1)
        out_dict[f"gpt4_ref_vs_llm"] = tests[f"gpt4_ref_vs_llm"].mean()

        print(tests[list(out_dict.keys())].corr())

        tests.to_csv(out_path, sep="\t", index=False)
        return out_dict
