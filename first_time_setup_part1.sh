#!/usr/bin/bash

conda env create -f pgx_llm_maketests.yml

conda activate pgx_llm_maketests
python -m ipykernel install --user --name=pgx_llm_maketests
echo "run 'conda activate pgx_llm_maketests' and then run './first_time_setup_part2.sh"
