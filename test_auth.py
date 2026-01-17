"""
Test script to verify Azure App credentials work with Xbox Live authentication.
"""
import asyncio
import httpx
import ssl
import certifi
from pythonxbox.authentication.manager import AuthenticationManager

# Replace these with your actual values from Azure App Registration
CLIENT_ID = "YOUR_CLIENT_ID_HERE"
CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"
REDIRECT_URI = "http://localhost:8765/callback"

async def test_auth():
    print("Testing Azure App credentials...")
    print(f"CLIENT_ID: {CLIENT_ID}")
    print(f"REDIRECT_URI: {REDIRECT_URI}")
    print()

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    session = httpx.AsyncClient(verify=ssl_context)

    try:
        auth_mgr = AuthenticationManager(
            session, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
        )

        # Generate auth URL
        auth_url = auth_mgr.generate_authorization_url()
        print("SUCCESS: Successfully generated authorization URL:")
        print(auth_url)
        print()
        print("Instructions:")
        print("1. Copy the URL above and paste it into your browser")
        print("2. Sign in with your Microsoft account")
        print("3. Copy the authorization code from the callback page")
        print("4. Paste it below")
        print()

        auth_code = input("Enter authorization code: ").strip()

        print()
        print(f"Attempting to exchange code (length: {len(auth_code)})...")

        try:
            await auth_mgr.request_tokens(auth_code)
            print("SUCCESS! Tokens received successfully!")
            print("Your Azure App credentials are working correctly.")
        except httpx.HTTPStatusError as e:
            print(f"FAILED: HTTP {e.response.status_code}")
            print(f"Response: {e.response.text}")
            print()
            print("This usually means:")
            if e.response.status_code == 400:
                print("  - The authorization code has expired (codes expire quickly)")
                print("  - The CLIENT_SECRET is incorrect")
                print("  - The redirect URI doesn't match Azure configuration")
                print("  - The authorization code was used with a different CLIENT_ID")
            elif e.response.status_code == 401:
                print("  - The CLIENT_SECRET is incorrect")
        except Exception as e:
            print(f"ERROR: {e}")

    finally:
        await session.aclose()

if __name__ == "__main__":
    asyncio.run(test_auth())
