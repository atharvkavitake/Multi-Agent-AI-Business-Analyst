# REST API Documentation
## Multi-Agent AI Business Analyst & Automated Business Intelligence System

The Multi-Agent AI BI System exposes a fully documented, type-safe REST API built on FastAPI and Pydantic V2.

- **Base URL (Local):** `http://localhost:8000/api`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc Specification:** `http://localhost:8000/redoc`
- **OpenAPI JSON Schema:** `http://localhost:8000/api/openapi.json`

---

## 1. Authentication Endpoints (`/api/auth`)

Authentication uses HTTP Bearer tokens (JWT HS256). For all protected endpoints, pass the header:
```http
Authorization: Bearer <your_jwt_token>
```

### `POST /api/auth/register`
Register a new user account.
- **Request Body:**
  ```json
  {
    "email": "analyst@enterprise.com",
    "password": "StrongPassword123!",
    "full_name": "Senior Business Analyst"
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": "usr_9f8e7d6c",
    "email": "analyst@enterprise.com",
    "full_name": "Senior Business Analyst",
    "is_active": true,
    "created_at": "2026-11-09T10:00:00"
  }
  ```

---

### `POST /api/auth/login`
Authenticate with email and password to receive a JWT access token.
- **Request Body (OAuth2 Form or JSON):**
  ```json
  {
    "email": "analyst@enterprise.com",
    "password": "StrongPassword123!"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in_minutes": 1440,
    "user": {
      "id": "usr_9f8e7d6c",
      "email": "analyst@enterprise.com",
      "full_name": "Senior Business Analyst"
    }
  }
  ```

---

### `POST /api/auth/guest`
Instant guest session generation for recruiters and demo evaluations. No registration needed.
- **Response (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in_minutes": 1440,
    "user": {
      "id": "guest_3a8b7c",
      "email": "guest_3a8b7c@demo.antigravity.ai",
      "full_name": "Guest Analyst"
    }
  }
  ```

---

## 2. Dataset Management Endpoints (`/api/datasets`)

### `POST /api/datasets/upload`
Upload a CSV or Excel dataset with real-time MIME-type validation, size bounds checks, and automatic schema profiling.
- **Content-Type:** `multipart/form-data`
- **Form Fields:** `file` (File binary, max 25MB, `.csv`, `.xlsx`, `.xls`)
- **Response (`201 Created`):**
  ```json
  {
    "dataset_id": "ds_4d78a9c2",
    "filename": "sample_sales.csv",
    "file_size_bytes": 4820,
    "row_count": 60,
    "column_count": 7,
    "columns": [
      {
        "name": "Transaction_Date",
        "inferred_type": "datetime",
        "sample_values": ["2024-01-15", "2024-01-16"]
      },
      {
        "name": "Revenue",
        "inferred_type": "numerical",
        "sample_values": [1250.50, 480.00]
      }
    ],
    "preview_rows": [
      {"Transaction_Date": "2024-01-15", "Category": "Technology", "Revenue": 1250.50}
    ]
  }
  ```

---

### `GET /api/datasets`
List all uploaded datasets available to the authenticated user.
- **Response (`200 OK`):** Array of dataset metadata objects.

---

### `GET /api/datasets/{dataset_id}`
Retrieve complete metadata and head preview for a specific dataset.
- **Response (`200 OK`):** Dataset metadata object.

---

### `DELETE /api/datasets/{dataset_id}`
Permanently delete an uploaded dataset file and all associated database records.
- **Response (`200 OK`):** `{"message": "Dataset successfully deleted"}`

---

## 3. Analysis & Multi-Agent Orchestration (`/api/analysis`)

### `POST /api/analysis/{dataset_id}/profile`
Deterministic structural analysis and data quality audit.
- **Response (`200 OK`):**
  ```json
  {
    "dataset_id": "ds_4d78a9c2",
    "shape": {"rows": 60, "columns": 7},
    "data_quality_score": 100.0,
    "quality_grade": "A+",
    "missing_values_count": 0,
    "duplicate_rows_count": 0,
    "inferred_domain": "Sales & Retail Operations",
    "columns_summary": { ... }
  }
  ```

---

### `POST /api/analysis/{dataset_id}/run`
Trigger the central Agent Orchestrator to execute the 7 specialized AI agents in structured sequence with deterministic calculation binding.
- **Request Body (Optional):**
  ```json
  {
    "focus_areas": ["revenue", "profitability", "regional_performance"],
    "llm_model": "google/gemini-2.0-flash-exp:free"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "analysis_id": "anl_82e4a1b0",
    "dataset_id": "ds_4d78a9c2",
    "status": "COMPLETED",
    "total_execution_time_seconds": 1.42,
    "agents_executed": 7,
    "kpi_summary": {
      "total_revenue": 76349.93,
      "total_profit": 19984.93,
      "overall_margin_percent": 26.17,
      "total_transactions": 60
    },
    "agent_results": {
      "profiling_agent": { ... },
      "data_analyst_agent": { ... },
      "trend_agent": { ... },
      "anomaly_agent": { ... },
      "strategy_agent": { ... },
      "report_agent": { ... }
    }
  }
  ```

---

### `GET /api/analysis/{analysis_id}/status`
Query the real-time execution status, stage, and outputs of an analysis run.
- **Response (`200 OK`):** Full analysis state schema.

---

## 4. Visualizations Engine (`/api/visualizations`)

### `GET /api/analysis/{dataset_id}/visualizations`
Generate Plotly-compatible interactive chart specifications dynamically tailored to the dataset's numerical distributions and temporal columns.
- **Response (`200 OK`):**
  ```json
  {
    "dataset_id": "ds_4d78a9c2",
    "charts": [
      {
        "id": "revenue_trend_chart",
        "title": "Revenue Performance Over Time",
        "chart_type": "line",
        "data": { ... },
        "layout": { "xaxis": {"title": "Date"}, "yaxis": {"title": "Revenue ($)"} }
      },
      {
        "id": "category_breakdown_chart",
        "title": "Category Contribution",
        "chart_type": "bar",
        "data": { ... }
      }
    ]
  }
  ```

---

## 5. Safe Natural Language BI Chat (`/api/chat`)

### `POST /api/chat/query`
Natural language query engine utilizing a zero-eval Abstract Query Plan. No arbitrary Python execution.
- **Request Body:**
  ```json
  {
    "dataset_id": "ds_4d78a9c2",
    "query": "Which category generated the highest profit?"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "query": "Which category generated the highest profit?",
    "answer": "Technology generated the highest total profit of $9,450.20, accounting for 47.3% of cumulative profits across all categories.",
    "operation_performed": "group_by_sum",
    "target_column": "Profit",
    "group_column": "Category",
    "calculated_result": {
      "Technology": 9450.20,
      "Office Supplies": 6120.45,
      "Furniture": 4414.28
    },
    "chart_suggestion": "bar_chart"
  }
  ```

---

## 6. Executive PDF Report Generation (`/api/reports`)

### `POST /api/reports/{analysis_id}/generate`
Compiles an enterprise-grade multi-page PDF executive brief via ReportLab.
- **Response (`200 OK`):**
  ```json
  {
    "report_id": "rep_3b19e2f4",
    "analysis_id": "anl_82e4a1b0",
    "file_path": "/app/data/reports/report_anl_82e4a1b0.pdf",
    "download_url": "/api/reports/rep_3b19e2f4/download"
  }
  ```

---

### `GET /api/reports/{report_id}/download`
Download the compiled PDF report directly with appropriate content disposition headers.
- **Response (`200 OK`):** Binary stream (`application/pdf`).
