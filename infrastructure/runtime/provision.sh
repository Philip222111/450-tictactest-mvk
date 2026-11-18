#!/usr/bin/env bash
set -euo pipefail
# Reuse bootstrap's fd 9, or take the same lock for a direct invocation.
if ! [[ /proc/self/fd/9 -ef /var/lock/tictactest-deployment.lock ]]; then
  exec 9>>/var/lock/tictactest-deployment.lock
fi
flock -x 9
atomic=/usr/local/lib/tictactest/atomic_runtime.py
temporary_files=()
cleanup() { for file in "${temporary_files[@]}"; do rm -f -- "$file"; done; }
trap cleanup EXIT
dnf install -y java-25-amazon-corretto-headless-1:25.0.5.0.9-1.amzn2023.1.x86_64 nginx-1:1.30.6-1.amzn2023.0.1.x86_64
ttyd_download=$(mktemp /tmp/tictactest-ttyd.XXXXXX)
temporary_files+=("$ttyd_download")
curl -fsSL https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 -o "$ttyd_download"
echo "8a217c968aba172e0dbf3f34447218dc015bc4d5e59bf51db2f2cd12b7be4f55  $ttyd_download" | sha256sum -c -
python3 "$atomic" file /usr/local/bin/ttyd "$ttyd_download" 755
id tictactest >/dev/null 2>&1 || useradd --system --no-create-home --shell /sbin/nologin tictactest
install -d -m 755 /opt/tictactest /opt/tictactest/releases
config=$(mktemp /opt/tictactest/.config.XXXXXX)
temporary_files+=("$config")
printf 'window.TICTACTEST = {consoleUrl: "%s/terminal/"};\n' "$BACKEND_ORIGIN" > "$config"
python3 "$atomic" file /opt/tictactest/config.js "$config" 644
# Disable the distribution default site; our virtual host owns port 80.
nginx_config=$(mktemp /etc/nginx/.tictactest-nginx.XXXXXX)
temporary_files+=("$nginx_config")
cat > "$nginx_config" <<'NGINX'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    include /etc/nginx/conf.d/*.conf;
}
NGINX
nginx -t -c "$nginx_config"
python3 "$atomic" file /etc/nginx/nginx.conf "$nginx_config" 644
nginx -t
systemctl daemon-reload
systemctl enable nginx tictactest amazon-ssm-agent
systemctl restart nginx
if [ -f /opt/tictactest/app.jar ]; then systemctl restart tictactest; fi
