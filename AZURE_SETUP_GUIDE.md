# Azure App Registration Setup Guide

Due to changes in Microsoft's OAuth redirect handling, the Xbox integration now requires users to create their own Azure App Registration. This guide will walk you through the process step-by-step.

## Why is this needed?

Microsoft deprecated the OAuth redirect URI that the python-xbox library was using, making it impossible to authenticate with the existing setup. By creating your own Azure App Registration, you get full control over the authentication flow and ensure it continues to work.

## Prerequisites

- A Microsoft account (the same one you use for Xbox Live)
- Access to the Azure Portal (free account is sufficient)

## Step-by-Step Instructions

### 1. Create a Microsoft Azure Account

1. Go to https://portal.azure.com
2. Sign in with your Microsoft account
3. If prompted, complete the Azure sign-up process (the free tier is sufficient - no credit card required for this feature)

### 2. Register a New Application

1. In the Azure Portal, search for **"Microsoft Entra ID"** (formerly Azure Active Directory) in the search bar
2. Click on **"App registrations"** in the left sidebar
3. Click **"+ New registration"** at the top
4. Fill in the registration form:
   - **Name**: `Unfolded Circle Xbox Integration` (or any name you prefer)
   - **Supported account types**: Select **"Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)"**
   - **Redirect URI**:
     - From the dropdown, select **"Public client/native (mobile & desktop)"**
     - Enter: `http://localhost`
5. Click **"Register"**

### 3. Copy Your Application (Client) ID

After registration, you'll be on your app's overview page:

1. Find the **"Application (client) ID"** field
2. Click the copy icon next to it to copy the ID (it looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
3. **Save this ID** - you'll need it during the integration setup

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

### 5. Verify Redirect URI (Optional)

1. In the left sidebar, click **"Authentication"**
2. Under **"Platform configurations"**, you should see **"Mobile and desktop applications"**
3. Verify that `http://localhost` is listed as a redirect URI
4. If you want to add additional redirect URIs for testing, you can add:
   - `http://localhost:36677`
   - `http://localhost:36677/auth`

## Using Your Credentials

When setting up the Xbox integration in your Unfolded Circle Remote:

1. Enter your **Application (client) ID** in the **"Azure App Client ID"** field
2. Enter your **Client Secret Value** in the **"Azure App Client Secret"** field
3. Enter your Xbox Live Device ID as usual
4. Follow the OAuth authentication flow to complete setup

## Security Notes

- Your Client ID and Secret are used only by your integration to authenticate with Xbox Live
- These credentials are stored locally on your Unfolded Circle Remote
- You can regenerate the Client Secret at any time in the Azure Portal if needed
- The free Azure tier is sufficient - there are no costs for this feature

## Troubleshooting

### "The provided value for 'redirect_uri' is not valid"
- Make sure you selected **"Public client/native (mobile & desktop)"** as the redirect URI type
- Verify the redirect URI is exactly: `http://localhost` (no trailing slash)

### "Supported account types" error during authentication
- Ensure you selected the option that includes **"personal Microsoft accounts (e.g. Skype, Xbox)"**
- You may need to delete and recreate the app registration with the correct account type

### Cannot find Client Secret Value
- The secret value is only shown once when created
- If you missed copying it, delete the old secret and create a new one

## Need Help?

If you encounter issues, please open an issue on the GitHub repository with:
- Screenshots of your Azure App registration settings (hide your Client ID and Secret)
- The error message you're receiving
- Steps you've already tried

---

**Note**: This setup only needs to be done once. Your credentials will be saved and reused for token refreshes.
