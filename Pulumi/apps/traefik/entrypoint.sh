#!/bin/sh
set -e

envsubst < config/routers.yml.tmpl > dynamic/01-routers.yml
envsubst < config/services.yml.tmpl > dynamic/00-services.yml

exec traefik "$@"