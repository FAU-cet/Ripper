#! /usr/bin/env python3

# general imports
from time import sleep
from os import path
import paramiko

# env
from os import getenv
username = getenv('R_USER')
password = getenv('R_PASSWORD')
if password is None:
    password = ''
keyfile = None
if path.exists('./id_ssh'):
    keyfile = './id_ssh'

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

        # connect
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, key_filename=keyfile, password=password)

        # CPU scrape
        stdin, stdout, stderr = client.exec_command('sudo turbostat -q -S -n 1 -s Busy%,PkgWatt')
        stdin.write(password + '\n')
        intermediate = stdout.read().split('\n')[1].split(' ') # TODO: ' ' or '\t'?
        data[f'{host}-cpu-usg'] = round(float(intermediate[0]))
        data[f'{host}-cpu-pkg'] = round(float(intermediate[-1]))

        # GPU scrape
        for gpu in range(gpus):
            if node['vendor'] == 'nvidia':
                stdin, stdout, stderr = client.exec_command(f'nvidia-smi -q -i {gpu} -d UTILIZATION,POWER')
                usg = int([l for l in stdout.split('\n') if 'Gpu' in l][0].split(' ')[-2])
                pwr = round(float([l for l in stdout.split('\n') if 'Gpu' in l][0].split(' ')[-2]))
                data[f'{host}-gpu{gpu}-usg'] = usg
                data[f'{host}-gpu{gpu}-pwr'] = pwr
            else:
                print(f'GPU vendor {node['vendor']} not implemented')

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
