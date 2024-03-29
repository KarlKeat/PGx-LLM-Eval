#!/usr/bin/bash

conda env create -f pgx_llm_maketests.yml

wget https://files.cpicpgx.org/data/database/cpic_db_dump-v1.38.0.sql.gz

echo "run 'conda activate pgx_llm_maketests' and then run './first_time_setup_part2.sh"