# 🚀 Quick Deploy to Vercel

Deploy LungGuard to Vercel in 5 minutes!

## One-Click Deploy (Fastest)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FAyushWadje%2FLungGuard&env=VITE_API_URL&envDescription=Backend%20API%20URL%20for%20the%20FastAPI%20backend&project-name=lungguard&repository-name=lungguard)

Click the button above and follow Vercel's prompts.

---

## Manual Deploy (Recommended)

### Step 1: Fork/Clone Repository

```bash
git clone https://github.com/AyushWadje/LungGuard.git
cd LungGuard
```

### Step 2: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 3: Login to Vercel

```bash
vercel login
```

### Step 4: Deploy

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### Step 5: Configure Environment

When prompted, set:
- **VITE_API_URL:** Your backend API URL (or `http://localhost:5000` for testing)

---

## Deploy Backend First

The frontend needs a backend API to function. Choose one:

### Option A: Railway (Free)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize
railway init

# 4. Deploy
railway up

# 5. Your backend URL will be shown (copy it)
```

### Option B: Render (Free)

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Render will auto-detect Python
5. Click "Create Web Service"
6. Copy your URL when ready

### Option C: Use Existing Backend

If you're running backend locally or have it deployed:
```bash
# Set environment variable
vercel env add VITE_API_URL production
# Enter: http://your-backend-url.com
```

---

## After Deployment

### 1. Update Frontend Environment

```bash
# In Vercel dashboard or via CLI
vercel env add VITE_API_URL production
# Enter your backend URL

# Redeploy
vercel --prod
```

### 2. Update Backend CORS

In your backend deployment, set environment variable:
```
CORS_ORIGINS=https://your-app.vercel.app
```

### 3. Test Deployment

Visit your Vercel URL and test:
- ✅ Login with `test@example.com` / `1234`
- ✅ Dashboard loads correctly
- ✅ API calls work
- ✅ ML predictions respond

---

## Troubleshooting

### "Failed to fetch" Error

**Solution:** Update CORS in backend
```python
# Backend needs to allow your Vercel domain
CORS_ORIGINS="https://your-app.vercel.app"
```

### Build Fails

**Solution:** Check build logs in Vercel dashboard
```bash
# Or view locally
vercel logs
```

### Page Blank After Deploy

**Solution:** Check browser console
- Verify API URL is correct
- Check network tab for failed requests
- Ensure backend is running

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API endpoint | `https://api.lungguard.com` |

---

## Custom Domain Setup

```bash
# Add domain via CLI
vercel domains add lungguard.app

# Or in Vercel dashboard:
# Project → Settings → Domains → Add
```

---

## Automatic Deployments

Once connected to GitHub:
- ✅ Every push to `main` → Production deploy
- ✅ Every PR → Preview deploy
- ✅ Instant rollback available

---

## Cost

- **Vercel Free Tier:**
  - 100GB bandwidth/month
  - Unlimited deployments
  - Perfect for personal projects
  
- **Vercel Pro ($20/month):**
  - Unlimited bandwidth
  - Team features
  - Advanced analytics

---

## Need Help?

- 📖 [Full Deployment Guide](./DEPLOYMENT.md)
- 🐛 [Report Issues](https://github.com/AyushWadje/LungGuard/issues)
- 💬 [Discussions](https://github.com/AyushWadje/LungGuard/discussions)

---

<div align="center">
  <b>⚡ Deploy in 5 minutes with Vercel!</b>
</div>
