# AeroLung Fix Plan - Progress Tracker

## Phase 1: Critical Security Fixes
- [x] Remove hardcoded API keys from main.py → uses `os.getenv` + `load_dotenv`
- [x] Remove hardcoded ngrok token from comments → ngrok block fully removed
- [x] Add python-dotenv to requirements.txt → already present
- [x] Create .env.example → created at project root
- [x] Fix login endpoint to return HTTP 401 → `raise HTTPException(status_code=401)` in place
- [ ] Create .env file for local dev → copy .env.example and fill in real keys

## Phase 2: Bug Fixes
- [x] Remove unused imports in main.py → cleaned (removed nest_asyncio, threading, sklearn, etc.)
- [x] Fix variable naming conflicts (req shadowing) → renamed to `http_client`
- [x] Remove unnecessary time.sleep(2) → removed
- [x] Fix plsi_engine.py unused imports and p_norm bug → cleaned
- [x] Add missing pollutant alert thresholds → AlertEngine handles PM2.5 > 100
- [x] Fix hardcoded NO2 value in TrendPredictor → uses `pollutants.get('o3', 30)`
- [x] Fix dynamic Tailwind classes in AirQualityMap.tsx → `AQI_STATUS_MAP` with pre-defined classes
- [x] Implement statusFilter in Alerts.tsx → `useMemo` filter on both severity + status
- [x] Fix duplicate dark mode classes in Alerts.tsx → resolved
- [x] Fix duplicate dark mode classes in PopulationHealth.tsx → `dark:text-slate-400` (single)
- [x] Remove duplicated cn() from Layout.tsx → no duplicate usage found
- [x] Fix pollutant display (% vs µg/m³) in Dashboard.tsx → units come from API `Pollutant.unit`
- [x] Remove unused `cn` import from Analytics.tsx → removed
- [x] Replace `alert()` calls with state-based error UI in PopulationHealth.tsx → `exportError` state
- [x] Add `React` import to Dashboard.tsx, Login.tsx, Settings.tsx → fixed (needed for `React.FormEvent`)

## Phase 3: Code Quality & Architecture
- [x] Remove empty lung_risk_api.py → file already deleted
- [x] Remove unused App.css → file already deleted
- [x] Update API_DOCS.md to match real endpoints → endpoints aligned
- [x] Add missing /api/analytics/export endpoint OR remove frontend call → endpoint exists in main.py
- [x] Remove ml_models.zip from tracking (add to .gitignore) → `*.zip` in .gitignore

## Phase 4: Performance & Best Practices
- [x] Add global FastAPI error handling middleware → `@app.exception_handler(Exception)` in main.py
- [x] Add token expiry logic in AuthContext.tsx → 24h expiry with periodic check every 60s
- [x] Add path aliases in vite.config.ts → `@`, `@components`, `@pages`, `@services`, etc.
- [x] Improve vite.config.ts with build optimizations → `manualChunks`, `minify: 'terser'`, proxy

## Phase 5: Non-Functional Buttons & UI Fixes ✅ COMPLETED
- [x] **PopulationHealth.tsx** — `dot={<svg />}` → `dot={false}` on Line component (invalid prop)
- [x] **Alerts.tsx** — `useCallback` for `loadAlerts`; "View Details" expand panel; optimistic acknowledge UI (removes alert from list immediately)
- [x] **Analytics.tsx** — `setExporting(true)` moved before try block; controlled `showRespiratoryOverlay` state; conditional Line render on toggle
- [x] **AirQualityMap.tsx** — `activeLayer` state for layer buttons; `searchQuery` state filters city list; `showTooltip` state for close button; `isPlaying` state for play button; `zoomLevel` state for zoom buttons
- [x] **Settings.tsx** — Stale notification toggle fixed (pass new value directly to handler); `twoFAEnabled` controlled state; avatar file input ref wired to camera button
- [x] **Layout.tsx** — `searchQuery` controlled state; `showNotifications` dropdown panel with click-outside close; `await logout()` for async logout
- [x] **Dashboard.tsx** — `parseFloat` for spo2; `??` for stats; `predictionError` state; `useCallback` for `loadDashboardData`; controlled city select; `String()` cast for plsi_score
- [x] **AuthContext.tsx** — `logout: () => Promise<void>` type fix; `useCallback` for login/logout

## Remaining Action Items
1. **Create `.env`** — Copy `.env.example` → `.env` and fill in real `OWM_API_KEY` and `OPENAQ_API_KEY`
2. **Install frontend deps** — `cd aerolung-dashboard && npm install`
3. **Install backend deps** — `pip install -r requirements.txt`
4. **Run & test** — `python main.py` + `npm run dev` to verify full stack integration
