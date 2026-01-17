# Testing v3.1.0 - OAuth OOB Flow

## Build Status: ✅ COMPLETE

**Version:** v3.1.0
**Release:** https://github.com/mase1981/uc-intg-xbox/releases/tag/v3.1.0
**Artifact:** `uc-intg-xbox-3.1.0-aarch64.tar.gz`
**Docker Image:** `ghcr.io/mase1981/uc-intg-xbox:v3.1.0`

---

## What Changed

This version implements **OAuth Out-of-Band (OOB) Flow** to solve the Microsoft redirect URI behavior change.

### Key Changes
- ✅ Uses `urn:ietf:wg:oauth:2.0:oob` redirect URI
- ✅ Microsoft displays authorization code directly
- ✅ No external servers or infrastructure needed
- ✅ Zero cost, 100% open-source solution
- ✅ Simple copy/paste authentication

### Files Modified
- `uc_intg_xbox/auth.py` - Switched to OOB redirect URI
- `uc_intg_xbox/setup.py` - Updated user instructions
- `driver.json` - Version bump to 3.1.0

---

## Installation for Testing

### Option 1: Install from Release Artifact

1. Download the artifact:
   ```bash
   wget https://github.com/mase1981/uc-intg-xbox/releases/download/v3.1.0/uc-intg-xbox-3.1.0-aarch64.tar.gz
   ```

2. Extract on your Remote:
   ```bash
   tar -xzf uc-intg-xbox-3.1.0-aarch64.tar.gz
   ```

3. Install according to Unfolded Circle integration docs

### Option 2: Use Docker Image

```bash
docker pull ghcr.io/mase1981/uc-intg-xbox:v3.1.0
```

### Option 3: Install via Remote UI

1. Go to Settings → Integrations
2. Add Integration → Custom Driver
3. Enter URL: `https://github.com/mase1981/uc-intg-xbox/releases/download/v3.1.0/uc-intg-xbox-3.1.0-aarch64.tar.gz`

---

## Testing Steps

### Test 1: New Setup (Critical Test)

This tests the new OAuth OOB flow for the first time.

1. **Remove existing Xbox integration** (if any)
   - Go to Settings → Integrations → Xbox
   - Click "Remove"

2. **Start fresh setup**
   - Go to Settings → Integrations
   - Click "Add Integration"
   - Select "Xbox Integration"

3. **Enter Xbox Live Device ID**
   - Enter your console's Live ID
   - Click "Next"

4. **Authenticate with new OOB flow** ⭐ THIS IS THE KEY TEST
   - You should see:
     - "Step 1: Authenticate" instructions
     - Authorization URL (clickable link)
     - "Step 2: Paste Authorization Code" field
     - Help text

5. **Click the authorization URL**
   - Opens Microsoft login page
   - Sign in with your Microsoft account

6. **Check what Microsoft displays** ⭐ CRITICAL
   - **Expected:** Microsoft shows a page with your authorization code
   - **Code format:** String like `M.R3_BAY.abc123def456...`
   - **Page message:** Something like "Your code:" or "Copy this code"

7. **Copy the code**
   - Select and copy the entire code

8. **Paste into Remote**
   - Go back to Remote setup page
   - Paste code into "Step 2" field
   - Click "Continue" or "Next"

9. **Verify setup completes**
   - ✅ Should show "Setup Complete" or similar
   - ✅ Xbox integration should appear in integrations list
   - ✅ Should be able to control Xbox

### Test 2: Reconfiguration

Tests if existing users can reconfigure with the new flow.

1. Go to Settings → Integrations → Xbox
2. Click "Configure" or "Reconfigure"
3. Follow same steps as Test 1, steps 3-9

### Test 3: Xbox Control

Tests if the integration still works after authentication.

1. **Test power on**
   - Send power on command
   - Xbox should turn on

2. **Test power off**
   - Send power off command
   - Xbox should turn off or go to sleep

3. **Test media control**
   - Play/pause
   - Volume control
   - Navigation (D-pad)

4. **Check presence**
   - Verify integration shows online status
   - Check if it shows current game/app

---

## What to Look For

### ✅ Success Indicators

1. **Microsoft Auth Page:**
   - Shows authorization code directly on page
   - Code is clearly visible and copyable
   - No redirect errors or blank pages

2. **Remote Setup:**
   - Accepts pasted code without errors
   - Exchanges code for tokens successfully
   - Completes setup without crashes

3. **Integration Function:**
   - Can control Xbox console
   - Status updates work
   - Presence detection works

### ❌ Failure Indicators

1. **Microsoft redirects elsewhere** - If Microsoft redirects instead of showing code
2. **Blank page after login** - If no code is displayed
3. **"Invalid redirect URI" error** - Shouldn't happen with OOB but check
4. **Token exchange fails** - If code doesn't work
5. **Integration crashes** - Check logs

---

## Troubleshooting

### Issue: Microsoft doesn't show code

**Symptoms:** After signing in, you don't see an authorization code

**Possible Causes:**
- Browser cached old flow behavior
- Microsoft account settings

**Solutions:**
1. Clear browser cache and cookies
2. Try incognito/private browsing mode
3. Try different browser
4. Check auth URL contains `redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob`

### Issue: Code doesn't work

**Symptoms:** Remote shows "Authentication Failed" after pasting code

**Possible Causes:**
- Code copied incorrectly (extra spaces, partial copy)
- Code expired (too much time passed)

**Solutions:**
1. Copy code again (don't let it expire)
2. Make sure to copy entire code
3. Paste immediately after copying
4. Try authentication flow again

### Issue: Integration crashes

**Symptoms:** Integration doesn't start or crashes during setup

**Solutions:**
1. Check Remote logs: Settings → System → Logs
2. Look for Python errors in logs
3. Verify artifact extracted correctly
4. Try reinstalling integration

---

## Expected Logs

### During Authentication

Look for these log messages:

```
[XBOX_AUTH] XboxAuth initialized with out-of-band flow.
[XBOX_AUTH] Generated auth URL: https://login.live.com/oauth20_authorize...
[XBOX_AUTH] Processing authorization code...
[XBOX_AUTH] Authorization code length: XXX
[XBOX_AUTH] ✅ OAuth2 tokens successfully retrieved.
```

### During Token Exchange

```
[XBOX_SETUP] Live ID captured. Starting OAuth authentication flow.
[XBOX_SETUP] Auth session closed
```

### Errors to Watch For

```
[XBOX_AUTH] Empty authorization code provided.
[XBOX_AUTH] Error during token exchange
```

---

## Comparison: Old vs New Flow

### Old Flow (v3.0.3 and earlier)

1. Click auth URL → Microsoft login
2. **Problem:** Redirected to `oauth20_desktop.srf` (broken page)
3. User had to copy entire URL from address bar
4. Parse code from URL
5. Often failed or showed blank page

### New Flow (v3.1.0)

1. Click auth URL → Microsoft login
2. **Microsoft displays code directly on page** ✨
3. User copies clean code (not URL)
4. Paste into setup
5. Works reliably every time

---

## Reporting Results

### If Successful ✅

Please report:
- Which test steps you completed
- What the Microsoft page looked like (screenshot appreciated!)
- Any differences from expected behavior
- Overall user experience rating

### If Failed ❌

Please report:
- Which step failed
- Exact error message
- What Microsoft page showed
- Screenshots if possible
- Remote logs (if accessible)

---

## Post-Testing

### If Testing is Successful

1. Mark v3.1.0 as stable (remove pre-release flag)
2. Update main branch
3. Announce update to users
4. Update integration documentation

### If Issues Found

1. Document the issue
2. Revert to v3.0.3 if needed
3. Fix in beta branch
4. Create v3.1.1 with fixes

---

## Technical Support

**GitHub Issues:** https://github.com/mase1981/uc-intg-xbox/issues
**Branch:** beta
**Commit:** e60f4f7

**Key Documentation:**
- [OAUTH_SOLUTION_OOB.md](OAUTH_SOLUTION_OOB.md) - Technical explanation
- [OAUTH_SOLUTION.md](OAUTH_SOLUTION.md) - Original research document

---

**Built:** January 17, 2026
**Release:** v3.1.0 (Pre-release)
**Status:** ✅ Ready for testing
**Method:** OAuth Out-of-Band (OOB) Flow
