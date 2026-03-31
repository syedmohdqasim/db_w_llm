# DB with LLM

A microservices-based system that allows users to query SQLite databases using natural language, powered by Google Gemini.

## System Architecture

The project is structured as a set of independent FastAPI microservices, each handling a specific part of the data-to-information lifecycle.

### Core Services
*   **CSV Ingestor (Port 5001):** Loads structured CSV data into the SQLite database (`project_db.db`) and automatically infers the schema.
*   **DB Validator (Port 5002):** A security and syntax layer. It ensures SQL queries are syntactically correct and blocks destructive operations (e.g., `DROP`, `DELETE`, `UPDATE`).
*   **Schema Manager (Port 5003):** Extracts table names and `CREATE TABLE` statements from the database to provide context for the LLM.
*   **Query Service (Port 5004):** Executes validated SQL queries against the database and returns structured results (columns and data).
*   **LLM Adapter (Port 5005):** The "brain" of the system. It uses **Gemini 2.5 Flash** to translate natural language questions into precise SQL queries by retrieving the database schema from the Schema Manager.

---

## Query Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant LLM_Adapter as LLM Adapter (5005)
    participant Schema_Mgr as Schema Manager (5003)
    participant Gemini as Google Gemini API
    participant Validator as DB Validator (5002)
    participant Query_Svc as Query Service (5004)
    participant DB as SQLite DB

    User->>LLM_Adapter: Natural Language Question
    LLM_Adapter->>Schema_Mgr: Get Current Schema
    Schema_Mgr-->>LLM_Adapter: SQL Table Definitions
    LLM_Adapter->>Gemini: Question + Schema Context
    Gemini-->>LLM_Adapter: Generated SQL Query
    LLM_Adapter-->>User: SQL Query string
    
    Note over User, DB: Execution Flow
    
    User->>Validator: SQL Query
    Validator->>Validator: Check Syntax & Security (DROP/DELETE/etc.)
    alt is Valid
        Validator-->>User: Validated OK
        User->>Query_Svc: SQL Query
        Query_Svc->>DB: Execute SQL
        DB-->>Query_Svc: Data Rows
        Query_Svc-->>User: Structured Results (JSON)
    else is Invalid/Malicious
        Validator-->>User: 403 Forbidden / 400 Syntax Error
    end
```

---

## Getting Started

### 1. Prerequisites
*   Python 3.10+
*   Google Gemini API Key

### 2. Setup
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Create a `.env` file in the root directory:
    ```bash
    GEMINI_API_KEY=your_api_key_here
    ```

### 3. Running the System
You can start all services and verify the system using the comprehensive integration test:
```bash
python tests/comprehensive_test.py
```

### 4. Testing
To run the full suite of unit tests, ensure your `PYTHONPATH` includes the project root:
```bash
export PYTHONPATH=$PYTHONPATH:.
pytest services/*/tests
```

To run the end-to-end integration tests:
```bash
python tests/comprehensive_test.py
```

## Security
The **DB Validator** service acts as a safety guardrail, rejecting any query containing restricted keywords like `DROP`, `DELETE`, `UPDATE`, or `TRUNCATE` to ensure the integrity of the data remains intact during natural language interactions.
