"""
Simple script to test the API endpoints.
"""

import requests

API_BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_login():
    """Test login endpoint."""
    print("Testing login...")
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": "test_user"},
        timeout=5,
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data}")
    print()
    return data.get("user_id")


def test_send_message(user_id: str):
    """Test sending a message."""
    print("Testing send message...")
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json={"message": "Hello, HR Chatbot!"},
        headers={"X-User-Id": user_id},
        timeout=5,
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data}")
    print()
    return data.get("conversation_id")


def test_get_conversations(user_id: str):
    """Test getting conversation list."""
    print("Testing get conversations...")
    response = requests.get(
        f"{API_BASE_URL}/chat/conversations",
        headers={"X-User-Id": user_id},
        timeout=5,
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_get_conversation_history(user_id: str, conversation_id: str):
    """Test getting conversation history."""
    print("Testing get conversation history...")
    response = requests.get(
        f"{API_BASE_URL}/chat/conversations/{conversation_id}",
        headers={"X-User-Id": user_id},
        timeout=5,
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("HR Chatbot API Tests")
    print("=" * 60)
    print()

    try:
        # Test health check
        test_health_check()

        # Test login
        user_id = test_login()
        if not user_id:
            print("Login failed, stopping tests")
            return

        # Test sending message
        conversation_id = test_send_message(user_id)
        if not conversation_id:
            print("Send message failed")
            return

        # Test getting conversations
        test_get_conversations(user_id)

        # Test getting conversation history
        test_get_conversation_history(user_id, conversation_id)

        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure backend is running on port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
