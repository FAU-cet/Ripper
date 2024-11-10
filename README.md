# Ripper

Collect Information such as Usage and Power Limits and visualize them on Grafana.

## Usage

1. Create `scraper/.env` for ssh access to the nodes
    ```
    USER=<username>
    PASS=<password>
    ```
2. Adjust `scraper/config.json` based on your needs
3. `./up.sh`

## Notes

You might need to change the default dashboard (or create your own) if you use a different node setup.

Use `./rebuild.sh` if you want to start a Ripper environment from scratch.

## Development TODO

- [X] Setup InfluxDB
- [X] Setup bare-bones Grafana
- [X] Setup scraper
- [X] Interface Grafana <-> InfluxDB
- [X] Interface python-scraper <-> InfluxDB
- [ ] Scrape data from nodes
- [ ] Create default dashboard layout
