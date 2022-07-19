#!/usr/bin/python3

import argparse
import importlib
import logging
import pathlib
import sys
from time import sleep
from typing import List

import yaml
from prometheus_client import REGISTRY, start_http_server
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily

log = None


class PoolCollector:
    _hashrate_tags = ("wallet", "coin", "pool", "worker")
    _balance_tags = ("wallet", "coin", "pool", "type")
    _ratio_tags = ("wallet", "coin", "pool", "type", "worker")
    _reward_tags = _balance_tags

    _pool_list = []

    def __init__(self, pool_config: dict, refresh_rate) -> None:
        sys.path.append("{}/../".format(pathlib.Path(__file__).parent.resolve()))
        for pool_name, instances in pool_config.items():
            module = importlib.import_module("pool.{}".format(pool_name))
            klass = getattr(module, pool_name)
            for cur_instance in instances:
                if "refresh_interval" not in cur_instance:
                    cur_instance["refresh_interval"] = refresh_rate
                self._pool_list.append(klass(**cur_instance))

    def collect(self):
        log.info("Collecting pool metrics")
        # hashrate, balance, ratio, reward = self._gen_metric_familes()
        hashrate = GaugeMetricFamily(name="pool_hashrate", documentation="Pool hashrate in H/s",
                                     labels=self._hashrate_tags)
        balance = CounterMetricFamily(name="pool_balance", documentation="Pool coin balance",
                                      labels=self._balance_tags)
        ratio = CounterMetricFamily(name="pool_ratio", documentation="Share acceptance counters",
                                    labels=self._ratio_tags)
        reward = GaugeMetricFamily(name="pool_reward", documentation="Rewards from pool", labels=self._reward_tags)

        for cur_pool in self._pool_list:
            log.debug('Collecting metrics for pool "{}"'.format(cur_pool.__class__.__name__))

            # Default pool hashrate / ratio metrics
            pool_hashrate, hashrate_timestamp = cur_pool.pool_hashrate
            hashrate.add_metric(value=pool_hashrate, timestamp=hashrate_timestamp,
                                labels=[cur_pool.wallet, cur_pool.coin, cur_pool.pool, "total"])
            for ratio_type, ratio_value, timestamp in cur_pool.pool_ratio:
                ratio.add_metric(value=ratio_value, timestamp=timestamp,
                                 labels=[cur_pool.wallet, cur_pool.coin, cur_pool.pool, ratio_type, "total"])

            # Default worker hashrate / ratio metrics
            for worker_name, worker_hashrate, worker_hashrate_timestamp in cur_pool.worker_hashrates:
                hashrate.add_metric(
                    value=worker_hashrate, timestamp=worker_hashrate_timestamp,
                    labels=[cur_pool.wallet, cur_pool.coin, cur_pool.pool, worker_name]
                )

            for worker_name, ratio_type, ratio_value, timestamp in cur_pool.worker_ratios:
                ratio.add_metric(
                    value=ratio_value, timestamp=timestamp,
                    labels=[cur_pool.wallet, cur_pool.coin, cur_pool.pool, ratio_type, worker_name]
                )

            # Default pool balance metrics
            pool_balance, balance_timestamp = cur_pool.pool_balance
            balance.add_metric(value=pool_balance, timestamp=balance_timestamp, labels=[cur_pool.wallet, cur_pool.coin,
                               cur_pool.pool, "unpaid"])

            # Default pool reward metrics
            for pool_reward, pool_reward_timestamp in cur_pool.pool_rewards:
                reward.add_metric(value=pool_reward, timestamp=pool_reward_timestamp,
                                  labels=[cur_pool.wallet, cur_pool.coin, cur_pool.pool, "reward"])

            # Default pool payout metrics
            for pool_payout, pool_payout_timestamp in cur_pool.pool_payouts:
                reward.add_metric(value=pool_payout, timestamp=pool_payout_timestamp,
                                  labels=[cur_pool.wallet, cur_pool.coin, cur_pool.pool, "payout"])

        yield hashrate
        yield balance
        yield ratio
        yield reward

    def describe(self) -> List:
        # return self._gen_metric_familes()
        return []


def get_config(path) -> dict:
    with open(path, "r") as config_file:
        config = yaml.safe_load(config_file)

    if not config:
        config = {}
    return config


def get_opts() -> argparse.Namespace:
    default_config_path = "{}/../etc/pools.yml".format(pathlib.Path(__file__).parent.resolve())

    parser = argparse.ArgumentParser(description="HiveOS Prometheus exporter",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-l", "--log_level", dest="log_level", help="The logging level", default="info")
    parser.add_argument("-p", "--port", dest="port", help="The listening port for the exporter", default=10102,
                        type=int)
    parser.add_argument("-c", "--config", dest="config", help="Path to the config file", default=default_config_path)
    parser.add_argument("-r", "--refresh", dest="refresh",
                        help="The default Pool API refresh rate.  Has no effect if refresh rate is configured via configuration file.",
                        default=55)
    return parser.parse_args()


def init_logging(level) -> None:
    global log
    all_loggers = [__name__, "pool"]
    log = logging.getLogger(__name__)
    log.addHandler(logging.NullHandler())
    log_level_constant = getattr(logging, level.upper())
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    for cur_logger in all_loggers:
        logging.getLogger(cur_logger).addHandler(console_handler)
        logging.getLogger(cur_logger).setLevel(log_level_constant)


def main() -> None:
    opts = get_opts()
    init_logging(opts.log_level)
    config = get_config(opts.config)
    if not config:
        log.error("No pools are configured for monitoring.  Quitting.")
        sys.exit(1)

    log.info("Starting HTTP server on port {}".format(opts.port))
    start_http_server(opts.port)

    REGISTRY.register(PoolCollector(config, refresh_rate=opts.refresh))
    while True:
        sleep(3600)


if __name__ == "__main__":
    main()
