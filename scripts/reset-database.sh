#!/bin/bash
PGPASSWORD=$DJANGO_DB_PASSWORD
PGUSER=$DJANGO_DB_USER
PGDATABASE="postgres"

echo 'close open database connections'
psql --quiet << END_OF_SQL
  SELECT pg_terminate_backend(pg_stat_activity.pid)
  FROM pg_stat_activity
  WHERE datname = '$DJANGO_DB_NAME'
    AND pid <> pg_backend_pid();
END_OF_SQL

# delete Supervisors and Participants
django-admin dummydata -X
echo 'backup of superusers'
django-admin dumpdata auth.user > superusers.json
echo 'clear database'
django-admin reset_db --noinput
echo 'run migrations'
django-admin migrate
echo 'reload superusers'
django-admin loaddata superusers.json
echo 'populate database with dummydata'
django-admin dummydata -f2014 -y3 -s5 -p10 -a semantic
