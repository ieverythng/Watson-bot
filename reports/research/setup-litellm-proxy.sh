#!/bin/bash
# LiteLLM Proxy Setup Script for Windows PC (via WSL or PowerShell)
# This sets up the LiteLLM proxy that sits between clients and llama.cpp

set -e

echo "=== LiteLLM Proxy Setup ==="

# Install LiteLLM with proxy dependencies
pip install 'litellm[proxy]'

# Create config directory
mkdir -p ~/.litellm

# Copy config file (adjust path as needed)
cp /path/to/litellm-config.yaml ~/.litellm/config.yaml

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the proxy, run:"
echo "  OPENAI_API_KEY=placeholder litellm --config ~/.litellm/config.yaml --port 4000"
echo ""
echo "Or to bind to ZeroTier interface specifically:"
echo "  OPENAI_API_KEY=placeholder litellm --config ~/.litellm/config.yaml --port 4000 --host 0.0.0.0"
echo ""
echo "Then configure your clients to point to: http://<YOUR_WINDOWS_IP>:4000/v1"
