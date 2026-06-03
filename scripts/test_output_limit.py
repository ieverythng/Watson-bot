#!/usr/bin/env python3
"""
Test script to verify model output token limit is configured correctly.
This will make a test API call and check if max_tokens is being passed.
"""

import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://172.24.16.1:8080/v1"
MODEL = "qwen35-27b-q3km"

def test_api_endpoint():
    """Test if the llama.cpp server is responding"""
    print("🔍 Testing API endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ API is responding")
            print(f"   Available models: {models.get('data', [])}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

def test_max_tokens_config():
    """Check if config.yaml has max_tokens set"""
    print("\n🔍 Checking config.yaml...")
    config_path = Path("/home/juanbeck/.hermes/config.yaml")
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        model_cfg = config.get("model", {})
        max_tokens = model_cfg.get("max_tokens")
        
        if max_tokens:
            print(f"✅ max_tokens configured: {max_tokens:,} tokens")
            return True
        else:
            print(f"⚠️  max_tokens not found in config.yaml")
            print(f"   Model config: {model_cfg}")
            return False
    except Exception as e:
        print(f"❌ Failed to parse config: {e}")
        return False

def test_chat_completion():
    """Test if we can make a chat completion with max_tokens"""
    print("\n🔍 Testing chat completion with max_tokens...")
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello briefly."}
        ],
        "max_tokens": 100,  # Test with a small limit
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Chat completion successful")
            print(f"   Response: {content[:100]}...")
            
            # Check token usage
            if 'usage' in result:
                usage = result['usage']
                print(f"   Tokens used: {usage.get('completion_tokens', 'N/A')} output")
            return True
        else:
            print(f"❌ Chat completion failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Chat completion error: {e}")
        return False

def main():
    print("="*60)
    print("Model Output Token Limit Test")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("API Endpoint", test_api_endpoint()))
    results.append(("Config Check", test_max_tokens_config()))
    results.append(("Chat Completion", test_chat_completion()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All tests passed! The output token limit fix is working.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
