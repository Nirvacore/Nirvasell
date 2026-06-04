# Deploying nirva.sell

Production-ready Docker deploy. ~10 min to your-own-domain.

---

## What you get

- Multi-stage Docker image (~400 MB, no compilers in the runtime layer)
- Non-root container, healthcheck, memory caps
- nginx / Caddy reverse proxy with HTTPS (Let's Encrypt)
- Daily backups of all per-user SQLite DBs
- Telegram alert on backup success/failure
- External uptime probe you can wire into UptimeRobot

---

## TL;DR (small VPS)

```bash
# 1. SSH into a Linux box (Ubuntu 22.04+, 1 vCPU, 2 GB RAM minimum)
git clone https://github.com/YOURNAME/nirva.sell.git
cd nirva.sell

# 2. Configure
cp .env.example .env
nano .env                      # fill in what you need

# 3. Run
docker compose up -d

# 4. Verify
./scripts/healthcheck.sh http://127.0.0.1:8501
docker compose logs -f
```

The app is now at `http://YOUR-IP:8501`. **DO NOT** expose this directly to
the internet — see "HTTPS" below.

---

## Alternatives (no VPS)

### Streamlit Cloud (free, fastest)

```bash
git push -u origin main          # to your GitHub repo
# open https://share.streamlit.io → New app → pick repo, branch=main, main=app.py
# Advanced settings → secrets → paste ANTHROPIC_API_KEY etc.
```

Live at `https://YOURAPP.streamlit.app`. Free tier is plenty for a small
shop; per-user DBs persist on Streamlit's storage.

### Cloudflare Tunnel (your-machine → public URL)

For dev / demo from your laptop:

```bash
brew install cloudflared
cloudflared tunnel login
cloudflared tunnel create nirva
cloudflared tunnel route dns nirva nirva.yourdomain.com
docker compose up -d
cloudflared tunnel run --url http://localhost:8501 nirva
```

No port forwarding needed.

---

## Requirements (self-host)

| | Minimum | Recommended |
|---|---|---|
| **CPU** | 1 vCPU | 2 vCPU |
| **RAM** | 1 GB | 2 GB (rembg + vision spike to ~600 MB) |
| **Disk** | 5 GB | 20 GB (room for images + backups) |
| **OS** | Linux with Docker 20+ | Ubuntu 22.04 LTS |

Tested on: DigitalOcean $6/mo droplet, Hetzner CX11 ($4.50/mo), AWS Lightsail $5/mo.

---

## Step 1 — Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# log out + back in for the group change to take effect
```

---

## Step 2 — Get the code + configure

```bash
git clone https://github.com/YOURNAME/nirva.sell.git
cd nirva.sell
cp .env.example .env
```

Edit `.env`. Bare minimum to start:

```ini
# leave ANTHROPIC_API_KEY empty — each user pastes their own in the UI
PROMPTPAY_ID=0812345678
PROMPTPAY_NAME=Your Shop
```

Everything else is optional. See `.env.example` for the full list (payments,
SMTP, Telegram, supplier scrapers, etc.).

---

## Step 3 — Run

```bash
docker compose up -d
```

First build pulls Python deps — takes 3-5 min. Subsequent rebuilds reuse the
cached `pip wheel` layer (~30 sec).

```bash
docker compose ps          # should show "healthy" after ~20s
docker compose logs -f app # tail
```

Browse to `http://YOUR-IP:8501`. **Sign up — the first account is
auto-promoted to admin.**

---

## Step 4 — HTTPS (don't skip!)

Streamlit ships no TLS. Stick Caddy or nginx in front.

### Option A — Caddy (easiest, auto-HTTPS)

```bash
sudo apt install -y caddy
sudo nano /etc/caddy/Caddyfile
```

```caddyfile
nirva.example.com {
    reverse_proxy 127.0.0.1:8501 {
        # Streamlit needs WebSocket upgrades
        header_up Host {host}
    }
    encode gzip
}
```

```bash
sudo systemctl reload caddy
```

Caddy auto-issues the cert and renews it.

### Option B — nginx + certbot

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/nirva
```

```nginx
server {
    listen 80;
    server_name nirva.example.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        # Required for Streamlit WebSockets
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/nirva /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d nirva.example.com
```

---

## Step 5 — Backups

`scripts/backup.sh` tars `data/` (every per-user DB + uploaded images +
generated content) to `backups/` daily.

```bash
crontab -e
```

```cron
# 03:00 every day, snapshot to ./backups/, keep 14 days
0 3 * * * /home/deploy/nirva.sell/scripts/backup.sh
```

If `.env` has `TELEGRAM_BOT_TOKEN` + `TELEGRAM_DEFAULT_CHAT_ID`, the script
posts a confirmation chat.

### Off-site copies (recommended)

Rotate to S3 / Backblaze:

```bash
# Add to cron after the backup line
30 3 * * * rclone copy /home/deploy/nirva.sell/backups remote:nirva-backups --max-age 25h
```

---

## Step 6 — Uptime monitoring

Free options: UptimeRobot, BetterUptime, Hetrix Tools.

Point them at `https://nirva.example.com/_stcore/health` — Streamlit's
built-in health probe returns 200 OK when the app is alive.

Or local cron:

```cron
*/5 * * * * /home/deploy/nirva.sell/scripts/healthcheck.sh https://nirva.example.com || curl -s -X POST your-alert-webhook
```

---

## Step 7 — Cron-driven background jobs

```cron
# Hourly: refresh marketplace policy diffs, fan out notify on change
0 * * * * docker compose -f /home/deploy/nirva.sell/docker-compose.yml exec -T app python scripts/policy_check.py

# 03:00 daily: backup
0 3 * * * /home/deploy/nirva.sell/scripts/backup.sh
```

---

## Maintenance

```bash
# Pull updates
git pull
docker compose build --no-cache app
docker compose up -d

# Check container resource use
docker stats nirva-sell

# Shell into the container
docker compose exec app bash

# Restore from backup
tar xzf backups/nirva-20260516-030000Z.tgz -C data/
docker compose restart app

# Free disk: prune stale images
docker image prune -a
```

---

## Scaling beyond one box

The architecture is per-user SQLite — fine up to ~500 active users on one
box. To go bigger:

1. Mount `data/` on an external block volume (EBS, Linode block storage).
2. Switch SQLite → Postgres (the `db.conn()` abstraction is the only place
   that touches the DB; ~1 day's port).
3. Run multiple `app` replicas behind an nginx upstream pool — Streamlit is
   session-stateful, so sticky-routing (`ip_hash`) is required.
4. Move heavy AI calls into a queue (`rq`/Celery) so the web tier stays
   responsive.

We don't ship this out of the box because most resellers will never need it.

---

## Common issues

**Container is unhealthy / 503**
→ `docker compose logs app` — usually a missing dep in `.env` or a port
conflict on 8501.

**`pip wheel` step takes forever**
→ rembg/onnxruntime are big. After the first build, subsequent rebuilds
hit the layer cache. Don't `--no-cache` unless you're debugging.

**Out-of-memory kill**
→ rembg with large images can spike to 800 MB. Bump the compose `memory:
1500M` limit, or set `REMBG_DISABLE=1` to skip background-removal features.

**HTTPS but app shows mixed-content**
→ Forgot `proxy_set_header X-Forwarded-Proto $scheme;` in nginx. Streamlit
detects the scheme from this header.

**WebSocket disconnects every 30s**
→ Your reverse proxy has a short `proxy_read_timeout`. Bump it to 86400
(see the nginx example above).

---

## Security checklist

- [ ] `.env` is in `.gitignore` AND `.dockerignore`
- [ ] Port 8501 is NOT open to the internet (firewall blocks all but 80/443)
- [ ] HTTPS is on
- [ ] First user signed up = admin (verified via `/Admin` page)
- [ ] Daily backups verified working (check `backups/` after first night)
- [ ] OS auto-updates enabled (`unattended-upgrades` on Ubuntu)
- [ ] Docker auto-update via Watchtower (optional, but tidy)

---

## Cost projection

A typical small-shop deployment:

| Item | Provider | $/mo |
|---|---|---|
| VPS (2 GB RAM, 50 GB SSD) | Hetzner CX11 | $4.50 |
| Domain | Cloudflare Registrar | $1 (avg) |
| S3 backup (~5 GB) | Backblaze B2 | $0.05 |
| **Total** | | **~$6/mo** |

Per-user AI costs ride on the user's own Anthropic key — your only spend is
the bytes/CPU.
