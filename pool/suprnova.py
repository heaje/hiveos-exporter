from typing import Any
from .pool import Pool
import requests
import logging
import logging.handlers
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
import datetime

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class suprnova(Pool):
    @property
    def wallet(self):
        if not getattr(self, "_wallet", None):
            data = self._call("action=getuserstatus")
            self._wallet = data["username"]

        return self._wallet

    @property
    def pool_hashrate(self):
        data = self._call("action=getuserstatus")
        return data["hashrate"] * 1000, None

    @property
    def pool_balance(self):
        data = self._call("action=getuserbalance")
        return data["confirmed"] + data["unconfirmed"], None

    @property
    def worker_hashrates(self):
        data = self._call("action=getuserworkers")
        for worker_info in data:
            # In case the worker name somehow includes a "."
            yield self._get_worker_name(worker_info["username"]), worker_info["hashrate"] * 1000, None

    @property
    def pool_ratio(self):
        data = self._call("action=getuserstatus")
        yield "accepted", data["shares"]["valid"], None
        yield "rejected", data["shares"]["invalid"], None

    @property
    def worker_ratios(self):
        # The Suprnova API does not provide information on worker invalid shares
        data = self._call("action=getuserworkers")
        for worker_info in data:
            worker_name = self._get_worker_name(worker_info["username"])
            yield worker_name, "accepted", worker_info["shares"], None

    @property
    def pool_rewards(self):
        data = self._call("action=getusertransactions")
        for cur_trx in data["transactions"]:
            if cur_trx["type"] == "Credit":
                yield cur_trx["amount"], self._timestamp_to_epoch(cur_trx["timestamp"])

    @property
    def pool_payouts(self):
        data = self._call("action=getusertransactions")
        for cur_trx in data["transactions"]:
            if cur_trx["type"] == "Debit_AP":
                yield cur_trx["amount"], self._timestamp_to_epoch(cur_trx["timestamp"])

    def __init__(self, api_key: str, coin: str, **kwargs) -> None:
        self._coin = coin.upper()
        endpoint = "https://{}.suprnova.cc/index.php?page=api&api_key={}&".format(self._coin.lower(), api_key)
        super().__init__(base_endpoint=endpoint, coin=self._coin, pool_name="suprnova.cc")

    def _get_worker_name(self, username: str):
        # In case the worker name somehow includes a "."
        return ".".join(username.split(".")[1:])

    def _timestamp_to_epoch(self, timestamp_str, format="%Y-%m-%d %H:%M:%S") -> float:
        converted_time = datetime.datetime.strptime(timestamp_str, format)
        return converted_time.timestamp()

    def _call(self, uri: str = "", **kwargs) -> Any:
        try:
            data = super()._call(uri, verify=False, **kwargs)
        except requests.exceptions.HTTPError as e:
            if str(e).startswith("401 "):
                log.error(
                    "Received HTTP 401 unauthorized talking to Supernova.  This means the API key is wrong, or too many HTTP requests have occurred."
                )
                raise

        return data[uri.replace("action=", "")]["data"]
