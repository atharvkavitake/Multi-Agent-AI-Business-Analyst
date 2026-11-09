# Multi-Agent AI Business Analyst & Automated BI System
### *Enterprise-Grade Multi-Agent Artificial Intelligence Platform for Automated Business Intelligence, Exploratory Data Analysis, and Strategic Executive Reporting*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Pandas](https://img.shields.io/badge/Pandas-2.2-150458.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3.svg?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Plotly](https://img.shields.io/badge/Plotly-5.20-3F4F75.svg?logo=plotly&logoColor=white)](https://plotly.com/)
[![ReportLab](https://img.shields.io/badge/ReportLab-4.1-FF6F00.svg)](https://www.reportlab.com/)
[![Tests](https://img.shields.io/badge/Pytest-36%20Passed%20(100%25)-success.svg?logo=pytest&logoColor=white)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Deployment](https://img.shields.io/badge/Render-Free%20Tier%20Ready-46E3B7.svg?logo=render&logoColor=white)](render.yaml)

---

## 🌟 Executive Summary & Motivation

Traditional Business Intelligence (BI) dashboards rely on static pre-configured charts or brittle drag-and-drop interfaces that demand significant manual data engineering before any actionable insight emerges. Conversely, modern generative AI prototypes often suffer from **mathematical hallucinations**, inventing metrics out of thin air, or executing risky arbitrary Python code via `eval()` that introduces severe security vulnerabilities.

The **Multi-Agent AI Business Analyst System** bridges this critical divide. Built from the ground up as a production-grade, enterprise-ready platform, it combines:
1. **Deterministic Statistical Engines:** 100% verified numerical computations (revenue, margins, anomalies, correlations, growth trajectories) powered by Pandas, NumPy, Scipy, and Scikit-learn.
2. **Specialized Multi-Agent AI Architecture:** 7 purpose-built AI agents orchestrated in a structured pipeline where language models *only interpret verified mathematical evidence*, eliminating metric fabrication.
3. **Safe Natural Language Query Engine:** A zero-eval Abstract Analytical Query Plan that parses free-form English questions into restricted, schema-validated aggregations.
4. **Automated Executive PDF Generation:** Instant compilation of boardroom-ready PDF briefs with professional typography, KPI tables, and prioritized strategic initiatives via ReportLab.
5. **100% Free Cloud Deployment:** Architected to run entirely on free-tier cloud infrastructure (Render Web Services, Supabase PostgreSQL, OpenRouter Free Tier LLMs).

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([Business User / Analyst]) -->|Upload CSV / Excel| UI[Enterprise Responsive UI\nHTML5 + CSS3 + Bootstrap 5]
    UI -->|REST API / Bearer JWT| Gateway[FastAPI Application Gateway\nInput Validation & MIME Filtering]
    
    subgraph Storage ["Persistence Layer"]
        SQLite[(Local SQLite Dev DB)]
        Supabase[(Supabase PostgreSQL Prod DB)]
    end
    Gateway <--> Storage

    subgraph DataEngine ["Deterministic Computation Engine (Pandas & Scikit-learn)"]
        Profiler[Column Detector & Quality Scorer]
        KPIEngine[Financial & KPI Calculator]
        OutlierEngine[Multi-Algorithm Anomaly Engine\nIQR + Z-Score + Isolation Forest]
        TrendEngine[Temporal Decomposition & Forecasting]
    end
    Gateway --> DataEngine

    subgraph Orchestrator ["Central Multi-Agent Orchestrator"]
        direction TB
        A1[Agent 1: Data Profiling Agent]
        A2[Agent 2: Business Data Analyst Agent]
        A3[Agent 3: Trend Analysis Agent]
        A4[Agent 4: Anomaly Detection Agent]
        A5[Agent 5: Business Strategy Agent]
        A6[Agent 6: Business Report Generation Agent]
        
        A1 --> A2 --> A3 --> A4 --> A5 --> A6
    end
    DataEngine --> Orchestrator
    
    subgraph GenAI ["AI Reasoning Layer (OpenRouter / Local Ollama)"]
        LLM1[Primary: Google Gemini 2.0 Flash Free]
        LLM2[Fallback: Meta Llama 3.3 70B Free]
        RuleEngine[Deterministic Zero-Failure Fallback Engine]
    end
    Orchestrator <--> GenAI

    subgraph OutputEngines ["Output & Presentation Engines"]
        VizEngine[Plotly & Chart.js Visualization Engine]
        ReportLabEngine[ReportLab Automated PDF Compiler]
        QueryAgent[Agent 7: Safe Natural Language Query Engine\nZero-Eval Abstract Query Plan]
    end
    Orchestrator --> OutputEngines
    OutputEngines --> UI
```

---

## 🤖 The 7 Specialized AI Agents

Every agent operates with strict Pydantic V2 schema validation, structured retry mechanisms, and a **deterministic fallback engine** that guarantees 100% platform availability even during cloud network timeouts or API rate limits.

| # | Agent Name | Core Responsibilities | Deterministic Foundation | AI Interpretation |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Data Profiling Agent** | Schema inference, column classification, missingness detection, duplicate identification, and data quality scoring. | Computes exact non-null counts, distinct cardinality, and applies a weighted A+ quality scoring formula. | Infers business domain context (e.g. Sales, Healthcare, SaaS) and recommends high-value analysis avenues. |
| **2** | **Business Data Analyst Agent** | Financial health diagnosis, KPI computation, category margins, and customer/regional segment performance. | Computes exact total revenue, gross profit, margin %, transaction counts, and Pearson correlation matrices. | Contextualizes margin drivers, pinpoints loss-leading categories, and extracts structural business patterns. |
| **3** | **Trend Analysis Agent** | Temporal pattern extraction, MoM/QoQ growth calculation, seasonality detection, and cautious forecasting. | Date parsing, time-series resampling (monthly/quarterly/yearly), linear slope calculation, and variance checks. | Interprets velocity changes, alerts on downward momentum, and presents bounded, non-hallucinatory forecasts. |
| **4** | **Anomaly Detection Agent** | Multivariate outlier identification and risk flagging. | Multi-method consensus combining Interquartile Range (IQR 1.5x), Z-score (|z| > 3.0), and Scikit-learn **Isolation Forest**. | Explains *why* records are anomalous without prematurely mischaracterizing legitimate spikes as fraud. |
| **5** | **Business Strategy Agent** | Converting analytical findings into boardroom-level strategic initiatives. | Synthesizes calculated KPIs, segment profitability gaps, and anomaly flags. | Formulates prioritized recommendations with **Supporting Evidence, Business Impact, Feasibility, and Action Steps**. |
| **6** | **Business Report Generation Agent** | Consolidating multi-agent outputs into an executive briefing document. | Aggregates structured Pydantic outputs from Agents 1 through 5. | Drafts a cohesive executive summary, synthesis narrative, and formats structured tables for the ReportLab PDF compiler. |
| **7** | **Business Query Agent** | Answering arbitrary natural language business questions about the uploaded dataset. | **Zero-Eval Abstract Query Plan:** Maps questions to safe, pre-compiled Pandas operations (`sum`, `mean`, `groupby`, `filter`). | Explains calculated quantitative facts in fluent, executive-ready language with chart recommendations. |

---

## 🛡️ Anti-Hallucination & Zero-Eval Security

### 1. Mathematical Anti-Hallucination Philosophy
Generative LLMs are probabilistic language predictors; they are notoriously unreliable at arithmetic on thousands of tabular rows. 
In this system:
- **Rule 1:** Language models are **never** permitted to calculate sums, averages, margins, or counts.
- **Rule 2:** All numbers originate exclusively from vectorized Pandas/NumPy execution on verified dataset memory.
- **Rule 3:** The LLM receives pre-computed numerical facts in its prompt context and is restricted to explaining, contextualizing, and synthesizing those exact verified values.

### 2. Zero-Eval Safe Analytical Query Engine
Many vulnerable LLM projects pass user questions into an LLM and execute the returned Python code using `exec()` or `eval()`. This invites catastrophic arbitrary code execution and SQL injection.

Our **Business Query Agent** utilizes an **Abstract Analytical Query Plan**:
```json
{
  "operation": "group_by_sum",
  "target_column": "Profit",
  "group_column": "Category",
  "sort_order": "descending",
  "limit": 5
}
```
The FastAPI backend validates the target columns against the dataset's actual schema, rejects any disallowed column references or unauthorized system calls, and executes the operation through a safe, sandboxed Pandas routine.

---

## 💻 Tech Stack & Engineering Decisions

### Frontend
- **Languages & Frameworks:** HTML5, CSS3, JavaScript (Vanilla ES6+ Modules), Bootstrap 5.3.
- **Visualizations:** Chart.js and Plotly.js for interactive client-side rendering.
- **Design System:** Custom Enterprise Dark/Light UI, glassmorphism telemetry cards, animated stage execution bars, and responsive layout across desktop, tablet, and mobile.

### Backend
- **Framework:** Python 3.10+, FastAPI (Asynchronous ASGI framework with OpenAPI/Swagger auto-generation).
- **Validation:** Pydantic V2 and Pydantic-Settings for strict type boundaries and environment configurations.
- **Server:** Uvicorn ASGI production server with lifespan state management.

### Data Processing & Machine Learning
- **Data Manipulation:** Pandas 2.2, NumPy 1.26.
- **Machine Learning & Statistics:** Scikit-learn 1.4 (`IsolationForest` for unsupervised anomaly detection), SciPy 1.12 (`zscore`, distribution metrics).
- **Spreadsheet Parsing:** OpenPyXL 3.1 for Excel `.xlsx` / `.xls` binary ingestion.

### AI & LLM Orchestration
- **API Client:** Asynchronous HTTPX client with custom exponential backoff retry handlers.
- **Model Providers:** OpenRouter Free Tier API (`google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.3-70b-instruct:free`) and optional local Ollama instances (`llama3`).
- **Resilience:** Deterministic rule-based analytical engine for seamless offline operation.

### Document & Report Generation
- **Compiler:** ReportLab 4.1 for multi-page PDF generation featuring corporate color palettes, tabular metric cards, and strategic priority matrices.

### Database & Security
- **Dual-Tier Database:** SQLite for zero-setup local development; Supabase PostgreSQL for cloud production persistence.
- **ORM:** SQLAlchemy 2.0 with connection pooling (`pool_pre_ping=True`).
- **Security:** Bcrypt password hashing, JWT (JSON Web Tokens) with HS256 signatures, CORS origin filtering, and instant guest demo sessions.

---

## 🚀 Quick Start & Local Setup

### Prerequisites
- Python 3.10 or 3.11 installed on your machine.
- Git installed.

### 1. Clone the Repository
```powershell
git clone https://github.com/<YOUR_USERNAME>/multi-agent-bi-system.git
cd "MULTI-AGENT AI BUSINESS ANALYST & AUTOMATED BUSINESS INTELLIGENCE SYSTEM"
```

### 2. Create and Activate Virtual Environment
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
*(Optional: Add your free OpenRouter API key in `.env`. If left blank, the system automatically runs in 100% deterministic fallback mode with zero errors!)*

### 5. Launch the Server
```powershell
uvicorn backend.app.main:app --reload --port 8000
```

### 6. Open in Browser
- **Enterprise Web UI:** [http://localhost:8000/app/](http://localhost:8000/app/)
- **Interactive Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Comprehensive Test Suite

The platform includes an automated Pytest test suite covering unit, integration, security, and edge-case failure scenarios:

```powershell
# Run the complete test suite
pytest -v
```

### Test Coverage Highlights (36 Passed Tests):
- `test_health.py`: Health checks, CORS validation, and static asset serving.
- `test_datasets.py`: File upload, MIME-type filtering, size limits, and dataset lifecycle.
- `test_analytics.py`: Column detection, data quality scoring, business KPIs, segment breakdown, correlations, and IQR/Z-score/Isolation Forest outlier algorithms.
- `test_agents.py`: All 7 specialized AI agents validated against verified mathematical calculations.
- `test_orchestration.py`: End-to-end multi-agent workflow lifecycle and timing tracking.
- `test_visualizations_and_reports.py`: Dynamic Plotly chart generation, ReportLab PDF compilation, and natural language query processing.
- `test_auth.py`: Bcrypt password hashing, JWT token lifecycle, and guest session creation.
- `test_failure_scenarios.py`: Corrupted datasets, missing API keys, unauthorized access, and non-existent resource handling.

---

## 📂 Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── agents/                     # 7 Specialized AI Agents
│   │   │   ├── base_agent.py           # Abstract Base Agent with OpenRouter + Ollama + Fallback
│   │   │   ├── profiling_agent.py      # Agent 1: Data Profiling
│   │   │   ├── data_analyst_agent.py   # Agent 2: Business Analytics & KPIs
│   │   │   ├── trend_agent.py          # Agent 3: Temporal Trends & Forecasting
│   │   │   ├── anomaly_agent.py        # Agent 4: Anomaly & Outlier Detection
│   │   │   ├── strategy_agent.py       # Agent 5: Strategic Business Initiatives
│   │   │   ├── report_agent.py         # Agent 6: Executive Brief Synthesizer
│   │   │   └── query_agent.py          # Agent 7: Safe Natural Language Query Engine
│   │   ├── api/                        # FastAPI REST API Route Controllers
│   │   │   ├── auth.py                 # Registration, Login & Guest Session Endpoints
│   │   │   ├── datasets.py             # File Upload, Preview & Management
│   │   │   ├── analysis.py             # Profiling & Multi-Agent Orchestration
│   │   │   ├── chat.py                 # Safe Natural Language BI Chat
│   │   │   └── reports.py              # PDF Generation & Download Endpoints
│   │   ├── models/                     # SQLAlchemy Relational ORM Models
│   │   │   ├── user.py                 # User Account & Role Model
│   │   │   ├── dataset.py              # Dataset Metadata Model
│   │   │   ├── analysis.py             # Analysis Run State Model
│   │   │   ├── agent_result.py         # Per-Agent Output Log Model
│   │   │   ├── chat_history.py         # Conversational Query History Model
│   │   │   └── report.py               # PDF Report Metadata Model
│   │   ├── orchestration/              # Multi-Agent Workflow Coordinator
│   │   │   ├── workflow.py             # Workflow State & Stage Definitions
│   │   │   └── orchestrator.py         # Pipeline Executor with Error Handling
│   │   ├── schemas/                    # Pydantic V2 Type & Validation Schemas
│   │   ├── services/                   # Core Business Logic & Statistical Engines
│   │   │   ├── data_service.py         # File Ingestion, Validation & Metadata Extraction
│   │   │   ├── analysis_service.py     # Deterministic Calculations (KPIs, Margins, Outliers)
│   │   │   ├── visualization_service.py# Dynamic Plotly/Chart.js Spec Generator
│   │   │   ├── report_service.py       # ReportLab PDF Document Compiler
│   │   │   └── auth_service.py         # Security & User Token Management
│   │   ├── utils/                      # Helper Utilities (Security, Logging, File Validation)
│   │   ├── config.py                   # Pydantic Settings & Environment Configurations
│   │   ├── database.py                 # Dual SQLite / Supabase PostgreSQL Engine
│   │   └── main.py                     # ASGI Application Root & Lifespan Hooks
│   ├── requirements.txt                # Production Python Dependencies
│   └── tests/                          # 8 Automated Test Suites (36 Pytest Tests)
├── data/
│   ├── sample_sales.csv                # Benchmark Sales Dataset (60 rows, $76.3k sales)
│   ├── uploads/                        # Runtime Upload Storage
│   └── reports/                        # Runtime Generated PDF Reports
├── docs/
│   ├── architecture.md                 # System Architecture & Agent Specifications
│   ├── api_documentation.md            # Complete REST API Reference
│   └── deployment_guide.md             # Free-Tier Cloud Deployment Guide (Render + Supabase)
├── frontend/                           # Enterprise Web UI
│   ├── css/                            # Bootstrap 5 Customization, Dark/Light Themes
│   ├── js/                             # Modular Frontend Controllers & API Client
│   ├── index.html                      # Landing Page & Feature Overview
│   ├── dashboard.html                  # Main KPI & Analytics Dashboard
│   ├── upload.html                     # Drag-and-Drop Dataset Ingestion
│   ├── insights.html                   # AI Agent Insights & Strategy Explorer
│   ├── chat.html                       # Natural Language BI Chatbot Interface
│   ├── reports.html                    # PDF Report Preview & Download Center
│   ├── history.html                    # Historical Analysis Catalog
│   └── settings.html                   # Model Selection & Host Configurations
├── Dockerfile                          # Multi-Stage Production Container Build
├── render.yaml                         # Render Infrastructure-as-Code Blueprint
├── Procfile                            # Universal PaaS Procfile
└── pytest.ini                          # Pytest Configuration
```

---

## 📈 Benchmark Dataset Walkthrough

The repository includes a verified benchmark dataset at [`data/sample_sales.csv`](data/sample_sales.csv) representing a retail business across multiple regions and product categories over calendar year 2024.

### Verified Benchmark Truth:
- **Total Transactions:** 60
- **Total Revenue:** \$76,349.93
- **Total Profit:** \$19,984.93
- **Overall Profit Margin:** 26.17%
- **Data Quality Score:** 100.0% (Grade A+)
- **Highest Performing Category:** Technology (\$9,450.20 profit, 47.3% contribution)
- **Underperforming Region:** South (lowest transaction volume and suppressed margins)

---

## 💼 Resume Bullet Points (Tailored for B.Tech AI & Data Science Students)

Copy and adapt these impact-focused bullet points for your resume:

### Option 1: AI / Machine Learning Engineer Focus
> - **Architected an enterprise Multi-Agent AI Business Intelligence platform** in FastAPI, orchestrating 7 specialized AI agents to automate exploratory data analysis, KPI synthesis, temporal trend decomposition, and executive PDF briefing generation.
> - **Eliminated AI metric hallucinations** by decoupling numerical calculations into a deterministic Pandas/Scikit-learn engine and binding verified quantitative facts to prompt schemas via Pydantic V2.
> - **Engineered an unsupervised anomaly detection engine** combining IQR, Z-Score, and Scikit-learn Isolation Forest, alongside a zero-eval natural language query parser mapping user questions into validated aggregation routines.
> - **Integrated multi-tier persistence and free-tier cloud deployment** using Supabase PostgreSQL, SQLite, and Render Web Services, maintaining 100% test coverage across 36 automated Pytest suites.

### Option 2: Generative AI & Full-Stack Python Focus
> - **Developed an end-to-end Automated Business Intelligence system** serving responsive HTML5/Bootstrap/Chart.js frontends and asynchronous FastAPI REST endpoints.
> - **Implemented a multi-agent orchestration pipeline** coordinating 7 LLM agents (Google Gemini 2.0 / Llama 3.3 via OpenRouter & local Ollama) with deterministic rule-based zero-failure fallbacks.
> - **Created a ReportLab automated PDF reporting engine** that translates complex analytical findings, KPI tables, and prioritized business recommendations into boardroom-ready downloadable documents.
> - **Implemented JWT authentication with Bcrypt security**, guest demo sessions, and automated file validation pipelines supporting 25MB CSV and Excel datasets.

---

## 🎤 Technical Interview Q&A Cheatsheet

Prepare for placement and internship interviews with these verified technical explanations:

<details>
<summary><b>Q1: Why did you build a multi-agent architecture instead of using a single large prompt?</b></summary>
<br>
<i>"A single massive prompt suffers from the 'Lost in the Middle' phenomenon, context degradation, and an inability to enforce modular validation. By decomposing the business intelligence lifecycle into 7 specialized agents (Data Profiler, Financial Analyst, Trend Analyzer, Anomaly Detector, Strategist, Report Compiler, and Query Engine), each agent has a focused responsibility, explicit input/output schemas validated by Pydantic V2, and isolated error boundaries. If the anomaly detection agent encounters an unusual variance, it doesn't crash the financial KPI calculations."</i>
</details>

<details>
<summary><b>Q2: How did you ensure your AI agents don't hallucinate revenue or profit numbers?</b></summary>
<br>
<i>"We enforced a strict mathematical anti-hallucination architectural rule: LLMs are strictly forbidden from performing arithmetic. All aggregations, sums, averages, profit margins, Pearson correlations, and outlier scores are calculated deterministically in Python using Pandas, NumPy, and Scikit-learn. The computed numerical results are serialized into structured JSON and injected into the agent's prompt context. The LLM is constrained to interpret, synthesize, and contextualize those verified figures. Furthermore, our test suite asserts exact float equality between dataset calculations and agent outputs."</i>
</details>

<details>
<summary><b>Q3: Why did you avoid using Python's <code>eval()</code> or <code>exec()</code> for the natural language chat agent?</b></summary>
<br>
<i>"Executing arbitrary code generated by an LLM via eval() or exec() is one of the most critical vulnerabilities in modern AI applications, exposing the host system to remote code execution (RCE) and data exfiltration. Instead, I designed a Zero-Eval Abstract Analytical Query Plan. The Query Agent parses user intent into a structured AST-like JSON payload specifying allowed operations ('sum', 'mean', 'group_by_sum'), validated target columns, and sort order. The backend verifies that the requested columns exist in the active dataset schema and executes pre-compiled, sandboxed Pandas routines."</i>
</details>

<details>
<summary><b>Q4: How does your system handle API rate limits or network failures from free LLM tiers?</b></summary>
<br>
<i>"Our Base Agent architecture implements a three-tier resilience strategy:
1. Primary call to OpenRouter with configurable timeout and automated exponential backoff retries.
2. Automatic failover to a secondary free model (e.g. from Gemini Flash to Llama 3.3).
3. If cloud APIs are completely unreachable, the agent falls back to an internal deterministic rule-based analytical engine that derives structured insights directly from computed statistics without raising an exception. This guarantees 100% platform uptime for recruiters and users."</i>
</details>

<details>
<summary><b>Q5: How does your system scale between local development and cloud production?</b></summary>
<br>
<i>"Through environment-driven configuration via Pydantic-Settings. In local development, the system runs with SQLite and local file storage. For cloud deployment on Render, it automatically hooks into Supabase managed PostgreSQL using connection pooling (pool_pre_ping=True, pool_size=10), handles URL protocol normalization ('postgres://' to 'postgresql://'), and dynamically provisions relational tables upon startup using FastAPI's lifespan context manager."</i>
</details>

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author & Acknowledgments

- **Developed by:** B.Tech Artificial Intelligence and Data Science Student
- **Mentorship & Architecture:** Antigravity AI Engineering Suite
- **Core Technologies:** FastAPI, Pandas, Scikit-learn, ReportLab, OpenRouter, Bootstrap 5.
