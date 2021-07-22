# Trend Micro Apex Central collector

## Using Collector Server SDK

## Build and upload

Update `metadata.json` with proper version description and number (if try to upload any already existing version will fail):

```bash
collector-cli upload
```

### Save

```bash
docker save 837131528613.dkr.ecr.us-east-1.amazonaws.com/collectors/trendmicro:<version> | gzip > collector-trendmicro-docker-image-<version>.tgz
```

### Run

Go to proper Collector Server environment and follow the instruction described at [Devo documentation website](https://docs.devo.com):
* [Integration/demo](https://collector-server.data.devo.com/home)
* [Production](https://https://collector-server-prod.data.devo.com/)

## Using Docker

### Build

```bash
docker build \
--compress \
--force-rm \
--no-cache \
--tag docker.devo.internal/collectors/trendmicro:<version> \
.
```

### Save

```bash
docker save docker.devo.internal/collectors/trendmicro:<version> | gzip > collector-trendmicro-docker-image-<version>.tgz
```

### Load

```bash
gunzip -c collector-trendmicro-docker-image-<version>.tgz | docker load
```
### Run

```bash
docker run \
--name collector-trendmicro \
--userns-remap="root:devo" \
--volume $PWD/certs:/devo-collector/certs \
--volume $PWD/credentials:/devo-collector/credentials \
--volume $PWD/config:/devo-collector/config \
--volume $PWD/state:/devo-collector/state \
--env CONFIG_FILE=config.yaml \
--rm \
--interactive \
--tty \
docker.devo.internal/collectors/trendmicro:<version>
```

## Trend Micro Apex Central Info

### Api Reference
https://automation.trendmicro.com/apex-central/api