# Financial Intelligence Agentic System - How It Works

## **Simple Overview**

This system lets business analysts ask financial questions in plain English and automatically get SQL queries, data results, and visualizations—without writing any code.

---

## **Input → Output Flow**

### **INPUT**
A user sends a natural language question via API:
```json
{
  "question": "Show revenue by segment for 2024-Q1",
  "user_id": "analyst_123",
  "role": "analyst"
}
```

### **OUTPUT**
The system returns:
```json
{
  "sql_query": "SELECT segment, SUM(revenue_usd) FROM financials_quarterly WHERE fiscal_quarter='2024-Q1' GROUP BY segment",
  "execution": {
    "rows": [{"segment": "Cloud", "revenue_usd": 1250}, ...],
    "row_count": 2,
    "latency_ms": 95
  },
  "visualization": {
    "kind": "bar",
    "spec": {...chart config...},
    "insight_summary": "Top segment: Cloud"
  }
}
```

---

## **How it Works?**

### **1. Security Check** (`RBACService`)
- Verifies the user's role is in the allowed list (e.g., "analyst", "admin")
- **If rejected:** Returns 403 Forbidden

### **2. Schema Discovery** (`SchemaDiscoveryService`)
- Loads database schema from:
  - **Snowflake** (if configured)
  - **Athena** (if configured)
  - **Fallback:** `src/fia_agent/data/sample_schema.yaml`
- Returns table/column definitions so the AI knows what data exists

### **3. Memory Recall** (`MemoryManager`)
- Checks conversation history for context
- Retrieves past successful queries from this user
- **Example:** If they asked "Show revenue" before, it remembers the SQL pattern

### **4. SQL Generation** (`QueryGenerationAgent`)
- Uses `Text2SQLTranslator` to convert the question into SQL
- **How it decides:**
  - Matches keywords ("revenue", "segment", "2024-Q1") to schema
  - Uses heuristics like: *"If question mentions 'segment', add GROUP BY segment"*
  - (Can be upgraded to use a real LLM like GPT-4)
- **Output:** `SELECT segment, SUM(revenue_usd) ... WHERE fiscal_quarter='2024-Q1'`

### **5. SQL Execution** (`QueryVerificationAgent`)
- Runs the SQL query via `QueryExecutor`
- Routes to:
  - **Snowflake** (`SnowflakeClient`)
  - **Athena** (`AthenaClient`)
  - **Mock data** (for testing/demo mode)
- **Security step:** Redacts sensitive columns (e.g., "salary", "ssn")

### **6. Self-Healing** (`ConductorGraph`)
- **If SQL fails** (syntax error, missing table, etc.):
  - Captures the error message
  - Calls `Text2SQLTranslator.repair_sql`
  - Tries again (up to 2 attempts)
- **Tracks corrections:** Records what was fixed in `self_corrections` array

### **7. Visualization** (`VisualizationAgent`)
- Decides how to present results:
  - **"chart"** → Bar/line chart spec (compatible with Vega-Lite)
  - **"narrative"** → Text summary: *"Returned 2 rows in 95ms"*
  - **"table"** (default) → Raw data rows
- Adds an insight like *"Top segment: Cloud"*

### **8. Audit Logging** (`AuditService`)
- Records:
  - Who asked what
  - SQL generated
  - Success/failure status
  - Latency
- **Can be streamed** to monitoring dashboards or SIEM tools

### **9. Response Assembly**
- Combines:
  - Generated SQL
  - Execution results
  - Visualization spec
  - Schema used
  - Self-correction notes (if any)
- Returns JSON to the user

---

## **The Orchestrator (LangGraph)**

All these steps are coordinated by `ConductorGraph` using **LangGraph**, which:
- Chains agents in sequence: `generate → execute → (repair if needed) → visualize → finalize`
- Maintains state across steps (SQL query, errors, schema, etc.)
- Decides when to retry vs. move forward

**Visual Flow:**
```
┌─────────────┐
│   INPUT     │ Question + User Info
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Security   │ Check role
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Schema    │ Load tables/columns
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Generate   │ NL → SQL
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Execute    │ Run SQL on warehouse
└──────┬──────┘
       │
       ├──[Error?]──┐
       │            ▼
       │      ┌─────────────┐
       │      │   Repair    │ Fix SQL & retry
       │      └──────┬──────┘
       │             │
       ▼             ▼
┌─────────────┐
│  Visualize  │ Build chart/table
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Audit     │ Log everything
└──────┬──────┘
       │
       ▼
   OUTPUT (JSON)
```

---

## **Model Context Protocol (MCP)**

The `mcp/` directory exposes tools that external AI systems (like Claude Desktop) can call:
- **`list_financial_tables`** → Get schema
- **`run_financial_query`** → Execute a question

This lets you integrate FIAS into larger AI workflows.

---

