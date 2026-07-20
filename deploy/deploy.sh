#!/usr/bin/env bash
# Runs on the production server, invoked over SSH by .github/workflows/deploy.yml
# AFTER `git pull` has already happened (see the workflow — pull is kept out of
# this script deliberately: reading+running a script while it's being
# overwritten mid-execution by its own git pull is a real footgun).
set -euo pipefail

PROJECT_DIR="/opt/job_scraper/vyserion_job_scraper"
SERVICE_USER="jobscraper-svc"

cd "$PROJECT_DIR"

# ponytail: no setgid reliance — chmod -R strips it anyway, and the sudoers
# whitelist has no room for a `find ... g+s` entry. Correctness comes from
# re-chowning to jobscraper-svc:deployers on every deploy instead.
echo "==> fixing ownership/permissions after pull"
sudo chown -R jobscraper-svc:deployers "$PROJECT_DIR"
sudo chmod -R 750 "$PROJECT_DIR"
sudo chmod 600 "$PROJECT_DIR/.env"

echo "==> updating virtualenv dependencies"
sudo -u "$SERVICE_USER" /bin/bash -c "cd $PROJECT_DIR && $PROJECT_DIR/.venv/bin/pip install -r requirements.txt"

if grep -qi '^playwright' "$PROJECT_DIR/requirements.txt"; then
    echo "==> installing/updating playwright browser (chromium)"
    sudo -u "$SERVICE_USER" "$PROJECT_DIR/.venv/bin/playwright" install chromium

    # ponytail: dropped the sentinel-file skip. The sudo -u jobscraper-svc
    # touch it relied on isn't in the sudoers whitelist and deploy has no
    # other writable path into a 750 jobscraper-svc:deployers tree to fake
    # it from. install-deps chromium is already idempotent and passwordless
    # as root, so just run it every deploy instead of tracking "first run".
    echo "==> installing playwright system deps"
    sudo "$PROJECT_DIR/.venv/bin/playwright" install-deps chromium
fi

echo "==> rebuilding + restarting dashboard container (db untouched, no downtime)"
sudo docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d --no-deps --build dashboard

echo "==> deploy complete"
