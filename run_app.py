import os
import subprocess
import time
import httpx
import signal
import sys
from dotenv import load_dotenv

# Load environment variables (API Key)
load_dotenv()

SERVICES = {
    "csv_ingestor": "http://localhost:5001",
    "db_validator": "http://localhost:5002",
    "schema_manager": "http://localhost:5003",
    "query_service": "http://localhost:5004",
    "llm_adapter": "http://localhost:5005",
}

def start_services():
    """Starts all microservices as background processes."""
    print("🚀 Starting microservices...")
    processes = []
    env = os.environ.copy()
    env["PYTHONPATH"] = f".:{env.get('PYTHONPATH', '')}"
    
    for service, url in SERVICES.items():
        # Using sys.executable to ensure we use the same python interpreter
        proc = subprocess.Popen(
            [sys.executable, f"services/{service}/app.py"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        processes.append(proc)
    
    # Wait for services to respond
    for name, url in SERVICES.items():
        ready = False
        print(f"  - Waiting for {name}...", end="", flush=True)
        for _ in range(30): # LLM adapter can be slow to start
            try:
                resp = httpx.get(url, timeout=1.0)
                if resp.status_code == 200:
                    ready = True
                    break
            except:
                pass
            time.sleep(1)
            print(".", end="", flush=True)
        
        if ready:
            print(" ✅")
        else:
            print(" ❌ FAILED")
            stop_services(processes)
            sys.exit(1)
            
    print("\n✨ All services are online and ready!")
    return processes

def stop_services(processes):
    """Terminates all service processes."""
    print("\n🛑 Shutting down microservices...")
    for p in processes:
        try:
            if os.name != 'nt':
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            else:
                p.terminate()
        except:
            pass

def run_query(question):
    """Orchestrates the NL -> SQL -> Data flow."""
    # 1. Translate NL to SQL via LLM Adapter
    try:
        print(f"\n🔍 Translating question to SQL...")
        resp = httpx.post(f"{SERVICES['llm_adapter']}/translate", json={"question": question}, timeout=30.0)
        if resp.status_code != 200:
            error_msg = resp.json().get("detail", "Unknown error")
            print(f"❌ LLM Error: {error_msg}")
            return
        
        sql = resp.json()["sql"]
        print(f"🤖 Generated SQL: {sql}")
    except Exception as e:
        print(f"❌ Connection error to LLM Adapter: {e}")
        return

    # 2. Execute SQL Query via Query Service
    try:
        print(f"⚙️  Executing query...")
        resp = httpx.post(f"{SERVICES['query_service']}/query", json={"query": sql}, timeout=10.0)
        if resp.status_code != 200:
            error_msg = resp.json().get("detail", "Unknown error")
            print(f"❌ Query Error: {error_msg}")
            return
        
        data = resp.json()["data"]
        columns = resp.json()["columns"]
        
        if not data:
            print("ℹ️  No results found for this query.")
            return

        # 3. Format and Display Results
        print("\n📊 Results:")
        # Calculate column widths
        widths = []
        for i, col in enumerate(columns):
            val_widths = [len(str(row[i])) for row in data]
            widths.append(max(len(col), max(val_widths) if val_widths else 0))

        # Print header
        header = " | ".join(f"{col:<{widths[i]}}" for i, col in enumerate(columns))
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in data:
            print(" | ".join(f"{str(val):<{widths[i]}}" for i, val in enumerate(row)))
            
    except Exception as e:
        print(f"❌ Connection error to Query Service: {e}")

def ingest_csv(file_path, table_name):
    """Sends a CSV file to the Ingestor service."""
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return

    try:
        print(f"📤 Ingesting {file_path} into table '{table_name}'...")
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "text/csv")}
            resp = httpx.post(f"{SERVICES['csv_ingestor']}/upload", 
                             params={"table_name": table_name}, 
                             files=files, 
                             timeout=60.0)
            
        if resp.status_code == 200:
            print(f"✅ Success: {resp.json().get('message')}")
        else:
            print(f"❌ Ingestion Failed: {resp.text}")
    except Exception as e:
        print(f"❌ Connection error to Ingestor: {e}")

def main():
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ ERROR: GEMINI_API_KEY not found in environment or .env file.")
        print("Please create a .env file with GEMINI_API_KEY=your_key")
        sys.exit(1)
    
    procs = start_services()
    
    try:
        print("\n" + "="*50)
        print("💬 Welcome to the Natural Language DB Interface!")
        print("Commands:")
        print("  - Type a question to query (e.g., 'Who is the oldest user?')")
        print("  - Type 'ingest <file.csv> <table_name>' to load data")
        print("  - Type 'exit' or 'quit' to stop.")
        print("="*50)
        
        while True:
            try:
                user_input = input("\n💬 Query: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                if user_input.lower().startswith("ingest "):
                    parts = user_input.split()
                    if len(parts) == 3:
                        ingest_csv(parts[1], parts[2])
                    else:
                        print("❌ Usage: ingest <file_path> <table_name>")
                else:
                    run_query(user_input)
            except EOFError:
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        stop_services(procs)
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
