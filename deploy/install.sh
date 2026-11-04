#!/usr/bin/env bash
set -euo pipefail
echo 'Obsolete installer: use scripts/deploy_cloud.py and docs/deployment.md' >&2
exit 1
cd "$(dirname "$0")/.."
jars=(artifacts/*.jar)
if [ "${#jars[@]}" -ne 1 ] || [ ! -f "${jars[0]}" ]; then
  echo "Expected exactly one release JAR in artifacts" >&2
  exit 1
fi
(cd artifacts && sha256sum -c "$(basename "${jars[0]}").sha256")
dnf install -y python3 java-25-amazon-corretto-headless rsync
id tictactest >/dev/null 2>&1 || useradd --system --no-create-home --shell /sbin/nologin tictactest
install -d /opt/tictactest/web
changed=false
copy_changed() {
  if ! cmp -s "$1" "$2"; then
    install -m 644 "$1" "$2"
    changed=true
  fi
}
copy_changed "${jars[0]}" /opt/tictactest/app.jar
copy_changed web/server.py /opt/tictactest/web/server.py
copy_changed web/index.html /opt/tictactest/web/index.html
copy_changed deploy/tictactest.service /etc/systemd/system/tictactest.service
systemctl daemon-reload
systemctl enable tictactest.service
if $changed; then systemctl restart tictactest.service; else systemctl start tictactest.service; fi
for attempt in {1..30}; do
  if curl -fsS http://127.0.0.1:8080/health; then exit 0; fi
  sleep 2
done
journalctl -u tictactest.service -n 30 --no-pager
exit 1
