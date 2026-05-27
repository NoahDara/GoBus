# GOOGLE OAUTH SETUP GUIDE - Complete Instructions

## Step 1: Create Google Cloud Project

1. Go to **Google Cloud Console**: https://console.cloud.google.com
2. Click on the **Project Dropdown** (top left)
3. Click **NEW PROJECT**
4. Enter project name: **GoBus** (or your preferred name)
5. Click **CREATE**
6. Wait for project to be created (2-3 minutes)

---

## Step 2: Enable Google+ API

1. In Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for **"Google+ API"**
3. Click on **Google+ API**
4. Click **ENABLE**
5. Wait for it to enable (30 seconds)

---

## Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** (top left)
3. Select **OAuth client ID**
4. You'll see a warning: "To create an OAuth client ID, you must first set a user consent screen"
   - Click **CONFIGURE CONSENT SCREEN**

---

## Step 4: Set Up OAuth Consent Screen

1. Choose **External** user type
2. Click **CREATE**
3. Fill in the required fields:
   - **App name**: GoBus
   - **User support email**: your-email@gmail.com
   - **Developer contact information**: your-email@gmail.com
4. Click **SAVE AND CONTINUE**
5. For **Scopes**, add these:
   - `openid`
   - `email`
   - `profile`
6. Click **SAVE AND CONTINUE**
7. For **Test users**, add your email (for testing)
8. Click **SAVE AND CONTINUE** → **BACK TO DASHBOARD**

---

## Step 5: Create OAuth 2.0 Client ID (Finally!)

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Select **Web application**
4. Fill in configuration:
   - **Name**: GoBus OAuth Client
   
5. **Authorized JavaScript origins** (add both):
   ```
   http://localhost:8000
   http://127.0.0.1:8000
   https://yourdomain.com  (for production)
   ```

6. **Authorized redirect URIs** (add all):
   ```
   http://localhost:8000/accounts/google/callback/
   http://127.0.0.1:8000/accounts/google/callback/
   https://yourdomain.com/accounts/google/callback/  (for production)
   ```

7. Click **CREATE**
8. You'll see a popup with:
   - **Client ID**: `XXXXXXXXXXX.apps.googleusercontent.com`
   - **Client Secret**: `XXXXXXXXXXX`

---

## Step 6: Copy Your Credentials

**SAVE THESE SECURELY!**

```
Google Client ID:     YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
Google Client Secret: YOUR_GOOGLE_CLIENT_SECRET
```

### Store in Django Settings

Update your `settings.py`:

```python
GOOGLE_OAUTH_CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com'
GOOGLE_OAUTH_CLIENT_SECRET = 'YOUR_GOOGLE_CLIENT_SECRET'
```

### Or Use Environment Variables (Recommended)

Create `.env` file in project root:

```
GOOGLE_OAUTH_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
```

Then in `settings.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
```

---

## Step 7: Install Required Package

```bash
pip install google-auth
```

Or if using django-allauth:

```bash
pip install django-allauth google-auth
```

---

## Step 8: Update Django Settings

Copy the configuration from `settings_google_oauth.py` to your main `settings.py`:

```python
GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
GOOGLE_OAUTH_REDIRECT_URI = 'http://localhost:8000/accounts/google/callback/'
```

---

## Step 9: Update Main urls.py

Add accounts URLs to main `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView

urlpatterns = [
    path('__debug__/', include('debug_toolbar.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # Add this line
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
```

---

## Step 10: Update Login Template

In `templates/accounts/login.html`, replace:

```html
<div id="g_id_onload"
     data-client_id="YOUR_GOOGLE_CLIENT_ID"
     data-callback="handleCredentialResponse"
     data-auto_prompt="false">
</div>
```

With your actual Client ID:

```html
<div id="g_id_onload"
     data-client_id="YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
     data-callback="handleCredentialResponse"
     data-auto_prompt="false">
</div>
```

---

## Step 11: Create Bus Image

Create/place bus image at:
```
static/images/login_bus.png
```

This will be displayed in the login page header.

Recommended size: **100x100 pixels** (or any square aspect ratio)

If you don't have an image, use a placeholder:
```bash
# Create a simple placeholder
touch static/images/login_bus.png
```

---

## Step 12: Test Google OAuth Locally

1. Start Django:
   ```bash
   python manage.py runserver
   ```

2. Go to: `http://localhost:8000/accounts/login/`

3. Click **"Sign in with Google"**

4. You should be redirected to Google Login

5. After authentication, you should be logged in automatically!

---

## Troubleshooting

### Issue: "The redirect_uri parameter does not match"
- **Fix**: Make sure redirect URI in Google Console matches your login template and urls.py

### Issue: "Invalid Client ID"
- **Fix**: Copy Client ID exactly from Google Console, including `.apps.googleusercontent.com`

### Issue: Google button not showing
- **Fix**: Make sure you have internet connection and script loaded:
  ```html
  <script src="https://accounts.google.com/gsi/client" async defer></script>
  ```

### Issue: CORS Error
- **Fix**: Add to `settings.py`:
  ```python
  CORS_ALLOWED_ORIGINS = [
      'http://localhost:8000',
      'https://yourdomain.com',
  ]
  ```

---

## Production Checklist

Before deploying to production:

- [ ] Update `GOOGLE_OAUTH_REDIRECT_URI` to your domain
- [ ] Add production domain to Google Console **Authorized JavaScript origins**
- [ ] Add production domain to Google Console **Authorized redirect URIs**
- [ ] Set `DEBUG = False` in settings.py
- [ ] Use environment variables for Client ID & Secret
- [ ] Set up HTTPS on production
- [ ] Test Google OAuth on production domain

---

## Security Best Practices

1. **Never commit credentials** to git
   ```bash
   # Add to .gitignore
   .env
   *.env
   ```

2. **Use environment variables** in production
   ```python
   GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
   ```

3. **Verify tokens on backend** (done in GoogleAuthService)

4. **Use HTTPS only** in production

5. **Rotate credentials** regularly in Google Console

---

## Helpful Links

- Google Cloud Console: https://console.cloud.google.com
- OAuth 2.0 Playground: https://developers.google.com/oauthplayground
- Google Identity Services: https://developers.google.com/identity
- Django AllAuth Docs: https://django-allauth.readthedocs.io/

---

## Next Steps

1. Implement email verification (optional)
2. Set up password reset flow
3. Add user profile picture from Google
4. Implement two-factor authentication (optional)
5. Add social login for other providers (Facebook, GitHub, etc.)