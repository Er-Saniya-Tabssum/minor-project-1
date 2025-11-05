#!/usr/bin/env python3
import requests
import json
import time

def test_api():
    """Test if the API is working"""
    base_url = "http://localhost:5001"
    
    print("🔍 Testing API Connection...")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"Health Check: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API is working!")
            print(f"   Status: {data.get('status')}")
            print(f"   Pipeline Loaded: {data.get('pipeline_loaded')}")
            print(f"   Service: {data.get('service')}")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Cannot connect to the API")
        print("   Make sure the server is running on port 5001")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("-" * 50)

if __name__ == "__main__":
    test_api()