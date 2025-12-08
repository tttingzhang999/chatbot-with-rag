#!/bin/bash
# 啟動本地 Vite 前端開發服務器
# For local development only

set -e

# Change to frontend directory
cd "$(dirname "$0")/../../apps/frontend" || exit

echo "=========================================="
echo "Starting Vite Frontend (Local Development)"
echo "=========================================="
echo "Frontend: http://localhost:5173"
echo "Network: Exposed to LAN (check output below for network IP)"
echo "Mode: Hot Module Replacement (HMR) enabled"
echo "=========================================="
echo ""

# Start Vite dev server
npm run dev
