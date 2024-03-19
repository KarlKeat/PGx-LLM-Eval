#!/usr/bin/bash

conda env create -f pgx_llm_maketests.yml

wget https://files.cpicpgx.org/data/database/cpic_db_dump-v1.38.0.sql.gz

initdb -D ./data
createdb cpic_db
pg_ctl -D cpic_db -l logfile start
gzip -c -d cpic_db_dump-v1.38.0.sql.gz > psql cpic_db
