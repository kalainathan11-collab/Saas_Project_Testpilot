#!/usr/bin/env bash
# One-command deploy for TestPilot on a fresh Ubuntu/Debian VPS (run as root).
#
#   curl -fsSL https://raw.githubusercontent.com/kalainathan11-collab/Saas_Project_Testpilot/main/deploy/deploy.sh | DOMAIN=solarsbs.sbs bash
#
# Idempotent: re-running pulls the latest code, rebuilds and restarts. Secrets are generated
# once into /opt/testpilot/.env.production (chmod 600) and reused on later runs.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/kalainathan11-collab/Saas_Project_Testpilot.git}"
BRANCH="${BRANCH:-main}"
APP_DIR="${APP_DIR:-/opt/testpilot}"
DOMAIN="${DOMAIN:-}"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "run as root"

# --- 1. Docker ---------------------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  log "Installing Docker"
  curl -fsSL https://get.docker.com | sh
fi
docker compose version >/dev/null 2>&1 || die "docker compose plugin missing"
systemctl enable --now docker >/dev/null 2>&1 || true

# --- 2. Code -----------------------------------------------------------------------------
command -v git >/dev/null 2>&1 || { apt-get update -y && apt-get install -y git; }
if [ -d "$APP_DIR/.git" ]; then
  log "Updating code in $APP_DIR"
  git -C "$APP_DIR" fetch --quiet origin "$BRANCH"
  git -C "$APP_DIR" reset --hard "origin/$BRANCH"
else
  log "Cloning $REPO_URL"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

# --- 3. Configuration / secrets ----------------------------------------------------------
ENV_FILE=".env.production"
if [ ! -f "$ENV_FILE" ]; then
  [ -n "$DOMAIN" ] || die "first run needs DOMAIN, e.g. DOMAIN=solarsbs.sbs"
  log "Generating $ENV_FILE with random secrets"
  umask 077
  cat > "$ENV_FILE" <<ENV
DOMAIN=$DOMAIN
POSTGRES_USER=testpilot
POSTGRES_DB=testpilot
POSTGRES_PASSWORD=$(openssl rand -hex 24)
SECRET_KEY=$(openssl rand -base64 48 | tr -d '\n=+/')
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
ENV
fi
chmod 600 "$ENV_FILE"
# shellcheck disable=SC1090
DOMAIN="$(grep -E '^DOMAIN=' "$ENV_FILE" | cut -d= -f2-)"

# --- 4. Firewall (only SSH + web) --------------------------------------------------------
if command -v ufw >/dev/null 2>&1; then
  log "Configuring firewall (22, 80, 443)"
  ufw allow 22/tcp >/dev/null
  ufw allow 80/tcp >/dev/null
  ufw allow 443/tcp >/dev/null
  ufw allow 443/udp >/dev/null
  ufw --force enable >/dev/null
fi

# --- 5. DNS sanity check (certificate issuance needs it) --------------------------------
MY_IP="$(curl -fsS -4 https://api.ipify.org || true)"
DNS_IP="$(getent ahostsv4 "$DOMAIN" | awk '{print $1; exit}' || true)"
if [ -n "$MY_IP" ] && [ "$DNS_IP" != "$MY_IP" ]; then
  printf '\n\033[1;33mWARNING: %s resolves to %s but this server is %s.\n' "$DOMAIN" "${DNS_IP:-nothing}" "$MY_IP"
  printf 'HTTPS certificates will fail until the DNS A record points here.\033[0m\n'
fi

# --- 6. Build & start --------------------------------------------------------------------
log "Building and starting the stack"
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml up -d --build

log "Waiting for the API to become healthy"
for _ in $(seq 1 60); do
  if docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml exec -T backend \
      python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3)" \
      >/dev/null 2>&1; then
    ok=1; break
  fi
  sleep 3
done
[ "${ok:-0}" = 1 ] || { docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml logs --tail=50 backend; die "backend did not become healthy"; }

docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml ps
printf '\n\033[1;32mDeployed.\033[0m  https://%s\n' "$DOMAIN"
echo "Secrets are in $APP_DIR/$ENV_FILE (root only). Back up the 'postgres_data' volume regularly."
