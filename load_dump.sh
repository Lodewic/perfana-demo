#!/bin/bash
echo "Loading mysql and mongodb datadumps into demo..."

echo "Copying ./Archive/grafana.sql into mariadb container..."
docker cp ./Archive/grafana.sql perfana-demo_mariadb_1:/usr/grafana.sql

echo "Loading grafana.sql dump into database..."
docker exec -it perfana-demo_mariadb_1 bash -c "mysql -pperfana --force -u root grafana < /usr/grafana.sql"

echo "Restoring mongodb database in mongo1 container with data dump..."
docker run --rm --network perfana-demo_perfana -v $PWD/Archive/dump:/backup mongo:4.4 bash -c 'mongorestore /backup --drop --host mongo1:27011'

echo "Done!"
