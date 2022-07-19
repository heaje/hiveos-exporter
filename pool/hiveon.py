import datetime
from .pool import Pool


class hiveon(Pool):

    @property
    def pool_hashrate(self):
        data = self._call()
        return data["hashrate"], None

    @property
    def pool_balance(self):
        data = self._call("/billing-acc")
        return data["totalUnpaid"], None

    @property
    def worker_hashrates(self):
        data = self._call("/workers")
        for worker_name, worker_info in data["workers"].items():
            yield worker_name, worker_info.get("hashrate", 0), None

    @property
    def pool_ratio(self):
        data = self._call()
        timestamp = self._convert_timestamp_to_epoch(data["sharesStatusStats"]["lastShareDt"])
        yield "accepted", data["sharesStatusStats"]["validCount"], timestamp
        yield "rejected", data["sharesStatusStats"]["staleCount"], timestamp

    @property
    def worker_ratios(self):
        data = self._call("/workers")
        for worker_name, worker_info in data["workers"].items():
            timestamp = self._convert_timestamp_to_epoch(worker_info["sharesStatusStats"]["lastShareDt"])
            yield worker_name, "accepted", worker_info["sharesStatusStats"]["validCount"], timestamp
            yield worker_name, "rejected", worker_info["sharesStatusStats"]["staleCount"], timestamp

    @property
    def pool_rewards(self):
        data = self._call("/billing-acc")

        for earned in data["earningStats"]:
            yield earned["reward"], self._convert_timestamp_to_epoch(earned["timestamp"])

    @property
    def pool_payouts(self):
        data = self._call("/billing-acc")
        if data["succeedPayouts"]:
            for index in data["succeedPayouts"]:
                yield index["amount"], self._convert_timestamp_to_epoch(index["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")

    def __init__(self, wallet: str, coin: str, **kwargs) -> None:
        # Remove the "0x" on the fly if the user included it
        if wallet.startswith("0x"):
            wallet = wallet[2:]

        wallet = wallet.lower()
        coin = coin.upper()
        endpoint = "https://hiveon.net/api/v1/stats/miner/{wallet}/{coin}".format(wallet=wallet, coin=coin)
        super().__init__(base_endpoint=endpoint, wallet=wallet, coin=coin, pool_name="hiveon.net")

    def _convert_timestamp_to_epoch(self, timestamp_str, format="%Y-%m-%dT%H:%M:%SZ") -> float:
        converted_time = datetime.datetime.strptime(timestamp_str, format)
        return converted_time.timestamp()
