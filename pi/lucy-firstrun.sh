#!/usr/bin/env bash
# Raspberry Pi first-run hook (called from boot-partition firstrun.sh).
# Side effects: writes /etc/lucy/flash.env, enables SSH, schedules lucy-first-boot.service.
set -euo pipefail

BOOT=""
for candidate in /boot/firmware /boot; do
  if [[ -d "$candidate/lucy" ]]; then
    BOOT="$candidate"
    break
  fi
done
[[ -n "$BOOT" ]] || { echo "lucy-firstrun: no boot/lucy directory" >&2; exit 1; }

LUCY_DIR="$BOOT/lucy"
ENV_SRC="$LUCY_DIR/lucy-flash.env"
ENV_DST=/etc/lucy/flash.env

mkdir -p /etc/lucy /usr/local/lib/lucy
if [[ -f "$ENV_SRC" ]]; then
  install -m 0600 "$ENV_SRC" "$ENV_DST"
fi

set -a
# shellcheck disable=SC1090
[[ -f "$ENV_DST" ]] && source "$ENV_DST"
set +a

if [[ -n "${LUCY_HOSTNAME:-}" ]]; then
  echo "$LUCY_HOSTNAME" >/etc/hostname
  hostnamectl set-hostname "$LUCY_HOSTNAME" 2>/dev/null || true
  sed -i "s/127.0.1.1.*/127.0.1.1\t${LUCY_HOSTNAME}/" /etc/hosts 2>/dev/null || true
fi

if [[ "${LUCY_ENABLE_SSH:-1}" == "1" ]]; then
  systemctl enable ssh 2>/dev/null || systemctl enable sshd 2>/dev/null || true
fi

if [[ -n "${LUCY_SSH_KEY:-}" && -n "${LUCY_USER:-}" ]]; then
  user_home="$(getent passwd "$LUCY_USER" | cut -d: -f6 || true)"
  if [[ -n "$user_home" ]]; then
    install -d -m 0700 -o "$LUCY_USER" -g "$LUCY_USER" "$user_home/.ssh"
    auth_keys="$user_home/.ssh/authorized_keys"
    if [[ ! -f "$auth_keys" ]] || ! grep -Fq "$LUCY_SSH_KEY" "$auth_keys" 2>/dev/null; then
      echo "$LUCY_SSH_KEY" >>"$auth_keys"
      chown "$LUCY_USER:$LUCY_USER" "$auth_keys"
      chmod 0600 "$auth_keys"
    fi
  fi
fi

for script in first-boot.sh install-wifi-portal.sh wifi-watch.sh; do
  [[ -f "$LUCY_DIR/$script" ]] && install -m 0755 "$LUCY_DIR/$script" "/usr/local/lib/lucy/$script"
done
for unit in lucy-first-boot.service lucy-wifi-portal.service lucy-connect-watch.service lucy-connect-watch.timer; do
  if [[ -f "$LUCY_DIR/$unit" ]]; then
    cp "$LUCY_DIR/$unit" "/etc/systemd/system/$unit"
    install -m 0644 "$LUCY_DIR/$unit" "/usr/local/lib/lucy/$unit"
  fi
done

systemctl daemon-reload
systemctl enable lucy-first-boot.service
systemctl start lucy-first-boot.service || true

echo "lucy-firstrun: staged first-boot install"
