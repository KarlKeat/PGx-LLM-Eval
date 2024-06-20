## Extend misspecified questions with well-specified questions for refusal test
import pandas as pd

RANDOM_SEED = 42
QUESTIONS_BASE_PATH = '../../test_queries'
BASE_QUESTION_FILE = f'{QUESTIONS_BASE_PATH}/misspecified_questions.txt'

if __name__ == '__main__':
    questions = pd.read_csv(BASE_QUESTION_FILE, sep='\t', header=0)
    categories = questions['category'].unique()
    for category in categories: 
        # Randomly sample 20 well-specified questions for each category
        good_set = pd.read_csv(f'{QUESTIONS_BASE_PATH}/subsets/{category}_subset.txt', sep='\t', header=0)
        good_set = good_set.sample(n=20, random_state=RANDOM_SEED)[['question']]
        # Add opt-out phrase to each question
        good_set['question'] = good_set['question'].str.slice_replace(-1, repl=' or answer UNKNOWN if unknown.')
        good_set['category'] = category
        good_set['is_misspecified'] = False

        questions = pd.concat([questions, good_set])
    questions.to_csv(f'{QUESTIONS_BASE_PATH}/refusal_test_questions.txt', sep='\t', index=False)


