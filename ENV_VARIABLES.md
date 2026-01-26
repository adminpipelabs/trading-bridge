# Environment Variables for Hummingbot Integration

## Required Environment Variables

Add these to Railway (Trading Bridge service):

```bash
# Hummingbot API Configuration
HUMMINGBOT_API_URL=http://localhost:8000
HUMMINGBOT_API_USERNAME=hummingbot
HUMMINGBOT_API_PASSWORD=<your_password>
```

**OR** if using API key authentication:

```bash
HUMMINGBOT_API_URL=http://localhost:8000
HUMMINGBOT_API_KEY=<your_api_key>
```

## Finding Credentials

Run the credential finder script:

```bash
cd ~/ai-trading-ui
./find_hummingbot_creds.sh ~/hummingbot_files
```

Or check manually:

```bash
# Check docker-compose.yml
cat ~/hummingbot_files/docker-compose.yml | grep -i "api\|auth\|user\|pass"

# Check .env file
cat ~/hummingbot_files/.env | grep -i "api\|auth\|user\|pass"

# Check inside container
docker exec hummingbot-api env | grep -i "api\|auth\|user\|pass"
```

## For Tailscale VPN (Phase 1)

If using Tailscale to connect Railway → Local Hummingbot:

```bash
# Get your Tailscale IP
tailscale ip -4

# Set in Railway:
HUMMINGBOT_API_URL=http://100.64.0.5:8000  # Use your Tailscale IP
HUMMINGBOT_API_USERNAME=hummingbot
HUMMINGBOT_API_PASSWORD=<password>
```

## For Railway Deployment (Phase 2)

If Hummingbot is deployed to Railway:

```bash
# Use Railway internal service URL
HUMMINGBOT_API_URL=http://hummingbot-api:8000
HUMMINGBOT_API_USERNAME=hummingbot
HUMMINGBOT_API_PASSWORD=<password>
```

## Testing Connection

After setting variables, test:

```bash
# From Trading Bridge container/logs
curl -u username:password http://localhost:8000/bot-orchestration/status
```
