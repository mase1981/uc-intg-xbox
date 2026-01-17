"""
Test script to verify the OAuth callback server functionality.
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uc_intg_xbox.oauth_server import OAuthCallbackServer

async def test_server():
    print("Testing OAuth callback server...")
    print()

    server = OAuthCallbackServer(port=8080)

    try:
        # Start the server
        print("Starting server on http://localhost:8080")
        await server.start()
        print("Server started successfully!")
        print()
        print("Server is now listening for OAuth callbacks at:")
        print("  http://localhost:8080/callback")
        print()
        print("You can test it by visiting:")
        print("  http://localhost:8080/callback?code=test_auth_code_12345")
        print()
        print("Or visit the root page:")
        print("  http://localhost:8080/")
        print()
        print("Waiting for callback (30 second timeout)...")
        print()

        # Wait for callback with 30 second timeout for testing
        code = await server.wait_for_code(timeout=30)

        if code:
            print(f"SUCCESS! Received authorization code: {code}")
        else:
            print("TIMEOUT: No authorization code received within 30 seconds")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print()
        print("Stopping server...")
        await server.stop()
        print("Server stopped.")

if __name__ == "__main__":
    asyncio.run(test_server())
