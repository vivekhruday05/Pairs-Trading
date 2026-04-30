#!/bin/bash

# Pairs Trading Terminal - Stop Script
# Kills both backend and frontend servers

pkill -f "python.*main.py"
pkill -f "npm run dev"
pkill -f "vite"

echo "Stopped Pairs Trading Terminal services"
