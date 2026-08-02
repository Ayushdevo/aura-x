# Ayush Tiwari Personal AI Digital Twin — Deployment Guide

## Architecture Overview

```
aura-x/
├── backend/          # FastAPI Python server
│   ├── main.py       # App entrypoint + API routes
│   ├── agent.py      # AI reasoning agent
│   ├── vector_db.py  # Vector search / RAG layer
│   └── resume_data.json
├── frontend/         # Static HTML/CSS/JS
│   ├── index.html
│   ├── style.css
│   └── app.js
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container config
├── railway.toml      # Railway platform config
└── render.yaml       # Render platform config
```

The FastAPI backend serves static frontend files directly — so **one single deployment** hosts everything.

---

## 🚀 Recommended: Deploy on Railway (Easiest)

Railway offers a **free tier**, GitHub integration, and auto-HTTPS. Perfect for this stack.

### Step 1 — Push to GitHub

First, create a `.gitignore` file so you don't upload `venv/` or cache files:

```
venv/
__pycache__/
*.pyc
backend/embeddings_cache.json
.env
```

Then push your project to a **new GitHub repository**:

```bash
git init
git add .
git commit -m "Initial deploy: Personal AI Digital Twin Portfolio"
git remote add origin https://github.com/Ayushdevo/aura-x.git
git push -u origin main
```

### Step 2 — Create Railway Project

1. Go to [railway.app](https://railway.app) → **Login with GitHub**
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `aura-x` repository
4. Railway auto-detects Python and uses the `railway.toml` config

### Step 3 — Set Environment Variable

In Railway project dashboard:
- Go to **Variables** tab
- Add: `OPENROUTER_API_KEY` = `<paste-your-openrouter-api-key-here>`

> ⚠️ **Important**: Never commit your API key to GitHub. The backend reads it from env (`os.getenv("OPENROUTER_API_KEY")`). Paste the key only in Railway/Render's Variables dashboard.

### Step 4 — Set Custom Domain `ayushrao.tech`

1. In Railway project → **Settings** → **Domains**
2. Click **"Add Custom Domain"**
3. Enter `ayushrao.tech`
4. Railway will give you a **CNAME target** like `abc123.up.railway.app`

**DNS Configuration at your domain registrar (GoDaddy/Namecheap/etc):**

| Type  | Name  | Value                        |
|-------|-------|------------------------------|
| CNAME | @     | `abc123.up.railway.app`      |
| CNAME | www   | `abc123.up.railway.app`      |

> DNS propagation takes 5–30 minutes. Railway auto-provisions a free SSL/HTTPS certificate.

---

## 🐳 Alternative: Deploy on Render (Also Free)

1. Go to [render.com](https://render.com) → Connect GitHub
2. New **Web Service** → select `aura-x` repo
3. Use the `render.yaml` config already created
4. Add env var `OPENROUTER_API_KEY`
5. Under **Custom Domains** → add `ayushrao.tech`
6. Point DNS CNAME to the Render URL

---

## 🖥️ Alternative: Deploy on a VPS (Full Control)

If you have a VPS (DigitalOcean, Vultr, Hostinger):

```bash
# On your VPS (Ubuntu)
git clone https://github.com/Ayushdevo/aura-x.git
cd aura-x
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Then use **nginx** as reverse proxy and **Certbot** for SSL:

```nginx
server {
    server_name ayushrao.tech www.ayushrao.tech;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

---

## 🔐 Security Checklist Before Publishing

- [x] API key moved to environment variable (already done)
- [ ] Add a `.gitignore` to exclude `venv/` and `embeddings_cache.json`
- [ ] Review CORS settings (currently `*` - fine for portfolio)
- [ ] The API key is a free-tier key, but still keep it private

---

## 📋 Quick Commands Summary

```bash
# 1. Create .gitignore
echo "venv/\n__pycache__/\n*.pyc\nbackend/embeddings_cache.json\n.env" > .gitignore

# 2. Initialize git and push
git init && git add . && git commit -m "Deploy: AI Digital Twin Portfolio"

# 3. Test production locally with Docker
docker build -t aura-x . && docker run -p 8000:8000 -e OPENROUTER_API_KEY="your-key" aura-x
```
