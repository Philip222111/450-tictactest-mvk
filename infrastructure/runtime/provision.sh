#!/usr/bin/env bash
set -euo pipefail
dnf install -y java-25-amazon-corretto-headless-1:25.0.5.0.9-1.amzn2023.1.x86_64 nginx-1:1.30.6-1.amzn2023.0.1.x86_64
curl -fsSL https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 -o /tmp/ttyd
echo '8a217c968aba172e0dbf3f34447218dc015bc4d5e59bf51db2f2cd12b7be4f55  /tmp/ttyd' | sha256sum -c -
install -m 755 /tmp/ttyd /usr/local/bin/ttyd
id tictactest >/dev/null 2>&1 || useradd --system --no-create-home --shell /sbin/nologin tictactest
install -d -m 755 /opt/tictactest /opt/tictactest/releases
printf 'window.TICTACTEST = {consoleUrl: "%s/terminal/"};\n' "$BACKEND_ORIGIN" > /opt/tictactest/config.js
# Disable the distribution default site; our virtual host owns port 80.
cat > /etc/nginx/nginx.conf <<'NGINX'
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
nginx -t
systemctl daemon-reload
systemctl enable nginx tictactest amazon-ssm-agent
systemctl restart nginx
if [ -f /opt/tictactest/app.jar ]; then systemctl restart tictactest; fi
