#! /bin/sh
sudo docker compose down
sudo docker compose build --no-cache
sudo docker compose up --build --force-recreate -d
