# Consensus AI - DigitalOcean Deployment Guide

## Prerequisites
- DigitalOcean account
- Domain (optional)
- SSH key added to DigitalOcean

## Step 1: Create Droplet

1. Go to DigitalOcean → Create → Droplets
2. Select:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic → $12/mo (2GB RAM, 1 CPU) minimum
   - **Datacenter:** Choose nearest to you
   - **Authentication:** SSH Key
3. Click **Create Droplet**
4. **Copy the IP address** — you'll need this for WEEX whitelist!

## Step 2: Connect to Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

## Step 3: Install Docker

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

## Step 4: Clone Repository

```bash
# Clone your repo
git clone https://github.com/Pratik-Shirodkar/consensus-ai.git
cd consensus-ai
```

## Step 5: Configure Environment

```bash
# Create .env file
cp backend/.env.example backend/.env

# Edit with your API keys
nano backend/.env
```

Add your keys:
```
WEEX_API_KEY=your_api_key
WEEX_API_SECRET=your_secret_key
WEEX_PASSPHRASE=your_passphrase
OPENAI_API_KEY=your_openai_key
```

## Step 6: Deploy

```bash
# Build and start containers
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Step 7: Access

- **Frontend:** http://YOUR_DROPLET_IP
- **Backend API:** http://YOUR_DROPLET_IP:8000
- **API Docs:** http://YOUR_DROPLET_IP:8000/docs

## Useful Commands

```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# View backend logs
docker-compose logs -f backend

# Update code
git pull
docker-compose up -d --build
```

## WEEX Whitelist

Use your Droplet's IP address for the WEEX API whitelist:
```
YOUR_DROPLET_IP (e.g., 164.92.123.45)
```
