# KATYA EXIM — Website

Premium Indian Textile Export Company website. Built with Node.js + Express, ready to deploy on Railway.

## Structure

```
katyaexim-website/
├── server.js          # Express server (serves static files + contact API)
├── package.json
├── railway.json       # Railway deploy config
├── .env.example       # Environment variable reference
└── public/
    └── index.html     # Full single-page website
```

## Deploy to Railway

### Option 1: Railway CLI
```bash
railway login
railway init
railway up
```

### Option 2: GitHub → Railway
1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo — Railway will auto-detect Node.js and run `npm start`

### Option 3: Railway Dashboard
1. New Project → Empty Project → Add Service → GitHub Repo
2. Done — Railway reads `railway.json` automatically

---

## Environment Variables (Optional)

Set these in Railway's **Variables** panel to enable real email delivery via the contact form:

| Variable | Description |
|---|---|
| `CONTACT_EMAIL` | Where to receive enquiries (default: katyayaniexim@gmail.com) |
| `SMTP_HOST` | SMTP host (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (e.g. `587`) |
| `SMTP_SECURE` | `true` for SSL/465, `false` for STARTTLS/587 |
| `SMTP_USER` | SMTP username / Gmail address |
| `SMTP_PASS` | SMTP password or Gmail App Password |

> **Gmail App Password**: Go to Google Account → Security → 2-Step Verification → App Passwords → Generate one for "Mail".

---

## Local Development

```bash
npm install
npm start
# Visit http://localhost:3000
```

---

## Features

- ✅ Full SPA: Home, About, Products, Gallery, Certificates, Contact
- ✅ Contact form with email delivery (SMTP configurable)
- ✅ Mobile-responsive with hamburger menu
- ✅ Smooth scroll animations and reveal on scroll
- ✅ Railway-ready (`railway.json`, proper `PORT` handling)
- ✅ SEO meta tags
- ✅ No external database required

---

## Company Info

**KATYA EXIM**  
Flat No. 104, Nilgiri Apartment, Barakhamba Road, New Delhi – 110001  
📧 katyayaniexim@gmail.com  
🏛️ GSTIN: 07EFQPD1466A1ZO
