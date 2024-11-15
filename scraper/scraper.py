#! /usr/bin/env python3

# general imports
from time import sleep
from os import getenv

# config
print('[ripper] loading config...', end='')
from json import load
from dotenv import load_dotenv
load_dotenv()
with open('config.json', 'r') as f:
    cfg = load(f)
print('done')

# influxdb setup
print('[ripper] loading influx info...', end='')
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
influxdb_url = getenv('INFLUXDB_URL')
influxdb_token = getenv('INFLUXDB_TOKEN')
influxdb_org = getenv('INFLUXDB_ORG')
influxdb_bucket = getenv('INFLUXDB_BUCKET')
client = InfluxDBClient(url=influxdb_url, token=influxdb_token, org=influxdb_org)
write_api = client.write_api(write_options=SYNCHRONOUS)
print('done')

# connect to nodes and build data dictionary
def scrape() -> dict:
    data = {}
    from random import randint, choice

    for node in cfg['nodes']:
        host = node['host']
        gpus = node['gpus']

        # CPU scrape
        # TODO: sudo turbostat -q -S -n 1 -s Busy%,PkgWatt
        data[f'{host}-cpu-usg'] = randint(0, 100)
        data[f'{host}-cpu-pkg'] = randint(5, 65)

        # GPU scrape
        for gpu in range(gpus):
            # TODO: nvidia-smi -q -i <gpu> -d UTILIZATION,POWER
            data[f'{host}-gpu{gpu}-usg'] = randint(0, 100)
            data[f'{host}-gpu{gpu}-pkg'] = randint(40, 200)

    return data

# upload data to influx
def push(data: dict):
    if not data:
        return

    point = Point('rip')
    for k, v in data.items():
        point.field(k, v)
    try:
        write_api.write(bucket=influxdb_bucket, org=influxdb_org, record=point)
    except Exception as e:
        print('[ripper] failed to push to db:', e)

# ripper go rip
print('[ripper] waiting for db to start...', end='')
sleep(5) # (docker depends_on is not accurate sadly)
print('done?')
while __name__ == '__main__':
    data = scrape()
    push(data)
    sleep(cfg['interval'])
