# Azure App Registration Setup Guide (Updated for v4.1.6+)

Due to changes in Microsoft's OAuth redirect handling, the Xbox integration now requires users to create their own Azure App Registration. This guide provides TWO methods - choose the one that works for you.

## Why is this needed?

Microsoft deprecated the OAuth redirect URI that the python-xbox library was using, making it impossible to authenticate with the existing setup. By creating your own Azure App Registration, you get full control over the authentication flow.

## Prerequisites

- A Microsoft account (the same one you use for Xbox Live)
- Access to the Azure Portal (free account is sufficient)

---

# Method 1: Mobile/Desktop App (RECOMMENDED - No Secret Required)

This method is simpler and works for most users. It doesn't require managing a client secret.

## Step-by-Step Instructions

### 1. Create a Microsoft Azure Account

1. Go to https://portal.azure.com
2. Sign in with your Microsoft account
3. If prompted, complete the Azure sign-up process (the free tier is sufficient - no credit card required)

### 2. Register a New Application

1. In the Azure Portal, search for **"Microsoft Entra ID"** (formerly Azure Active Directory)
2. Click on **"App registrations"** in the left sidebar
3. Click **"+ New registration"** at the top
4. Fill in the registration form:
   - **Name**: `Unfolded Circle Xbox Integration` (or any name you prefer)
   - **Supported account types**: Select **"Personal Microsoft accounts only"**
   - **Redirect URI**: Leave blank for now (we'll add it in the next step)
5. Click **"Register"**

### 3. Copy Your Application (client) ID

After registration, you'll be on your app's overview page:

1. Find the **"Application (client) ID"** field
2. Click the copy icon next to it (it looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
3. **Save this ID** - you'll need it during integration setup

### 4. Configure Mobile/Desktop Platform

1. In the left sidebar, click **"Authentication"**
2. Under **Platform configurations**, click **"+ Add a platform"**
3. Select **"Mobile and desktop applications"**
4. In the "Custom redirect URIs" section, enter: `http://localhost:8765/callback`
5. Click **"Configure"**
6. Back on the Authentication page, scroll down to **Advanced settings**
7. Verify **"Allow public client flows"** is set to **YES**
8. Click **"Save"** at the top

### 5. Use in Integration Setup

When setting up the Xbox integration in your Unfolded Circle Remote:

1. Enter your **Application (client) ID** in the **"Azure App Client ID"** field
2. **Leave the "Azure App Client Secret" field EMPTY** (just press space and delete, or enter a single space)
3. Enter the number of consoles and continue
4. Enter your Xbox Live Device ID(s)
5. Click the provided authorization URL to authenticate with Microsoft
6. Complete the setup

---

# Method 2: Web App with Client Secret (ALTERNATIVE)

Use this method only if Method 1 doesn't work, or if you specifically need a confidential client setup.

## Step-by-Step Instructions

### 1-2. Create Azure Account and Register Application

Follow steps 1-2 from Method 1 above, but in step 4:
   - **Supported account types**: Select **"Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)"**

### 3. Copy Your Application (client) ID

Same as Method 1, step 3

### 4. Create a Client Secret

1. In the left sidebar, click **"Certificates & secrets"**
2. Click on the **"Client secrets"** tab
3. Click **"+ New client secret"**
4. Fill in:
   - **Description**: `Xbox Integration Secret` (or any name you prefer)
   - **Expires**: Choose **"24 months"** (or your preference)
5. Click **"Add"**
6. **IMPORTANT**: Immediately copy the **"Value"** (the long string, not the Secret ID)
7. **Save this secret value** - you cannot view it again after leaving this page

### 5. Configure Web Platform

1. In the left sidebar, click **"Authentication"**
2. Under **Platform configurations**, click **"+ Add a platform"**
3. Select **"Web"**
4. Enter redirect URI: `http://localhost:8765/callback`
5. Click **"Configure"**
6. Back on the Authentication page, scroll down to **Advanced settings**
7. Verify **"Allow public client flows"** is set to **NO**
8. Click **"Save"** at the top

### 6. Use in Integration Setup

When setting up the Xbox integration:

1. Enter your **Application (client) ID** in the **"Azure App Client ID"** field
2. Enter your **Client Secret VALUE** in the **"Azure App Client Secret"** field
3. Continue with setup as normal

---

## Troubleshooting

### "unauthorized_client" error before seeing login page

**Most Common Cause**: You're using Method 2 (Web app) but the secret isn't properly configured.

**Solutions**:
1. **Switch to Method 1** (Mobile/Desktop app) - This is the recommended approach for Xbox Live
2. If staying with Method 2:
   - Verify the secret hasn't expired in Azure Portal
   - Delete and recreate the client secret
   - Make sure you copied the VALUE, not the Secret ID

### "The provided value for 'redirect_uri' is not valid"

- Make sure the redirect URI is EXACTLY: `http://localhost:8765/callback`
- It must be `http://` (not `https://`)
- No trailing slash
- Check for typos

### Which method should I use?

**Use Method 1 (Mobile/Desktop)** if:
- You want the simpler setup
- You don't want to manage a client secret
- You're authenticating from localhost
- You're having issues with Method 2

**Use Method 2 (Web with Secret)** if:
- Method 1 doesn't work for your setup
- You specifically need a confidential client
- You're building a server-side integration (advanced)

### Integration doesn't accept empty client secret

If the integration requires a value in the client secret field:
- Try entering a single space character
- Or enter any random text - it will be ignored by Microsoft for Mobile/Desktop apps

### Can I switch between methods?

Yes! You can switch between methods by updating your Azure App Registration:
- Remove the old platform configuration in Authentication page
- Add the new platform type
- Update your integration setup with new credentials (or blank secret for Method 1)

## Security Notes

- Your Client ID is used to identify your app to Microsoft
- For Method 1: No secret is needed, making it simpler and more secure for client-side apps
- For Method 2: The secret is stored locally on your Unfolded Circle Remote
- You can regenerate secrets at any time in Azure Portal
- The free Azure tier is sufficient - there are no costs

## Need Help?

If you encounter issues, please open an issue on the GitHub repository with:
- Which method you're using
- Screenshots of your Azure App registration settings (hide your Client ID and any secrets)
- The error message you're receiving
- Steps you've already tried

---

**Technical Note**: Xbox Live OAuth works with both confidential (Web) and public (Mobile/Desktop) client types. The Mobile/Desktop approach is recommended because it doesn't require managing a client secret, reducing complexity and potential configuration issues.

**Sources:**
- [Sign in to Xbox Live with OAuth2 - GitHub Gist](https://gist.github.com/tuxuser/8b7cc153cdecd0a9c3f2694850fa90bd)
- [OAuth 2.0 for Microsoft Accounts (installed applications)](https://afterlogic.com/mailbee-net/docs/OAuth2MicrosoftRegularAccountsInstalledApps.html)
- [OAuth login in desktop apps | Damir's Corner](https://www.damirscorner.com/blog/posts/20231229-OAuthLoginInDesktopApps.html)
