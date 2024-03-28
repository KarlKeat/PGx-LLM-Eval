#!/usr/bin/bash

conda env create -f pgx_llm_maketests.yml

wget https://files.cpicpgx.org/data/database/cpic_db_dump-v1.38.0.sql.gz

conda activate pgx_llm_maketests
initdb -D ./data
pg_ctl -D ./data -l logfile start
createdb cpic_db
gzip -c -d cpic_db_dump-v1.38.0.sql.gz | psql cpic_db
