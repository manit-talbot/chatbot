#!/usr/bin/env python3
"""
Test client for the Chatbot API
Demonstrates how to use the REST endpoints
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:8000"

def test_chat_endpoint():
    """Test the /chat endpoint"""
    print("=== Testing Chat Endpoint ===")
    
    # Test 1: New conversation
    print("\n1. Starting new conversation...")
    response = requests.post(f"{API_BASE_URL}/chat", json={
        "message": "What is the purpose of this knowledge base?"
    })
    
    if response.status_code == 200:
        data = response.json()
        session_id = data["session_id"]
        print(f"✅ New session created: {session_id}")
        print(f"Response: {data['response'][:100]}...")
        print(f"Agents used: {data['agents_used']}")
        
        # Test 2: Continue conversation
        print("\n2. Continuing conversation...")
        response2 = requests.post(f"{API_BASE_URL}/chat", json={
            "message": "Can you tell me more about the database tables?",
            "session_id": session_id
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"✅ Continued session: {data2['session_id']}")
            print(f"Response: {data2['response'][:100]}...")
            print(f"Agents used: {data2['agents_used']}")
            
            return session_id
        else:
            print(f"❌ Error continuing conversation: {response2.status_code}")
            print(response2.text)
    else:
        print(f"❌ Error creating conversation: {response.status_code}")
        print(response.text)
    
    return None

def test_history_endpoint(session_id):
    """Test the /chathistory endpoint"""
    if not session_id:
        print("No session ID available for history test")
        return
    
    print(f"\n=== Testing Chat History Endpoint ===")
    print(f"Retrieving history for session: {session_id}")
    
    response = requests.get(f"{API_BASE_URL}/chathistory/{session_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {data['total_count']} conversations")
        
        for i, conv in enumerate(data['conversations'], 1):
            print(f"\nConversation {i}:")
            print(f"  User: {conv['user']}")
            print(f"  AI: {conv['ai'][:100]}...")
            print(f"  Time: {conv['timestamp']}")
    else:
        print(f"❌ Error retrieving history: {response.status_code}")
        print(response.text)

def test_health_endpoint():
    """Test the /health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    
    response = requests.get(f"{API_BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed: {data['status']}")
        print(f"Knowledge Base Agent: {data['knowledge_base_agent']}")
        print(f"SQL Agent: {data['sql_agent']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        print(response.text)

def test_root_endpoint():
    """Test the root endpoint"""
    print("\n=== Testing Root Endpoint ===")
    
    response = requests.get(f"{API_BASE_URL}/")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Root endpoint working")
        print(f"Message: {data['message']}")
        print(f"Version: {data['version']}")
        print("Available endpoints:")
        for endpoint, description in data['endpoints'].items():
            print(f"  - {endpoint}: {description}")
    else:
        print(f"❌ Root endpoint failed: {response.status_code}")

def main():
    """Run all tests"""
    print("🚀 Starting Chatbot API Tests")
    print(f"API Base URL: {API_BASE_URL}")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    try:
        # Test health first
        test_health_endpoint()
        
        # Test root endpoint
        test_root_endpoint()
        
        # Test chat functionality
        session_id = test_chat_endpoint()
        
        # Test history functionality
        test_history_endpoint(session_id)
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("Make sure the server is running: python chatbot_api.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
