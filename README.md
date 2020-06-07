# Docker client GWS

## Build the docker image

```sh
docker build -t gws-docker .
```

```sh
cp .env.sample .env
# Add your GWS API Key
```

## Run the docker image

```sh
docker run --rm --env-file .env gws-docker
```

## Cronjob

```sh
0 * * * * docker run --rm --env-file /home/diogopms/gws-client-api-test/.env gws-docker > /dev/null 2>&1
```
