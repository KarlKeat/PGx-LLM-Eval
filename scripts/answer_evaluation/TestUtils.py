import pandas as pd
import re
import os
import openai
import itertools
from numpy import dot, mean
from numpy.linalg import norm
from text_embeddings import *

class TestRunner:
    def __init__(self, llm_client, model_name, system_prompt):
        self.client = llm_client
        self.model = model_name
        self.sys_prompt = system_prompt

    def query_llm(self, llm_prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.sys_prompt},
                {"role": "user", "content": llm_prompt}
            ]
        )
        return response.choices[0].message.content.replace("\n","  ")
    
    def run_tests(self, in_path, out_path):
        pass


class AlleleDefinitionTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
    
    def query_llm(self, llm_prompt):
        return super().query_llm(llm_prompt)
    
    @staticmethod
    def extract_rsids(llm_answer):
        llm_list = list(set(re.findall(r'rs[0-9]+', llm_answer)))
        return llm_list

    @staticmethod
    def score_response(llm_rsids, ref_answer):
        precision = 0
        recall = 0

        ref_list = list(set(ref_answer.split(";")))
        
        for rsid in llm_rsids:
            if rsid in ref_list:
                precision += 1
        precision = precision / len(llm_rsids) if len(llm_rsids) > 0 else 0

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

class AlleleFrequencyTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
    
    def query_llm(self, llm_prompt):
        return super().query_llm(llm_prompt)
    
    @staticmethod
    def score_response(llm_answer, ref_answer):
        search_result = re.search(r'[0-9]\.[0-9]{4}', llm_answer)
        llm_freq = round(float(search_result.group(0)), 4) if search_result is not None else 0.5000
        
        return abs(ref_answer - llm_freq)
    
    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)
        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["score"] = tests.apply(lambda x: self.score_response(llm_answer=x["llm_answer"], ref_answer=x["answer"]), axis=1)
        tests.to_csv(out_path, sep="\t", index=False)
        return {"Mean absolute deviation": tests['score'].mean()}

class AlleleFunctionTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
    
    def query_llm(self, llm_prompt):
        return super().query_llm(llm_prompt)
    
    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["score"] = tests.apply(lambda x: x["answer"].lower() == x["llm_answer"].lower().strip("'"), axis = 1)

        tests.to_csv(out_path, sep="\t", index=False)
        return {"Accuracy": tests['score'].mean()}
    
class DiplotypeToPhenotypeTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
    
    def query_llm(self, llm_prompt):
        return super().query_llm(llm_prompt)
    
    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["score"] = tests.apply(lambda x: x["answer"].lower() == x["llm_answer"].lower().strip("'"), axis = 1)

        tests.to_csv(out_path, sep="\t", index=False)
        return {"Accuracy": tests['score'].mean()}
    

class DrugToGenesTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
    
    def query_llm(self, llm_prompt):
        return super().query_llm(llm_prompt)
    
    @staticmethod
    def extract_genes(llm_answer):
        return [x.strip() for x in llm_answer.split(";")]
    
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
        tests = tests.sample(20)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["llm_genes"] = tests["llm_answer"].apply(self.extract_genes)

        tests[["precision","recall"]] = tests.apply(lambda x: self.score_response(llm_genes=x["llm_genes"], ref_answer=x["answer"]), axis=1, result_type="expand")
        tests.to_csv(out_path, sep="\t", index=False)
        return {"Mean precision": tests['precision'].mean(),
                "Mean recall": tests['recall'].mean()}
    

class GeneToDrugsTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
    
    def query_llm(self, llm_prompt):
        return super().query_llm(llm_prompt)
    
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


class PhenoToCategoryTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
    
    def query_llm(self, llm_prompt):
        return super().query_llm(llm_prompt)
    
    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0, keep_default_na=False)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["score"] = tests.apply(lambda x: x["answer"] == x["llm_answer"], axis = 1)

        tests.to_csv(out_path, sep="\t", index=False)
        return {"Accuracy": tests['score'].mean()}
    
class PhenoToGuidelineTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
        self.embedding_cache = {}
        self.embedding_funcs = {
            'oai_embedding': oai_embedding,
            'negation_mpnet': negation_mpnet,
            'base_mpnet': base_mpnet,
            'roberta': roberta,
            'gte': gte,
        }
    
    def query_llm(self, llm_prompt):
        return super().query_llm(llm_prompt)

    def cosine_sim(self, vector1, vector2):
        return dot(vector1, vector2)/(norm(vector1)*norm(vector2))
    
    def precompute_embeddings(self, strings):
        queries = sorted(list(set(strings)))
        for func_name in self.embedding_funcs:
            func = self.embedding_funcs[func_name]

            if func not in self.embedding_cache:
                self.embedding_cache[func] = {}
            
            embeddings = func(queries)
            self.embedding_cache[func] = self.embedding_cache[func] | dict(zip(queries, embeddings))
    
    def embedding_similarity(self, ref_answer, comparison_answer, embedding_func):
        ref_embedding = self.embedding_cache[embedding_func][ref_answer]
        comparison_embedding = self.embedding_cache[embedding_func][comparison_answer]

        return self.cosine_sim(ref_embedding, comparison_embedding)
    
    def mean_similarity_score(self, ref_answer, comparison_answers, embedding_func):
        comparisons = []
        for answer in comparison_answers:
            comparisons.append(self.embedding_similarity(ref_answer, answer, embedding_func))

        return mean(comparisons)
    
    def oai_llm_similarity(self, sentence1, sentence2, model="gpt-4o"):
        gpt_client = openai.OpenAI(
            organization=os.environ.get("KIMLAB_OAI_ID"),
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="http://oai.hconeai.com/v1",
            default_headers={
                "Helicone-Auth": f"Bearer {os.environ.get('HELICONE_API_KEY')}",
                "Helicone-Cache-Enabled": "true",
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
        tests = pd.read_csv(in_path, sep="\t", header=0, keep_default_na=False).sample(50)

        tests["question"] = tests["question"].apply(lambda x: x + " Give a 2-3 sentence summary.")
        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["incorrect_recommendations"] = tests["incorrect_recommendations"].apply(lambda x: x.split("|"))

        
        print("start_embeddings")
        self.precompute_embeddings(tests["answer"])
        self.precompute_embeddings(tests["llm_answer"])
        self.precompute_embeddings(tests["concurring_recommendation"])
        self.precompute_embeddings(itertools.chain.from_iterable(tests["incorrect_recommendations"]))
        print("done embeddings")

        out_dict = {}
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
        tests[f"gpt4_ref_vs_llm"] = tests.apply(lambda x: self.oai_llm_similarity(x["answer"], x["llm_answer"]), axis = 1)
        out_dict[f"gpt4_ref_vs_llm"] = tests[f"gpt4_ref_vs_llm"].mean()

        print(tests[list(out_dict.keys())].corr())

        tests.to_csv(out_path, sep="\t", index=False)
        return out_dict
