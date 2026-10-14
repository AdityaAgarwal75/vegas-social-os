#!/usr/bin/env bash
# Separated root broker; the public application remains vegas-social.
set -Eeuo pipefail
umask 077
(( EUID == 0 )) || { echo 'Run the broker installer as root'; exit 1; }
VSO_SOURCE=$(cd "$(dirname "$0")/.." && pwd)
VSO_UID=$(id -u vegas-social)
install -d -o root -g root -m 0755 /usr/local/lib/vegas-social-admin
install -o root -g root -m 0644 "$VSO_SOURCE/vso/admin_broker.py" /usr/local/lib/vegas-social-admin/broker.py
install -d -o root -g root -m 0700 /var/lib/vegas-social-admin
cat > /etc/systemd/system/vegas-social-admin.service <<UNIT
[Unit]
Description=Vegas Social OS private owner administrator broker
After=local-fs.target
[Service]
User=root
Group=vegas-social
WorkingDirectory=/usr/local/lib/vegas-social-admin
Environment=VSO_ADMIN_UID=$VSO_UID
Environment=PYTHONNOUSERSITE=1
ExecStart=/usr/bin/python3 -I /usr/local/lib/vegas-social-admin/broker.py serve
Restart=on-failure
RestartSec=3
RuntimeDirectory=vegas-social-admin
RuntimeDirectoryMode=0750
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=1024
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now vegas-social-admin.service >/dev/null
# Never print the TOTP enrollment secret. Issue a private owner link separately:
# python3 -I /usr/local/lib/vegas-social-admin/broker.py enrollment-link https://YOUR-DOMAIN
printf '%s\n' 'Private Unix broker installed. Owner enrollment is required for dangerous operations.'
