import openai
import os
import sys
sys.path.append(f"{os.getcwd()}/test_utils")
from gemini_client import GeminiClient
from TestUtils import *

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

llama_client = openai.OpenAI(
    api_key='EMPTY',
    base_url="http://localhost:8000/v1",
)

gemini_client = GeminiClient()

input_dir = "../../test_queries/subsets"
input_paths = {
    'AlleleDefinition': f"{input_dir}/allele_def_subset.txt",
    'AlleleFrequency': f"{input_dir}/allele_freq_subset.txt",
    'AlleleFunction': f"{input_dir}/allele_function_subset.txt",
    'DiplotypeToPhenotype': f"{input_dir}/diplotype_to_phenotype_subset.txt",
    'DrugToGenes': f"{input_dir}/drug_to_genes_subset.txt",
    'GeneToDrugs': f"{input_dir}/gene_to_drugs_subset.txt",
    'PhenoToCategory': f"{input_dir}/recommendation_category_for_pheno_subset.txt",
    'PhenoToGuideline': f"{input_dir}/drug_guidelines_for_pheno_subset.txt"
}

test_runners = TestRunner.__subclasses__()
# test_runners = [PhenoToGuidelineTestRunner]

def run_tests(model_name, client):
    display_name = model_name.split('/')[-1] if ('/' in model_name) else model_name
    print(f"# {display_name}\n")
    for runner_class in test_runners:
        test_name = runner_class.__name__.replace("TestRunner","")
        runner = runner_class(client, model_name, SYSTEM_PROMPT)
        input_path = input_paths[test_name]
        output_path = f"../../results/{test_name}_{display_name}_results.txt"
        result = runner.run_tests(input_path, output_path)
        print(f"## {test_name}\n")
        for score_category in result:
            print(f"{score_category}: {result[score_category]}\n")

run_tests("gpt-3.5-turbo", gpt_client)
run_tests("gpt-4-turbo", gpt_client)
run_tests("gpt-4o", gpt_client)
run_tests("gemini-pro", gemini_client)
run_tests("meta-llama/Meta-Llama-3-70B-Instruct", llama_client)
