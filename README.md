# DB with LLM

A natural language interface for querying SQLite databases using LLM integration.

## Project Plan

### Step 1: Define the structure of your Github project
Organize the repository into logical modules for Control, Data, and Information layers.

### Step 2: Define the APIs of each module
Standardize the interfaces for communication between the following modules:
*   **Control:** Orchestrates the flow between the user, LLM, and database.
*   **Data:** Handles low-level database operations (SQLite).
*   **Information:** Manages schema metadata and LLM adaptations.

### Step 3: Build Unit Tests for each component
Implement comprehensive unit tests using mocked data to ensure each component functions independently before integration.

### Step 4: Implement modules in order
1.  **CSV Loader:** Utility to ingest data into the system.
2.  **SQLite Setup:** Core database initialization.
3.  **Schema Manager:** Handles table definitions and metadata extraction.
4.  **Query Service:** Executes SQL and manages results.
5.  **LLM Adapter:** Translates natural language to SQL and vice-versa.
6.  **CLI:** The primary user interface (Final implementation).
