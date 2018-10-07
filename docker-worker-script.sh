#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

pipenv run celery -A ava_rememberme.tasks worker --loglevel INFO -E
