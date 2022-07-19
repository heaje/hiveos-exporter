#!/usr/bin/python3

import argparse
import datetime
import json
import logging
import re
import sys
from time import sleep
from typing import List, Tuple

from prometheus_client import Gauge, start_http_server

HIVEOS_CONFIG = '/hive-config/rig.conf'
HIVEOS_GPU_DETECT_FILE = '/run/hive/gpu-detect.json'
HIVEOS_STATS_FILE = '/run/hive/last_stat.json'
GPU_STATS_FILE = '/run/hive/gpu-stats.json'

SENSITIVE_CONFIG = ('RIG_PASSWD',)
GPU_LABELS = ['rig', 'card', 'model', 'brand', 'vendor']
METRICS = {
    'gpu_fan': Gauge('hiveos_gpu_fan', 'GPU Fan Speed', GPU_LABELS),
    'gpu_coretemp': Gauge('hiveos_gpu_core_temp', 'GPU Core Temp', GPU_LABELS),
    'gpu_hash': Gauge('hiveos_gpu_hashrate', 'GPU Hashrate', GPU_LABELS + ['coin', 'miner', 'miner_version']),
    'gpu_jtemp': Gauge('hiveos_gpu_junction_temp', 'GPU Junction Temperature', GPU_LABELS),
    'gpu_load': Gauge('hiveos_gpu_load', 'GPU load utilization', GPU_LABELS),
    'gpu_memtemp': Gauge('hiveos_gpu_mem_temp', 'GPU Memory Temperature', GPU_LABELS),
    'gpu_power': Gauge('hiveos_gpu_power_watts', 'GPU Power Consumption', GPU_LABELS),
    'cpu_hash': Gauge('hiveos_cpu_hashrate', 'CPU Hashrate', ['rig', 'core', 'coin', 'miner', 'miner_version']),
    'cpu_temp': Gauge('hiveos_cpu_temp', 'CPU Temperature', ['rig', 'cpu']),
    'ratio': Gauge('hiveos_miner_ratio', 'Acceptance ratio', ['rig', 'type', 'coin', 'miner', 'miner_version']),
    'total_hash': Gauge('hiveos_miner_hashrate', 'Hashrate', ['rig', 'coin', 'miner', 'miner_version']),
}

log = None


class Gpu:
    def __init__(self, index: int, gpu_detect_dict: dict) -> None:
        self.model = gpu_detect_dict['name']
        self.brand = gpu_detect_dict['brand']
        self.vendor = gpu_detect_dict['subvendor']
        self.bus_number_hex_str = gpu_detect_dict['busid']
        self.bus_number_decimal = int(gpu_detect_dict['busid'].split(':')[0], 16)
        self.card_index = index

    def is_nvidia(self) -> bool:
        return self.brand.lower() == 'nvidia'

    def is_amd(self) -> bool:
        return self.brand.lower() == 'amd'


class Miner:
    def __init__(self, name: str, stats: dict, total_khs: int, coin: str) -> None:
        self.name = name
        self.stats = stats
        self.total_hs = total_khs * 1000
        self.coin = coin

    def is_gpu_miner(self) -> bool:
        return self.stats['bus_numbers'][0] is not None

    def is_cpu_miner(self) -> bool:
        return self.stats['bus_numbers'][0] is None


def read_gpu_details() -> Tuple[List[Gpu], dict]:
    gpu_by_index = []
    gpu_by_bus_num = {}
    log.debug('Reading GPU details from %s', HIVEOS_GPU_DETECT_FILE)
    with open(HIVEOS_GPU_DETECT_FILE, 'r') as gpu_detect:
        for index, cur_gpu in enumerate(json.load(gpu_detect)):
            gpu_obj = Gpu(index, cur_gpu)
            gpu_by_index.append(gpu_obj)
            gpu_by_bus_num[gpu_obj.bus_number_decimal] = gpu_obj

    return gpu_by_index, gpu_by_bus_num


def read_stats_file() -> dict:
    log.debug('Reading statistics from %s', HIVEOS_STATS_FILE)
    with open(HIVEOS_STATS_FILE, 'r') as stats:
        return json.load(stats)


def read_miner_stats() -> List[Miner]:
    miners = []
    data = read_stats_file()['params']
    for miner_name, meta in data['meta'].items():
        for miner_num in range(1, len(data['meta']) + 1):
            postfix = ''
            if miner_num > 1:
                postfix = str(miner_num)

            if miner_name == data['miner{}'.format(postfix)]:
                miner_stats = data['miner_stats{}'.format(postfix)]
                miner_khs = data['total_khs{}'.format(postfix)]
                coin = meta['coin']
                miners.append(Miner(miner_name, miner_stats, miner_khs, coin))
                break
            else:
                continue

    return miners


def read_cpu_temp() -> List:
    return read_stats_file()['params']['cputemp']


def read_gpu_stats() -> dict:
    log.debug('Reading GPU statistics from %s', GPU_STATS_FILE)
    with open(GPU_STATS_FILE, 'r') as gpu_stats:
        return json.load(gpu_stats)


def read_hiveos_config(path: str) -> dict:
    log.debug('Reading HiveOS configuration from %s', path)
    config = {}
    valid_line = re.compile('^\s*([a-zA-Z0-9_]+)="*([^"\n]+)"*\S *$')
    with open(path, 'r') as hive_config:
        for line in hive_config.readlines():
            match = valid_line.match(line)
            if not match:
                continue
            elif match.group(1) in SENSITIVE_CONFIG:
                continue
            config[match.group(1)] = match.group(2)

    return config


def init_logging(level):
    global log
    log = logging.getLogger(__name__)
    log.addHandler(logging.NullHandler())

    log_level_constant = getattr(logging, level.upper())
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)
    log.setLevel(log_level_constant)


def get_opts():
    parser = argparse.ArgumentParser(description='HiveOS Prometheus exporter',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-l', '--log_level', dest='log_level', help='The logging level', default='info')
    parser.add_argument('-r', '--refresh', dest='refresh', help='How often to refresh metrics', default=60, type=int)
    parser.add_argument('-p', '--port', dest='port', help='The listening port for the exporter', default=10101,
                        type=int)
    return parser.parse_args()


def main():
    opts = get_opts()
    init_logging(opts.log_level)
    config = read_hiveos_config(HIVEOS_CONFIG)
    rig = config['WORKER_NAME']
    log.info('Starting HTTP server on port %s', opts.port)
    start_http_server(opts.port)
    while True:
        gpu_by_index, gpu_by_bus_num = read_gpu_details()
        for cur_miner in read_miner_stats():
            METRICS['ratio'].labels(rig=rig, type='accepted', coin=cur_miner.coin, miner=cur_miner.name,
                                    miner_version=cur_miner.stats['ver']).set(cur_miner.stats['ar'][0])
            METRICS['ratio'].labels(rig=rig, type='rejected', coin=cur_miner.coin, miner=cur_miner.name,
                                    miner_version=cur_miner.stats['ver']).set(cur_miner.stats['ar'][1])
            if len(cur_miner.stats['ar']) >= 3:
                METRICS['ratio'].labels(rig=rig, type='invalid', coin=cur_miner.coin, miner=cur_miner.name,
                                        miner_version=cur_miner.stats['ver']).set(cur_miner.stats['ar'][2])
            else:
                log.debug('Miner %s does not support tracking invalid shares', cur_miner.name)

            METRICS['total_hash'].labels(rig=rig, coin=cur_miner.coin, miner=cur_miner.name,
                                         miner_version=cur_miner.stats['ver']).set(cur_miner.total_hs)
            if cur_miner.is_gpu_miner():
                for index, bus_number in enumerate(cur_miner.stats['bus_numbers']):
                    try:
                        cur_gpu = gpu_by_bus_num[bus_number]
                        METRICS['gpu_hash'].labels(rig=rig, card=cur_gpu.card_index, model=cur_gpu.model,
                                                   brand=cur_gpu.brand, vendor=cur_gpu.vendor, coin=cur_miner.coin,
                                                   miner=cur_miner.name, miner_version=cur_miner.stats['ver']).set(cur_miner.stats['hs'][index])
                    except KeyError:
                        log.warning('Device detected with invalid bus number.  Assuming this is a non-GPU device')
                        METRICS['gpu_hash'].labels(rig=rig, card=index, model='unknown',
                                                   brand='unknown', vendor='unknown', coin=cur_miner.coin,
                                                   miner=cur_miner.name, miner_version=cur_miner.stats['ver']).set(cur_miner.stats['hs'][index])

            elif cur_miner.is_cpu_miner():
                for index, hs in enumerate(cur_miner.stats['hs']):
                    METRICS['cpu_hash'].labels(rig=rig, core=index, coin=cur_miner.coin,
                                               miner=cur_miner.name, miner_version=cur_miner.stats['ver']).set(hs)

        gpu_stats = read_gpu_stats()
        for index, cur_gpu in enumerate(gpu_by_index):
            labels = dict(rig=rig, card=cur_gpu.card_index, model=cur_gpu.model, brand=cur_gpu.brand,
                          vendor=cur_gpu.vendor)
            METRICS['gpu_coretemp'].labels(**labels).set(gpu_stats['temp'][index])
            METRICS['gpu_power'].labels(**labels).set(gpu_stats['power'][index])
            METRICS['gpu_fan'].labels(**labels).set(gpu_stats['fan'][index])
            METRICS['gpu_load'].labels(**labels).set(gpu_stats['load'][index])

            # Not all cards support tracking memory/junction temps.
            if 'mtemp' in gpu_stats and int(gpu_stats['mtemp'][index]) > 0:
                METRICS['gpu_memtemp'].labels(**labels).set(gpu_stats['mtemp'][index])
            if 'jtemp' in gpu_stats and int(gpu_stats['jtemp'][index]) > 0:
                METRICS['gpu_jtemp'].labels(**labels).set(gpu_stats['jtemp'][index])

        for index, cur_temp in enumerate(read_cpu_temp()):
            METRICS['cpu_temp'].labels(rig=rig, cpu=index).set(cur_temp)

        next_check = datetime.datetime.now() + datetime.timedelta(seconds=opts.refresh)
        log.info('Next metric refresh at %s', next_check.strftime('%Y-%d-%m %H:%M:%S'))
        sleep(opts.refresh)


if __name__ == '__main__':
    main()
