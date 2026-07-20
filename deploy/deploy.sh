#!/usr/bin/env bash
# Runs on the production server, invoked over SSH by .github/workflows/deploy.yml
# AFTER `git pull` has already happened (see the workflow — pull is kept out of
# this script deliberately: reading+running a script while it's being
# overwritten mid-execution by its own git pull is a real footgun).
set -euo pipefail

PROJECT_DIR="/opt/job_scraper/vyserion_job_scraper"
SERVICE_USER="deployers"

cd "$PROJECT_DIR"

echo "==> fixing ownership/permissions after pull"
sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "$PROJECT_DIR"
sudo chmod 750 "$PROJECT_DIR"
sudo chmod 600 "$PROJECT_DIR/.env"

echo "==> updating virtualenv dependencies"
sudo -u "$SERVICE_USER" "$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

if grep -qi '^playwright' "$PROJECT_DIR/requirements.txt"; then
    echo "==> installing/updating playwright browser (chromium)"
    sudo -u "$SERVICE_USER" "$PROJECT_DIR/.venv/bin/playwright" install chromium

    # ponytail: sentinel file, not a live dependency check — if system libs get
    # removed/changed outside this script, delete the marker to force a re-check.
    DEPS_MARKER="$PROJECT_DIR/.venv/.playwright-deps-ok"
    if [ ! -f "$DEPS_MARKER" ]; then
        echo "==> installing playwright system deps (first run only)"
        sudo "$PROJECT_DIR/.venv/bin/playwright" install-deps chromium
        sudo -u "$SERVICE_USER" touch "$DEPS_MARKER"
    else
        echo "==> playwright system deps already present, skipping"
    fi
fi

echo "==> rebuilding + restarting dashboard container (db untouched, no downtime)"
sudo docker compose up -d --build --no-deps dashboard

echo "==> deploy complete"
