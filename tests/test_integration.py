import pytest
import subprocess
import time
import httpx
import os
import signal

# Service configuration
SERVICES = {
    "csv_ingestor": "http://localhost:5001",
    "db_validator": "http://localhost:5002",
    "schema_manager": "http://localhost:5003",
    "query_service": "http://localhost:5004",
    "llm_adapter": "http://localhost:5005",
}

@pytest.fixture(scope="module", autouse=True)
def manage_services():
    """Fixture to start all services before tests and stop them after."""
    if os.path.exists("integration_db.db"):
        os.remove("integration_db.db")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f".:{env.get('PYTHONPATH', '')}"
    
    processes = []
    for service, url in SERVICES.items():
        # Use a separate DB for integration tests
        s_env = env.copy()
        s_env["DB_PATH"] = "integration_db.db"
        
        proc = subprocess.Popen(
            ["python", f"services/{service}/app.py"],
            env=s_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid # Create a process group for clean shutdown
        )
        processes.append(proc)
    
    # Wait for all services to be ready
    print("\nWaiting for services to boot...")
    for i, (name, url) in enumerate(SERVICES.items()):
        current_proc = processes[i]
        ready = False
        # Increase wait time for the LLM adapter (it imports heavy libraries)
        wait_limit = 20 if name == "llm_adapter" else 10
        for _ in range(wait_limit):
            try:
                resp = httpx.get(url, timeout=1.0)
                if resp.status_code == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(1)
        if not ready:
            print(f"FAILED: Service {name} at {url} did not respond.")
            # Check if process is still running
            if current_proc.poll() is not None:
                print(f"Service {name} process exited with code {current_proc.poll()}")
            for p_to_kill in processes:
                try:
                    os.killpg(os.getpgid(p_to_kill.pid), signal.SIGTERM)
                except Exception:
                    pass
            pytest.fail(f"Service {name} failed to start at {url}")

    yield # This is where the tests run
    
    # Shutdown all services
    for p in processes:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    
    if os.path.exists("integration_db.db"):
        os.remove("integration_db.db")

@pytest.fixture(scope="module")
def setup_data():
    """Ingests initial test data."""
    # Table 1: Employees
    emp_csv = "employees_test.csv"
    with open(emp_csv, "w") as f:
        f.write("id,name,department,salary\n1,Alice,Engineering,120000\n2,Bob,Marketing,90000\n3,Charlie,Engineering,110000")
    
    # Table 2: Departments
    dept_csv = "depts_test.csv"
    with open(dept_csv, "w") as f:
        f.write("dept_id,dept_name,location\n1,Engineering,Building A\n2,Marketing,Building B")

    with open(emp_csv, "rb") as f:
        httpx.post(f"{SERVICES['csv_ingestor']}/upload?table_name=employees", files={"file": f})
    with open(dept_csv, "rb") as f:
        httpx.post(f"{SERVICES['csv_ingestor']}/upload?table_name=departments", files={"file": f})
    
    os.remove(emp_csv)
    os.remove(dept_csv)

@pytest.mark.integration
def test_basic_query_flow(setup_data):
    """Verifies that a natural language question correctly returns data."""
    question = "Who is the highest paid employee in Engineering?"

    # 1. Translate NL to SQL
    resp = httpx.post(f"{SERVICES['llm_adapter']}/translate", json={"question": question})
    if resp.status_code != 200:
        print(f"Error Detail: {resp.text}")
    assert resp.status_code == 200
    sql = resp.json()["sql"]

    # 2. Validate SQL
    val_resp = httpx.post(f"{SERVICES['db_validator']}/validate", json={"query": sql})
    assert val_resp.status_code == 200

    # 3. Execute and Check Results
    query_resp = httpx.post(f"{SERVICES['query_service']}/query", json={"query": sql})
    assert query_resp.status_code == 200
    data = query_resp.json()["data"]

    # Assert result contains 'Alice'
    assert any("Alice" in str(row) for row in data)

@pytest.mark.integration
def test_join_query(setup_data):
    """Tests if LLM can handle joining two tables."""
    question = "Where is Bob's department located?"

    resp = httpx.post(f"{SERVICES['llm_adapter']}/translate", json={"question": question})
    sql = resp.json()["sql"]

    query_resp = httpx.post(f"{SERVICES['query_service']}/query", json={"query": sql})
    data = query_resp.json()["data"]

    # Bob is in Marketing -> Building B
    assert any("Building B" in str(row) for row in data)

@pytest.mark.integration
def test_security_rejection(setup_data):
    """Tests that malicious queries are caught by the Query Service via the Validator."""
    question = "Delete all employees"

    # 1. Get the query from LLM
    resp = httpx.post(f"{SERVICES['llm_adapter']}/translate", json={"question": question})
    sql = resp.json()["sql"]

    # 2. Try to run it directly through the Query Service. 
    # It should call the Validator and return a 403.
    query_resp = httpx.post(f"{SERVICES['query_service']}/query", json={"query": sql})

    assert query_resp.status_code == 403
    assert "Security Violation" in query_resp.json()["detail"]

