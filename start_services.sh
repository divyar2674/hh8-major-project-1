#!/bin/bash
# T10 AIRPS - Complete Startup Script for Linux/Mac

echo "=========================================="
echo "T10 AI Incident Response System"
echo "Starting All Services..."
echo "=========================================="

# Check if running on Windows
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "Detected Windows environment"
    echo "Please use: start_services.bat"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

echo ""
echo "1. Installing backend dependencies..."
cd "$SCRIPT_DIR/major_project/backend"
pip install -q -r requirements.txt

echo "2. Installing frontend dependencies..."
cd "$SCRIPT_DIR/major_project/frontend"
npm install > /dev/null 2>&1

echo ""
echo "3. Starting Backend Server (port 8000)..."
cd "$SCRIPT_DIR/major_project/backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo "   Backend started with PID: $BACKEND_PID"

echo ""
echo "4. Waiting for backend to initialize..."
sleep 3

echo ""
echo "5. Starting Frontend Server (port 5173)..."
cd "$SCRIPT_DIR/major_project/frontend"
npm run dev > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "   Frontend started with PID: $FRONTEND_PID"

echo ""
echo "=========================================="
echo "T10 System Started Successfully!"
echo "=========================================="
echo ""
echo "Access Points:"
echo "  Web UI:        http://localhost:5173"
echo "  API:           http://localhost:8000"
echo "  API Docs:      http://localhost:8000/api/docs"
echo "  Health Check:  http://localhost:8000/api/health"
echo ""
echo "Default Credentials:"
echo "  Username: admin"
echo "  Password: Admin@1234"
echo ""
echo "Logs:"
echo "  Backend:  $SCRIPT_DIR/logs/backend.log"
echo "  Frontend: $SCRIPT_DIR/logs/frontend.log"
echo ""
echo "To stop services, run: stop_services.sh"
echo ""

# Save PIDs for later stopping
echo "$BACKEND_PID" > "$SCRIPT_DIR/logs/backend.pid"
echo "$FRONTEND_PID" > "$SCRIPT_DIR/logs/frontend.pid"

echo "System is running. Press Ctrl+C to stop."
wait
