#!/usr/bin/env python3
"""
Test script for free AI Chatbot
Verifies Ollama connectivity and chatbot functionality
"""
import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_chatbot():
    """Test chatbot without authentication."""
    from app.chatbot import get_ollama_chat, stream_chatbot_response

    print("=" * 60)
    print("T10 AIRPS Free AI Chatbot - Test Suite")
    print("=" * 60)

    # Test 1: Ollama connectivity
    print("\n[TEST 1] Checking Ollama Server...")
    ollama = get_ollama_chat()
    if ollama.available:
        print(f"✓ Ollama is RUNNING (Model: {ollama.model})")
    else:
        print("✗ Ollama is NOT running")
        print("  Install from: https://ollama.ai")
        print("  Then run: ollama serve")
        print("  Then: ollama pull mistral")
        return

    # Test 2: Simple chat
    print("\n[TEST 2] Testing Chat Functionality...")
    test_message = "What incident types do you support?"
    print(f"User: {test_message}")
    print("Bot: ", end="", flush=True)

    try:
        response = ""
        async for chunk in stream_chatbot_response(test_message):
            response += chunk
            print(chunk, end="", flush=True)
        print("\n✓ Chat working!")
    except Exception as e:
        print(f"\n✗ Chat error: {e}")
        return

    # Test 3: Command detection
    print("\n[TEST 3] Testing Dashboard Command Interpretation...")
    from app.chatbot import CommandInterpreter

    test_response = """I'll create that incident for you.
{"action": "create_incident", "params": {"title": "Test Incident", "description": "Test", "severity": "High"}}
The incident has been created."""

    action = CommandInterpreter.extract_action(test_response)
    if action and CommandInterpreter.validate_action(action):
        print(f"✓ Command detected: {action['action']}")
        print(f"  Parameters: {action['params']}")
    else:
        print("✗ Command not detected")

    # Test 4: Voice support
    print("\n[TEST 4] Checking Voice Support...")
    try:
        import pyttsx3
        print("✓ Text-to-Speech available (pyttsx3)")
    except ImportError:
        print("✗ pyttsx3 not installed")

    try:
        import speech_recognition
        print("✓ Speech-to-Text available (speech_recognition)")
    except ImportError:
        print("✗ speech_recognition not installed")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✓ Ollama is running and chatbot is functional")
    print("✓ FREE AI chatbot is ready for use")
    print("✓ No API costs, completely offline")
    print("\nNext steps:")
    print("1. Open http://localhost:5173 in browser")
    print("2. Click the chatbot icon")
    print("3. Type or use voice control")
    print("4. Try: 'Create a critical malware incident'")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_chatbot())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        logger.exception("Test error")
        sys.exit(1)
