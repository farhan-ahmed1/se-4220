#!/bin/bash
# Cloud-init style startup script for the gallery VM.
# Rendered by Terraform's templatefile() -- $${...} placeholders are substituted
# at plan time, not at boot time. (The doubled $$ is so this very comment
# isn't itself parsed as a template variable.)
set -euo pipefail

LOG=/var/log/photogallery-startup.log
exec > >(tee -a "$LOG") 2>&1
echo "=== photogallery startup script: $(date -u) ==="

export DEBIAN_FRONTEND=noninteractive

# 1. System packages
apt-get update -y
apt-get install -y python3-venv python3-pip default-mysql-client unzip curl

# 2. Pull app source + schema from the deploy bucket (uses the VM's attached SA).
APP_DIR=/opt/photogallery
mkdir -p "$APP_DIR"
gsutil cp "gs://${deploy_bucket}/${app_object}"    /tmp/app.zip
gsutil cp "gs://${deploy_bucket}/${schema_object}" /tmp/schema.sql
unzip -oq /tmp/app.zip -d "$APP_DIR"

# 3. Python venv + dependencies
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# 4. Initialize DB schema (idempotent; CREATE TABLE IF NOT EXISTS).
mysql \
  --host="${db_host}" \
  --user="${db_user}" \
  --password="${db_password}" \
  --connect-timeout=30 \
  "${db_name}" < /tmp/schema.sql

# 5. systemd service: gunicorn on port 80, restart on failure, start on boot.
cat >/etc/systemd/system/photogallery.service <<EOF
[Unit]
Description=Photogallery Flask app (gunicorn)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment="DB_HOSTNAME=${db_host}"
Environment="DB_USERNAME=${db_user}"
Environment="DB_PASSWORD=${db_password}"
Environment="DB_NAME=${db_name}"
Environment="GCS_BUCKET=${gcs_photo_bucket}"
Environment="FLASK_SECRET_KEY=${flask_secret_key}"
ExecStart=$APP_DIR/.venv/bin/gunicorn -b 0.0.0.0:80 --workers 2 --threads 4 --timeout 60 main:app
Restart=on-failure
RestartSec=3
# gunicorn needs CAP_NET_BIND_SERVICE to listen on :80 as a non-root user;
# easier for a class project to just run as root, which is what System default is.

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now photogallery.service

echo "=== photogallery startup script done: $(date -u) ==="
