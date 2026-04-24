(#!/usr/bin/env python3
"""
T10 AIRPS - Complete Auto-Startup Script
Starts everything needed: Ollama, Backend, Frontend, and opens browser
"""
import subprocess
import sys
import time
import webbrowser
import requests
import os
from pathlib import Path

class Starter:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.processes = []

    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")

    def start_ollama(self):
        """Start Ollama server"""
        self.print_header("Starting Ollama")

        try:
            # Check if already running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                print("[OK] Ollama is already running!")
                return True
        except:
            pass

        print("Starting Ollama server...")
        try:
            if sys.platform == "win32":
                # Windows
                process = subprocess.Popen(
                    ["cmd", "/c", "ollama serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Mac/Linux
                process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            self.processes.append(process)
            print("[OK] Ollama started (PID: %d)" % process.pid)

            # Wait for Ollama to be ready
            print("Waiting for Ollama to be ready...")
            for i in range(30):
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=1)
                    if response.status_code == 200:
                        print("[OK] Ollama is ready!")
                        return True
                except:
                    pass
                time.sleep(1)
                print(".", end="", flush=True)

            print("\n[WARN] Ollama may still be starting. Continuing...")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to start Ollama: {e}")
            print("Make sure Ollama is installed from: https://ollama.ai")
            return False

    def check_mistral_model(self):
        """Check if Mistral model is available"""
        self.print_header("Checking Mistral Model")

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            data = response.json()

            if data.get("models"):
                for model in data["models"]:
                    if "mistral" in model.get("name", "").lower():
                        print(f"[OK] Mistral model found: {model.get('name')}")
                        return True

            print("[WARN] Mistral model not found")
            print("Attempting to download Mistral (4GB)...")
            print("This may take 5-15 minutes. Progress shows in Ollama window.\n")

            try:
                requests.post(
                    "http://localhost:11434/api/pull",
                    json={"name": "mistral"},
                    timeout=300
                )
                print("[OK] Model download initiated!")
                return True
            except:
                print("[WARN] Could not auto-download. Run manually: ollama pull mistral")
                return True  # Continue anyway

        except Exception as e:
            print(f"✗ Model check failed: {e}")
            return False

    def start_backend(self):
        """Start FastAPI backend"""
        self.print_header("Starting Backend")

        print(f"Backend directory: {self.backend_dir}")

        try:
            # Change to backend directory
            os.chdir(self.backend_dir)

            # Start backend
            if sys.platform == "win32":
                process = subprocess.Popen(
                    ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                process = subprocess.Popen(
                    ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

            self.processes.append(process)
            print(f"✓ Backend started (PID: {process.pid})")

            # Wait for backend to be ready
            print("Waiting for backend to be ready...")
            for i in range(20):
                try:
                    response = requests.get("http://localhost:8000/api/health", timeout=1)
                    if response.status_code == 200:
                        print("✓ Backend is ready!")
                        return True
                except:
                    pass
                time.sleep(1)
                print(".", end="", flush=True)

            print("\n⚠ Backend may still be starting. Continuing...")
            return True

        except Exception as e:
            print(f"✗ Failed to start backend: {e}")
            return False

    def start_frontend(self):
        """Start Vite frontend"""
        self.print_header("Starting Frontend")

        print(f"Frontend directory: {self.frontend_dir}")

        try:
            os.chdir(self.frontend_dir)

            # Start frontend
            if sys.platform == "win32":
                process = subprocess.Popen(
                    ["npm", "run", "dev"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                process = subprocess.Popen(
                    ["npm", "run", "dev"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

            self.processes.append(process)
            print(f"✓ Frontend started (PID: {process.pid})")

            # Wait a bit for frontend to start
            print("Waiting for frontend to be ready...")
            time.sleep(5)
            print("✓ Frontend is ready!")
            return True

        except Exception as e:
            print(f"✗ Failed to start frontend: {e}")
            return False

    def open_browser(self):
        """Open browser to the application"""
        self.print_header("Opening Browser")

        url = "http://localhost:5173"
        print(f"Opening {url}...")

        try:
            webbrowser.open(url)
            print("✓ Browser opened!")
        except Exception as e:
            print(f"⚠ Could not open browser: {e}")
            print(f"Please open manually: {url}")

    def run(self):
        """Run complete startup sequence"""
        print("\n" + "="*60)
        print("  T10 AIRPS - Complete Auto-Startup")
        print("="*60)

        # Step 1: Start Ollama
        if not self.start_ollama():
            print("\n✗ Failed to start Ollama. Please install from https://ollama.ai")
            return False

        # Step 2: Check Mistral model
        time.sleep(2)
        self.check_mistral_model()

        # Step 3: Start backend
        time.sleep(2)
        if not self.start_backend():
            print("\n⚠ Backend failed. Check Python installation and port 8000")

        # Step 4: Start frontend
        time.sleep(3)
        if not self.start_frontend():
            print("\n⚠ Frontend failed. Check npm installation")

        # Step 5: Open browser
        time.sleep(3)
        self.open_browser()

        # Summary
        self.print_header("System Started!")
        print("✓ Ollama server is running")
        print("✓ Backend API is running on http://localhost:8000")
        print("✓ Frontend is running on http://localhost:5173")
        print("✓ Browser opened")
        print()
        print("="*60)
        print("  T10 AIRPS Chatbot is Ready!")
        print("="*60)
        print()
        print("Try these commands in the chatbot:")
        print("  • 'Create critical incident'")
        print("  • 'Show open incidents'")
        print("  • Click 🎤 for voice input")
        print("  • Click 🔊 for voice output")
        print()
        print("Press Ctrl+C to stop all services")
        print()

        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.print_header("Shutting Down")
            print("Stopping all services...")
            for process in self.processes:
                try:
                    process.terminate()
                except:
                    pass
            print("✓ Services stopped")
            return True

if __name__ == "__main__":
    starter = Starter()
    success = starter.run()
    sys.exit(0 if success else 1)
