#!/bin/bash

# Pairs Trading Terminal - Startup Script
# Starts both backend and frontend servers

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║   Pairs Trading Terminal - Starting...                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}[1/2]${NC} Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Error: Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Error: Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

echo ""
echo -e "${BLUE}[2/2]${NC} Starting services..."
echo ""

# Start backend
echo -e "${YELLOW}Starting Backend (Port 8000)...${NC}"
cd "$SCRIPT_DIR/backend"

# Check if requirements are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -r requirements.txt
fi

# Start backend in background
python3 main.py &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo ""

# Give backend time to start
sleep 3

# Start frontend
echo -e "${YELLOW}Starting Frontend (Port 3000)...${NC}"
cd "$SCRIPT_DIR/frontend"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend in background
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo ""

echo "╔════════════════════════════════════════════════════════╗"
echo "║   Pairs Trading Terminal is Running!                  ║"
echo "╠════════════════════════════════════════════════════════╣"
echo "║                                                        ║"
echo -e "║   ${GREEN}Frontend: http://localhost:3000${NC}                    ║"
echo -e "║   ${GREEN}Backend:  http://localhost:8000${NC}                    ║"
echo "║                                                        ║"
echo "║   Logs:                                                ║"
echo "║   - Backend output above                               ║"
echo "║   - Frontend output in separate terminal               ║"
echo "║                                                        ║"
echo "║   To stop: Press Ctrl+C or run stop_terminal.sh       ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
