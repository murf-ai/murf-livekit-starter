#!/bin/bash

# Start all services in background
if command -v livekit-server >/dev/null 2>&1; then
  livekit-server --dev &
elif [ -f "./livekit-server" ]; then
  ./livekit-server --dev &
else
  echo "Warning: livekit-server not found. Skipping local LiveKit startup and using your configured LIVEKIT_URL instead."
fi

# The agent starts the metrics/dashboard HTTP server itself on port 8082.
# Starting metrics.py separately races for the same port.
(cd backend && uv run python src/agent.py dev) &
(cd frontend && pnpm dev) &

# Wait for all background jobs
wait
