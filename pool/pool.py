from typing import Any
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
import requests
import requests_cache
import ssl
import logging
import logging.handlers

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
requests_cache.install_cache(backend="memory", expire_after=60)


class Pool:
    @property
    def wallet(self) -> str:
        if not self._wallet:
            raise NotImplementedError

        return self._wallet

    @property
    def coin(self) -> str:
        if not self._coin:
            raise NotImplementedError

        return self._coin

    @property
    def pool(self) -> str:
        if not self._pool:
            raise NotImplementedError

        return self._pool

    def __init__(self, base_endpoint: str, wallet: str = None, coin: str = None, pool_name: str = None) -> None:
        self._base_url = base_endpoint
        self._coin = coin
        self._wallet = wallet
        self._pool = pool_name

    def set_metrics(
        self,
        hashrate_metrics: GaugeMetricFamily,
        ratio_metrics: CounterMetricFamily,
        balance_metrics: CounterMetricFamily,
        reward_metrics: GaugeMetricFamily,
    ) -> None:
        self._set_balance_metrics(balance_metrics)
        self._set_worker_metrics(hashrate_metrics, ratio_metrics)
        self._set_hashrate_metrics(hashrate_metrics, ratio_metrics)
        self._set_reward_metrics(reward_metrics)

    def _set_hashrate_metrics(self) -> None:
        raise NotImplementedError

    def _set_worker_metrics(self) -> None:
        raise NotImplementedError

    def _set_balance_metrics(self) -> None:
        raise NotImplementedError

    def _set_reward_metrics(self) -> None:
        raise NotImplementedError

    def _call(self, uri: str = "", **kwargs) -> Any:
        if not getattr(self, "_api", None):
            self._api = requests.Session()

        full_url = "{}{}".format(self._base_url, uri)
        try:
            response = self._api.get(full_url, **kwargs)
            response.raise_for_status()
        except ssl.SSLCertVerificationError as e:
            log.warn('SSL Cert error calling {} -> {}'.format(full_url, str(e)))
        except Exception:
            # Add more intelligent handling
            raise

        try:
            return response.json()
        except Exception:
            # Add more intelligent handling
            raise
