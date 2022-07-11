# Mining Exporters
Prometheus exporters for Cryptocurrency mining.
* HiveOS
* Mining Pools
    * Hiveon
    * suprnova.cc

## HiveOS Supported Functionality:
Exporter listens on port 10101 by default.

* Multiple miners
* Multiple coins (across different miners)
* Nvidia & AMD stats (Temps / Fan Speeds / etc.)

**Known Limitations:**
* Does not currently support multi-algorithm mining configurations within a single miner (e.g. ETH + ZIL, ETH + TON, etc.)

## Pool Supported Functionality:
Exporter listens on port 10102 by default.

* Total pool hashrate
* Per worker hashrate
* Pool rewards
* Pool payouts
* Pool share counts (Accepted / Rejected)

### Pool Exporter Configuration
Examples of configuration for the supported Pool Exporters can be found in [etc/pools.yml](etc/pools.yml).  The pool exporter will not do anything useful until it has been configured.

## Installation
Installation puts all files under /opt/hiveos-exporter.

```bash
sudo git clone https://github.com/heaje/hiveos-exporter.git
cd hiveos-exporter
sudo apt install python3-prometheus-client python3-requests-cache
sudo make install

# For HiveOS Exporter
sudo systemctl enable hiveos-exporter
sudo systemctl start hiveos-exporter

# For Pool Exporter.  Configuration REQUIRED.
sudo systemctl enable pool-exporter
sudo systemctl start pool-exporter
```

## Uninstall
```
sudo apt remove python3-prometheus-client python3-requests-cache
sudo make uninstall
```

## Acknowledgements
The HiveOS exporter was originally forked from [esille/hiveos-prometheus](https://github.com/esille/hiveos-prometheus), but has been almost entirely re-written to provide additional functionalities.

## Compatibility between versions
These exporters are very much a work in progress at the moment.  I do not expect that there will be changes to metric names or labels at this point, but please do be aware that they could change.  I'm making no promises on that right now.

## Donations
If you found these scripts helpful and would like to donate to the author, you can do so at the following addresses.  This does not provide any guarantee of future support.

ETH: 0xDcd7c971Fe679569CAeaB8A91f7a1f291B527F21

BTC: 1BPvBqaMjqWVHrmeMQTrZqADZr5n4ML5GA

RVN: RPq85qKtLg8dgrsGPicQrBpLVgR4YU4txg