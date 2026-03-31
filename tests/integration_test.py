import subprocess
import time
import httpx
import os
import sqlite3

# URLs for the services
SERVICES = {
    "csv_ingestor": "http://localhost:5001",
    "db_validator": "http://localhost:5002",
    "schema_manager": "http://localhost:5003",
    "query_service": "http://localhost:5004",
    "llm_adapter": "http://localhost:5005",
}

def start_services(env):
    processes = []
    # Start each service in the background
    processes.append(subprocess.Popen(["python", "services/csv_ingestor/app.py"], env=env, stdout=subprocess.DEVNULL))
    processes.append(subprocess.Popen(["python", "services/db_validator/app.py"], env=env, stdout=subprocess.DEVNULL))
    processes.append(subprocess.Popen(["python", "services/schema_manager/app.py"], env=env, stdout=subprocess.DEVNULL))
    processes.append(subprocess.Popen(["python", "services/query_service/app.py"], env=env, stdout=subprocess.DEVNULL))
    processes.append(subprocess.Popen(["python", "services/llm_adapter/app.py"], env=env, stdout=subprocess.DEVNULL))
    return processes

def run_integration_test():
    print("--- Starting Integration Test ---")
    
    # 1. Setup clean environment
    if os.path.exists("project_db.db"): os.remove("project_db.db")
    
    # 2. Start services
    print("Starting background services...")
    env = os.environ.copy()
    env["PYTHONPATH"] = f".:{env.get('PYTHONPATH', '')}"
    
    procs = start_services(env)
    
    print("Waiting for services to be ready (up to 15 seconds)...")
    for name, url in SERVICES.items():
        ready = False
        for _ in range(15):
            try:
                if httpx.get(url).status_code == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(1)
        if not ready:
            print(f"FAILED: Service {name} at {url} did not start.")
            for p in procs: p.terminate()
            return

    try:
        # 3. Step 1: Ingest Data
        print("\n[Step 1] Ingesting CSV...")
        with open("test_data.csv", "w") as f:
            f.write("id,product,price,stock\n1,Laptop,1200,5\n2,Mouse,25,50\n3,Keyboard,75,20")
        
        with open("test_data.csv", "rb") as f:
            resp = httpx.post(f"{SERVICES['csv_ingestor']}/upload?table_name=inventory", files={"file": f})
        print(f"CSV Ingestor Response: {resp.status_code} - {resp.json()['message']}")

        # 4. Step 2: Verify Schema
        print("\n[Step 2] Verifying Schema Manager...")
        resp = httpx.get(f"{SERVICES['schema_manager']}/tables")
        print(f"Tables in DB: {resp.json()['tables']}")

        # 5. Step 3: LLM Translation
        print("\n[Step 3] Asking LLM for a query...")
        question = "What is the total value of stock for all products?"
        resp = httpx.post(f"{SERVICES['llm_adapter']}/translate", json={"question": question})
        print(f"LLM Adapter Status: {resp.status_code}")
        print(f"LLM Adapter Body: {resp.text}")
        sql = resp.json()["sql"]
        print(f"Question: {question}")
        print(f"Generated SQL: {sql}")

        # 6. Step 4: Validate SQL
        print("\n[Step 4] Validating SQL...")
        resp = httpx.post(f"{SERVICES['db_validator']}/validate", json={"query": sql})
        print(f"Validator Response: {resp.json()['message']}")

        # 7. Step 5: Execute Query
        print("\n[Step 5] Executing Query...")
        resp = httpx.post(f"{SERVICES['query_service']}/query", json={"query": sql})
        data = resp.json()
        print(f"Result Columns: {data['columns']}")
        print(f"Result Data: {data['data']}")

        print("\n--- INTEGRATION TEST SUCCESSFUL ---")

    except Exception as e:
        print(f"\n--- INTEGRATION TEST FAILED ---")
        print(f"Error: {e}")
    finally:
        # Cleanup
        print("\nShutting down services...")
        for p in procs: p.terminate()
        if os.path.exists("test_data.csv"): os.remove("test_data.csv")

if __name__ == "__main__":
    run_integration_test()
