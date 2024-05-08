import pandas as pd
import re

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


class RecToCategoryTestRunner(TestRunner):
    def __init__(self, llm_client, model_name, system_prompt):
        super().__init__(llm_client, model_name, system_prompt)
    
    def query_llm(self, llm_prompt):
        return super().query_llm(llm_prompt)
    
    def run_tests(self, in_path, out_path):
        tests = pd.read_csv(in_path, sep="\t", header=0)

        tests["llm_answer"] = tests["question"].apply(self.query_llm)
        tests["score"] = tests.apply(lambda x: x["answer"] == x["llm_answer"], axis = 1)

        tests.to_csv(out_path, sep="\t", index=False)
        return {"Accuracy": tests['score'].mean()}