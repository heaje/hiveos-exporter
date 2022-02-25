# Push stats from hiveos to prometheus
Originally forked from [tomcsi/hiveos-prometheus](https://github.com/tomcsi/hiveos-prometheus), but has been almost entirely re-written to provide additional functionalities.

## Supports:
* Multiple miners
* Multiple coins
* Nvidia & AMD stats

## Known Limitations:
* Does not currently support multi-algorithm mining configurations (e.g. ETH + ZIL, ETH + TON, etc.)

## Installation
```bash
sudo git clone https://github.com/heaje/hiveos-prometheus.git
cd hiveos-prometheus
sudo apt install python3-prometheus-client
sudo make install
sudo systemctl enable hiveos-exporter
sudo systemctl start hiveos-exporter
```

## Uninstall
```
sudo apt remove python3-prometheus-client
sudo make uninstall
```