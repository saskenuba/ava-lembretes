#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

pipenv run flask create-db
pipenv run gunicorn -w 1 --bind=0.0.0.0 ava_rememberme:app
