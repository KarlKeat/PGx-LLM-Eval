#!/usr/bin/bash

initdb -D ./data
pg_ctl -D ./data -l logfile start
createdb cpic_db
gzip -c -d cpic_db_dump-v1.38.0.sql.gz | psql cpic_db