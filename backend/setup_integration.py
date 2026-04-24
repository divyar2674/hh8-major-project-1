#!/usr/bin/env python3
"""
T10 AIRPS - Ollama Integration Setup & Verification
Fast automated setup and testing
"""
import subprocess
import requests
import time
import sys
import json
import os
import asyncio

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}→ {text}{Colors.END}")

async def check_ollama_running():
    """Check if Ollama is running on port 11434"""
    print_info("Checking if Ollama is running...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print_success("Ollama is running!")
            return True
    except requests.exceptions.ConnectionError:
        pass
    except Exception as e:
        pass

    print_error("Ollama is not running")
    return False

async def check_ollama_installed():
    """Check if Ollama is installed"""
    print_info("Checking if Ollama is installed...")

    import platform
    system = platform.system()

    if system == "Windows":
        import shutil
        ollama_exe = shutil.which("ollama")
        if ollama_exe:
            print_success(f"Ollama found at: {ollama_exe}")
            return True

        # Check default Windows path
        default_path = os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe")
        if os.path.exists(default_path):
            print_success(f"Ollama found at: {default_path}")
            return True

    elif system in ["Darwin", "Linux"]:
        result = subprocess.run(["which", "ollama"], capture_output=True)
        if result.returncode == 0:
            print_success("Ollama is installed")
            return True

    print_error("Ollama is not installed")
    return False

async def get_ollama_models():
    """Get list of downloaded Ollama models"""
    print_info("Checking downloaded models...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        data = response.json()

        if data.get("models"):
            print_success(f"Found {len(data['models'])} model(s):")
            for model in data["models"]:
                print(f"  - {model.get('name', 'unknown')}")
            return data["models"]
        else:
            print_warning("No models downloaded yet")
            return []
    except Exception as e:
        print_error(f"Could not check models: {e}")
        return []

async def pull_mistral_model():
    """Download Mistral model"""
    print_info("Starting Mistral model download (4GB)...")
    print_warning("This may take 5-15 minutes depending on your internet speed")

    try:
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": "mistral"},
            stream=True,
            timeout=300
        )

        if response.status_code == 200:
            print_success("Model download initiated!")
            print_info("Progress:")

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "status" in data:
                            status = data["status"]
                            if "downloading" in status.lower():
                                if "completed" in data and "total" in data:
                                    pct = (data["completed"] / data["total"]) * 100
                                    print(f"  {status}: {pct:.1f}%", end='\r')
                            else:
                                print(f"  {status}")
                    except json.JSONDecodeError:
                        pass

            print_success("Model download complete!")
            return True
        else:
            print_error(f"Download failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Could not download model: {e}")
        return False

async def test_chatbot_integration():
    """Test chatbot integration"""
    print_header("Testing Chatbot Integration")

    print_info("Testing chatbot service...")
    try:
        from app.chatbot import get_ollama_chat
        ollama = get_ollama_chat()

        if ollama.available:
            print_success("Chatbot service is functional!")
            return True
        else:
            print_warning("Chatbot service detected Ollama is offline")
            return False
    except ImportError as e:
        print_error(f"Could not import chatbot service: {e}")
        return False
    except Exception as e:
        print_error(f"Chatbot test failed: {e}")
        return False

async def verify_backend_endpoints():
    """Verify backend endpoints are registered"""
    print_info("Checking backend endpoints...")

    endpoints = [
        "/api/chatbot/chatbot/status",
        "/api/chatbot/chatbot/help",
    ]

    for endpoint in endpoints:
        try:
            # Note: These require authentication, so 401 is OK
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=2)
            if response.status_code in [200, 401]:
                print_success(f"Endpoint exists: {endpoint}")
            else:
                print_warning(f"Endpoint returned {response.status_code}: {endpoint}")
        except requests.exceptions.ConnectionError:
            print_error("Backend is not running on port 8000")
            return False
        except Exception as e:
            print_warning(f"Could not check {endpoint}: {e}")

    return True

async def main():
    """Main setup and verification"""
    print_header("T10 AIRPS - Ollama Integration Setup")

    print(f"{Colors.BOLD}System Status Check{Colors.END}\n")

    # Step 1: Check if Ollama is installed
    is_installed = await check_ollama_installed()

    if not is_installed:
        print_error("Ollama is not installed!")
        print_info("Download from: https://ollama.ai")
        print_info("Or run: SETUP_OLLAMA.bat (Windows)")
        return False

    # Step 2: Check if Ollama is running
    time.sleep(1)
    is_running = await check_ollama_running()

    if not is_running:
        print_warning("Ollama is not running!")
        print_info("Start Ollama with: ollama serve")
        return False

    # Step 3: Check models
    time.sleep(1)
    models = await get_ollama_models()

    has_mistral = any(m.get("name", "").startswith("mistral") for m in models)

    if not has_mistral:
        print_warning("Mistral model not found")
        response = input(f"\n{Colors.CYAN}Download Mistral model now? (y/n): {Colors.END}")

        if response.lower() == 'y':
            success = await pull_mistral_model()
            if not success:
                print_error("Model download failed")
                return False
        else:
            print_warning("Skipping model download. Run: ollama pull mistral")

    # Step 4: Test chatbot integration
    time.sleep(1)
    chatbot_ok = await test_chatbot_integration()

    # Step 5: Verify backend
    time.sleep(1)
    backend_ok = await verify_backend_endpoints()

    # Summary
    print_header("Setup Summary")

    status_items = [
        ("Ollama Installed", is_installed),
        ("Ollama Running", is_running),
        ("Mistral Model", has_mistral),
        ("Chatbot Service", chatbot_ok),
        ("Backend Endpoints", backend_ok),
    ]

    all_ok = all(status for _, status in status_items)

    for name, status in status_items:
        if status:
            print_success(f"{name}")
        else:
            print_error(f"{name}")

    print()

    if all_ok:
        print_success("All systems ready!")
        print_info("You can now start the full T10 AIRPS system:")
        print()
        print(f"{Colors.CYAN}Terminal 1: ollama serve{Colors.END}")
        print(f"{Colors.CYAN}Terminal 2: cd backend && python -m uvicorn main:app --port 8000{Colors.END}")
        print(f"{Colors.CYAN}Terminal 3: cd frontend && npm run dev{Colors.END}")
        print()
        print(f"{Colors.CYAN}Then open: http://localhost:5173{Colors.END}")
        return True
    else:
        print_error("Some components are not ready")
        print_info("Fix issues above and try again")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Fatal error: {e}{Colors.END}")
        sys.exit(1)
