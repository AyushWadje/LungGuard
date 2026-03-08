# Project Requirements (requirement.md)

This document outlines the software dependencies, environment setup, and system requirements needed to run the **AeroLung** platform, including both the Backend API (PLSI Engine) and the React Dashboard.

---

## 1. System & Environment Requirements

To ensure a smooth execution of the project, the primary deployment environment should meet the following minimum configurations:

- **Operating System:** Window 10/11, macOS, or Linux (Ubuntu 20.04+ recommended)
- **Minimum RAM:** 4 GB (8 GB recommended for simultaneous backend and frontend operation)
- **Minimum Storage:** 1 GB free space
- **Network Interface:** Active internet connection required for live sensory data (OpenWeatherMap, OpenAQ).

---

## 2. Software Requirements

Ensure the following runtimes and package managers are installed globally on your machine:

- **Python Runtime:** Python 3.9 or higher (Ensure `pip` is installed).
- **Node Environment:** Node.js v18.0.0 or higher.
- **Node Package Manager:** `npm` (v9+) or `yarn` (v1.22+).

---

## 3. Backend Dependencies (Python)

The ML forecasting engine and API are built using Python. These dependencies should be installed in a Virtual Environment.

### Core Frameworks
- `fastapi` (High-performance API framework)
- `uvicorn` (ASGI server for FastAPI)
- `pydantic` (Data validation and payload parsing)

### Machine Learning & Data Processing
- `scikit-learn` (RandomForest & predictive modeling)
- `numpy` (Numerical arrays and mathematical logic)
- `pandas` (Dataframe manipulation)
- `joblib` (Model serialization/deserialization)

### Asynchronous & Network Libraries
- `aiohttp` (Asynchronous HTTP requests for OpenAQ & OWM APIs)
- `nest-asyncio` (To manage nested event loops if required)
- `requests` (Synchronous HTTP fallbacks)
- `pyngrok` (Optional: For securely bridging localhost to public URLs)

**Installation Command:**
```bash
pip install fastapi uvicorn pydantic scikit-learn numpy pandas joblib aiohttp nest-asyncio requests pyngrok
```
*(You may also place these in a `requirements.txt` file and run `pip install -r requirements.txt`).*

---

## 4. Frontend Dependencies (React Dashboard)

The analytics platform relies on a modern enterprise frontend setup.

### Core Libraries
- `react` (v19.2) - UI Library
- `react-dom` (v19.2) - DOM Rendering
- `react-router-dom` (v7+) - Route Management
- `vite` (v7+) - Bundler and Dev Server

### UI & Styling
- `tailwindcss` (v3.4+) - Utility-first styling map
- `postcss` & `autoprefixer` - CSS processors
- `clsx` & `tailwind-merge` - Dynamic class construction

### Charts & Reporting
- `recharts` (v3.7) - Composable React charting library
- `jspdf` & `html2canvas` - Report generation and PDF exporting

**Installation Command:**
```bash
cd aerolung-dashboard
npm install
```

---

## 5. Third-Party API Keys

The system requires external API tokens integrated into a `.env` file at the root of the backend directory.

| Service | Environment Variable | Purpose |
|---------|-----------------------|---------|
| **OpenWeatherMap** | `OWM_API_KEY` | Fetching live macro-city Air Quality Index metrics natively. |
| **OpenAQ** | `OPENAQ_API_KEY` | Fetching granular, localized sensor nodal readings for PM2.5. |

*Note: Default developmental tokens are embedded in the repository for immediate hackathon evaluation, but standard practice involves isolating these out of source control.*
