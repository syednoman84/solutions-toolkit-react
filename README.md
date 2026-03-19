<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=white" alt="React 19" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Vite-⚡-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Flask-🐍-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/Python-3-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3" />
</p>

# 🛠️ PCM Tenants Configuration Toolkit

> 🚀 A full-stack web application for automating PCM tenant configuration management — product setup, validation, SSO connections, rebasing, and cross-tenant scanning.

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| 🖥️ Frontend | React 19, TypeScript, Vite |
| ⚙️ Backend | Python 3, Flask |
| 🔀 Routing | React Router v7 |
| 🎨 Styling | Custom CSS (no framework) |
| 📜 Scripts | Python automation (Git, GitHub CLI) |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🏗️ New Tenant Setup | Create a full tenant config from scratch: clone repos, create product directories, generate `definition.json`, commit, push, and open a PR |
| ➕ Add Products | Add new products to an existing tenant without touching app/env files |
| 🚫 Disable Products | Set `selfServiceManaged: false` and disable agent creation for specific products |
| 🔐 Add SSO Connection | Update `queueManagerUISettings.json` with new SSO entries |
| 🔄 Rebase Pending Changes | Interactive step-by-step rebase of `pending-changes` branches onto master |
| 📝 Add Changelog | Create changelog JSON files in each product's `pending-changes` branch |
| 👁️ View Products by Tenant | Fetch and display all product definitions for a tenant in a table |
| 🔍 Scan All Tenants | Scan every tenant repo in the org and generate product reports (JSON, counts, type breakdowns) |
| ✅ Validation | Verify template vars, env file placeholders, and product summaries post-setup |

---

## 📁 Project Structure

```
📦 pcm-toolkit
├── 🖥️ frontend/               # React TypeScript app (Vite)
│   ├── src/
│   │   ├── 📄 pages/          # 9 page components (1:1 with features)
│   │   ├── 🧩 components/     # Shared UI components
│   │   ├── 🪝 hooks/          # Custom React hooks
│   │   ├── 🌐 api.ts          # Typed API client
│   │   └── 📋 types.ts        # TypeScript interfaces
│   └── ⚡ vite.config.ts      # Dev server + API proxy config
│
├── ⚙️ web-ui/
│   └── 🐍 app.py              # Flask API server (all /api/* endpoints)
│
├── 📜 scripts/                 # Python automation scripts
│   ├── PCM_Tenants_Configs_Setup.py
│   ├── PCM_Add_Products_Existing_Tenant.py
│   ├── PCM_Disable_Products_Existing_Tenant.py
│   ├── PCM_Add_SSO_Connection.py
│   ├── fetch_tenant_products.py
│   ├── tenant_product_analyzer.py
│   ├── print_products_summary.py
│   ├── validate_template_vars.py
│   └── validate_env_files.py
│
├── 📂 params/
│   └── params.txt              # Configuration file (read/written by API)
│
└── 🚀 start-dev.sh            # One-command dev startup
```

---

## 🏁 Getting Started

### 📋 Prerequisites

| Requirement | Version |
|-------------|---------|
| 📗 Node.js | 18+ |
| 🐍 Python | 3.6+ |
| 🔧 Git CLI | Latest |
| 🐙 GitHub CLI (`gh`) | Authenticated with your GitHub Enterprise instance |

### ⚡ Install & Run

```bash
# 1️⃣ Install frontend dependencies
cd frontend && npm install && cd ..

# 2️⃣ Install backend dependencies
pip3 install -r web-ui/requirements.txt

# 3️⃣ Start both servers
chmod +x start-dev.sh
./start-dev.sh
```

Or run them separately in two terminals:

```bash
# 🖥️ Terminal 1 — Flask API (port 5000)
cd web-ui && python3 app.py

# 💻 Terminal 2 — React dev server (port 3000)
cd frontend && npm run dev
```

Then open 🌐 **http://localhost:3000**

### 🔧 How It Works

The React frontend runs on port 3000 and proxies all `/api/*` requests to the Flask backend on port 5000. Flask reads/writes `params/params.txt` and executes the Python scripts in `scripts/` via subprocess. Results are stored in a `results/` directory (git-ignored).

```
🌐 Browser → ⚛️ React (Vite :3000) → 🐍 Flask API (:5000) → 📜 Python Scripts → 🐙 Git/GitHub
```

---

## ⚙️ Configuration

All scripts read from `params/params.txt`. The web UI loads and saves this file automatically. Key parameters:

| Parameter | Description |
|-----------|-------------|
| `destination_repo_github_url` | 🔗 Tenant config repo URL |
| `tenant-domain` | 🏷️ 3-letter tenant code |
| `tenant-id` | 🆔 Tenant identifier |
| `template_vars_tag` | 🏷️ Version tag for template vars |
| `pr_title` | 📌 Pull request title |
| `branchName` | 🌿 Feature branch name |
| `commit_message` | 💬 Commit message |
| Products | 📦 `Consumer_DAO_Product_1=Eagle Free Checking (150)` |

### 📦 Supported Product Types

| Type | Description |
|------|-------------|
| 💳 `Consumer_CC` | Consumer Credit Card Self Service |
| 🏦 `Consumer_DAO` | Consumer Deposit Account Opening |
| 🏢 `SMB_DAO` | Small Business Deposit Account Opening |
| 💳 `SMB_CC` | Small Business Credit Card |
| 💰 `SMB_LOC` | Small Business Line of Credit |
| 📄 `SMB_TL` | Small Business Term Loan |

---

## 🏗️ Production Build

```bash
cd frontend
npm run build
```

The built files land in `frontend/dist/` and can be served by any static file server or integrated into the Flask app.

---

## 📄 License

Internal use only.
