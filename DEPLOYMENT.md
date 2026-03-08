# Deploying LungGuard to Vercel

This guide will walk you through deploying the **LungGuard** frontend dashboard to Vercel and the FastAPI backend to a serverless platform.

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐
│  Vercel         │  ────►  │  Railway/Render  │
│  (Frontend)     │  ◄────  │  (Backend API)   │
│  React + Vite   │         │  FastAPI + ML    │
└─────────────────┘         └──────────────────┘
```

---

## Part 1: Deploy Frontend to Vercel

### Prerequisites

- GitHub account
- Vercel account (free tier is sufficient)
- Your repository: https://github.com/AyushWadje/LungGuard

### Step 1: Connect Repository to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New Project"**
3. Import your GitHub repository: `AyushWadje/LungGuard`
4. Click **"Import"**

### Step 2: Configure Project Settings

Vercel will detect the project automatically. Configure these settings:

#### Framework Preset
- **Framework Preset:** Vite
- **Root Directory:** `./` (leave as is - vercel.json handles subdirectory)

#### Build & Development Settings
- **Build Command:** `cd aerolung-dashboard && npm install && npm run build`
- **Output Directory:** `aerolung-dashboard/dist`
- **Install Command:** `cd aerolung-dashboard && npm install`

#### Environment Variables

Add these environment variables in Vercel:

| Key | Value | Description |
|-----|-------|-------------|
| `VITE_API_URL` | `https://your-backend-url.com` | Backend API URL (update after deploying backend) |

**Important:** Initially, you can use `http://localhost:5000` for testing, but you'll need to deploy the backend separately.

### Step 3: Deploy

1. Click **"Deploy"**
2. Wait for the build to complete (typically 2-3 minutes)
3. Your frontend will be live at: `https://lungguard-[random].vercel.app`

### Step 4: Custom Domain (Optional)

1. Go to your project settings in Vercel
2. Navigate to **Domains**
3. Add your custom domain (e.g., `lungguard.app`)
4. Follow DNS configuration instructions

---

## Part 2: Deploy Backend (FastAPI)

Vercel doesn't support long-running Python processes like FastAPI. Deploy the backend to one of these platforms:

### Option A: Railway (Recommended)

**Why Railway?**
- Free tier includes 500 hours/month
- Supports Python/FastAPI natively
- Includes free PostgreSQL if needed
- Simple GitHub integration

#### Steps:

1. Go to [Railway.app](https://railway.app)
2. Sign up with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select `AyushWadje/LungGuard`
5. Railway will detect the Python app

**Add Environment Variables:**
```env
PORT=5000
SECRET_KEY=your-production-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

**Create `railway.json`:**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

6. Deploy and copy your Railway URL (e.g., `https://lungguard-production.up.railway.app`)

### Option B: Render

1. Go to [Render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name:** lungguard-api
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Add same environment variables as above

### Option C: Fly.io

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Launch: `fly launch` (in project root)
4. Deploy: `fly deploy`

---

## Part 3: Connect Frontend to Backend

After deploying the backend:

1. Copy your backend URL (e.g., `https://lungguard-api.railway.app`)
2. Go to Vercel project settings
3. Navigate to **Environment Variables**
4. Update `VITE_API_URL` to your backend URL
5. Go to **Deployments** tab
6. Click **"⋮"** on latest deployment → **"Redeploy"**

---

## Part 4: Update CORS Settings

Update your backend `main.py` to allow your Vercel domain:

```python
# In main.py, update CORS_ORIGINS
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", 
    "https://your-vercel-app.vercel.app,http://localhost:5173"
).split(",")
```

Set this in your backend deployment environment variables.

---

## Quick Deploy Commands

### Using Vercel CLI (Alternative Method)

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
cd PIH-2026_SYNTAX_GLITCH-main
vercel

# Deploy to production
vercel --prod
```

### Environment Variables via CLI

```bash
# Add environment variable
vercel env add VITE_API_URL production

# Pull environment variables
vercel env pull
```

---

## Testing Your Deployment

After both frontend and backend are deployed:

### 1. Test Backend API

```bash
# Test health endpoint
curl https://your-backend-url.com/health

# Test login
curl -X POST https://your-backend-url.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"1234"}'
```

### 2. Test Frontend

1. Visit your Vercel URL: `https://lungguard-[random].vercel.app`
2. Try logging in with:
   - Email: `test@example.com`
   - Password: `1234`
3. Check if dashboard loads correctly
4. Test predictions and API calls

---

## CI/CD: Automatic Deployments

### Vercel Automatic Deployments

Vercel automatically deploys on every push to `main` branch.

**Preview Deployments:**
- Every PR gets a unique preview URL
- Test changes before merging

**Production Deployments:**
- Merges to `main` deploy to production
- Instant rollback available

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```

---

## Performance Optimization

### Frontend Optimization

1. **Code Splitting:**
   ```typescript
   // In App.tsx, use lazy loading
   const Dashboard = lazy(() => import('./pages/Dashboard'));
   ```

2. **Image Optimization:**
   - Use WebP format
   - Implement lazy loading for images

3. **Bundle Size:**
   ```bash
   # Analyze bundle
   npm run build -- --mode analyze
   ```

### Backend Optimization

1. **Caching:**
   - Add Redis for response caching
   - Cache ML predictions for common inputs

2. **CDN for ML Models:**
   - Upload models to S3/CloudFlare R2
   - Load on-demand instead of during startup

---

## Troubleshooting

### Frontend Issues

**Issue: "Failed to fetch" errors**
- Check CORS settings in backend
- Verify `VITE_API_URL` environment variable
- Ensure backend is running

**Issue: Blank page after deployment**
- Check browser console for errors
- Verify build output in Vercel logs
- Check routing configuration in `vercel.json`

### Backend Issues

**Issue: "Application error" or 500 errors**
- Check backend logs in Railway/Render
- Verify ML models are included in deployment
- Check memory limits (ML models need ~500MB RAM)

**Issue: Slow API responses**
- ML models take time to load (30-60s on first request)
- Implement model caching
- Consider using cold start optimization

---

## Monitoring & Maintenance

### Vercel Analytics

Enable in Vercel dashboard:
- **Speed Insights:** Monitor page load times
- **Web Vitals:** Track Core Web Vitals
- **Audience Insights:** Understand user geography

### Backend Monitoring

#### Railway/Render Logs

```bash
# View live logs
railway logs --tail

# Or in Render dashboard
```

#### Health Checks

Add health check endpoint:
```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "ml_models_loaded": calculator.ml_models_loaded,
        "timestamp": datetime.now().isoformat()
    }
```

Set up uptime monitoring:
- [UptimeRobot](https://uptimerobot.com) (free)
- [Better Uptime](https://betteruptime.com) (free tier)

---

## Security Checklist

Before going to production:

- [ ] Change `SECRET_KEY` to a strong random string (min 32 characters)
- [ ] Enable HTTPS only (Vercel does this automatically)
- [ ] Update CORS origins to only allow your Vercel domain
- [ ] Review exposed endpoints and add authentication where needed
- [ ] Enable rate limiting on sensitive endpoints
- [ ] Scan for vulnerabilities: `npm audit` and `pip check`
- [ ] Set up error tracking (e.g., Sentry)
- [ ] Enable Vercel Password Protection for staging environments

---

## Cost Estimation

### Free Tier Limits

**Vercel (Free):**
- 100GB bandwidth/month
- 1,000 builds/month
- Unlimited personal projects

**Railway (Free Trial):**
- $5 credit/month
- ~500 hours of runtime

**Render (Free):**
- 750 hours/month per service
- Spins down after 15 minutes of inactivity

### Paid Options

If you exceed free tiers:
- **Vercel Pro:** $20/month
- **Railway Hobby:** $5-10/month (usage-based)
- **Render Starter:** $7/month per service

---

## Domain Setup

### Custom Domain on Vercel

1. Purchase domain (Namecheap, Google Domains, etc.)
2. Add domain in Vercel project settings
3. Update DNS records:
   - **A Record:** `76.76.21.21`
   - **CNAME:** `cname.vercel-dns.com`

### SSL Certificate

Vercel automatically provisions SSL certificates via Let's Encrypt.

---

## Rollback Strategy

### Vercel Rollback

1. Go to **Deployments** in Vercel dashboard
2. Find previous working deployment
3. Click **"⋮"** → **"Promote to Production"**

### Backend Rollback

**Railway:**
```bash
railway rollback
```

**Render:**
- Use manual deploy from specific commit

---

## Next Steps After Deployment

1. ✅ Test all functionality in production
2. ✅ Set up monitoring and alerts
3. ✅ Configure custom domain
4. ✅ Enable analytics
5. ✅ Add error tracking (Sentry)
6. ✅ Set up backup strategy for user data
7. ✅ Create staging environment
8. ✅ Document API for external users

---

## Support & Resources

- **Vercel Docs:** https://vercel.com/docs
- **Railway Docs:** https://docs.railway.app
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/
- **Issues:** https://github.com/AyushWadje/LungGuard/issues

---

<div align="center">
  <h3>🚀 Your LungGuard Application is Ready for Production!</h3>
  <p><i>High-performance, scalable, and secure deployment on Vercel</i></p>
</div>
