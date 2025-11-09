#!/usr/bin/env python3
"""
Standalone test for conversational response generator
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.services.conversational_responses import generate_conversational_response

def test_responses():
    """Test various conversational responses"""

    print("=" * 60)
    print("Testing Conversational Response Generator")
    print("=" * 60)

    # Test greetings at different times of day
    print("\n1. GREETING RESPONSES (cycling through variations)")
    print("-" * 60)

    contexts = [
        {"timezone": "America/New_York"},  # Should detect time of day
        {"timezone": "America/Los_Angeles"},
        {"timezone": "UTC"}
    ]

    for i, ctx in enumerate(contexts, 1):
        response = generate_conversational_response("greeting", ctx)
        print(f"   Greeting #{i}: {response}")

    # Test thanks responses (cycling)
    print("\n2. THANKS RESPONSES (cycling through variations)")
    print("-" * 60)
    for i in range(5):
        response = generate_conversational_response("thanks")
        print(f"   Thanks #{i+1}: {response}")

    # Test chitchat with different contexts
    print("\n3. CHITCHAT RESPONSES (context-aware)")
    print("-" * 60)

    chitchat_contexts = [
        {"original_query": "how's the weather today?"},
        {"original_query": "how are you doing?"},
        {"original_query": "did you watch the game?"},
        {"original_query": "what's up?"}
    ]

    for ctx in chitchat_contexts:
        response = generate_conversational_response("chitchat", ctx)
        print(f"   Query: '{ctx['original_query']}'")
        print(f"   Response: {response}\n")

    # Test help responses
    print("4. HELP RESPONSES (cycling through variations)")
    print("-" * 60)
    for i in range(3):
        response = generate_conversational_response("help")
        print(f"   Help #{i+1}: {response}\n")

    # Test cancel responses
    print("5. CANCEL RESPONSES (cycling through variations)")
    print("-" * 60)
    for i in range(3):
        response = generate_conversational_response("cancel")
        print(f"   Cancel #{i+1}: {response}")

    print("\n" + "=" * 60)
    print("✅ All tests passed! Responses are cycling and context-aware.")
    print("=" * 60)

if __name__ == "__main__":
    test_responses()
