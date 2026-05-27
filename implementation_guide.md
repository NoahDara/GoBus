# GOBUS GOOGLE OAUTH IMPLEMENTATION GUIDE

## 📋 Quick Summary

You now have:
1. ✅ Modern login & register templates
2. ✅ Google OAuth service layer
3. ✅ Views for authentication & callbacks
4. ✅ URL routing
5. ✅ Django settings configuration
6. ✅ Complete Google Console setup guide

---

## 🚀 IMPLEMENTATION STEPS (In Order)

### Step 1: Install Dependencies

```bash
pip install -r requirements_with_oauth.txt
```

Or minimal installation:

```bash
pip install google-auth
```

---

### Step 2: Set Up Google OAuth Credentials

**Follow the complete guide in: `GOOGLE_OAUTH_SETUP_GUIDE.md`**

This will give you:
- Google Client ID
- Google Client Secret

---

### Step 3: Add Credentials to Django

Create `.env` file in project root:

```
GOOGLE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET
SECRET_KEY=your-django-secret-key
```

Add to `.gitignore`:

```
.env
*.env
```

---

### Step 4: Copy Files to Your Project

```
# Copy these files to your GoBus project:

accounts/views.py ← accounts_views_improved.py
accounts/urls.py ← accounts_urls_updated.py
accounts/services.py ← accounts_services.py
accounts/admin.py ← (you already have this)

templates/accounts/login.html ← login.html
templates/accounts/register.html ← register.html

# Create this directory if it doesn't exist:
mkdir -p static/images/
```

---

### Step 5: Update Django Settings

**File: `config/settings.py` (your main settings file)**

Add these imports at the top:

```python
import os
from dotenv import load_dotenv

load_dotenv()
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'debug_toolbar',
    'rest_framework',
    'corsheaders',
    
    # Local
    'accounts',
    'drivers',
    'buses',
    'bookings',
    'payments',
    'notifications',
    'dashboard',
    'helpers',
]
```

Add Google OAuth configuration (copy from `settings_google_oauth.py`):

```python
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

# CORS
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
```

---

### Step 6: Update Main URLs

**File: `config/urls.py`**

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
    path('accounts/', include('accounts.urls')),  # ← Add this
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
```

---

### Step 7: Create Bus Image Directory

```bash
mkdir -p static/images/
```

**Place your bus image here:**
- `static/images/login_bus.png` (recommended: 100x100 px)

Or create a placeholder:

```bash
# Create an empty placeholder
touch static/images/login_bus.png
```

---

### Step 8: Update Login Template with Your Client ID

**File: `templates/accounts/login.html`**

Find this line (around line 200):

```html
<div id="g_id_onload"
     data-client_id="YOUR_GOOGLE_CLIENT_ID"
     ...
```

Replace `YOUR_GOOGLE_CLIENT_ID` with your actual Client ID:

```html
<div id="g_id_onload"
     data-client_id="123456789.apps.googleusercontent.com"
     data-callback="handleCredentialResponse"
     data-auto_prompt="false">
</div>
```

Do the same in `templates/accounts/register.html` (line ~290):

```javascript
const clientId = 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com';
```

---

### Step 9: Run Migrations

```bash
python manage.py migrate
```

---

### Step 10: Test Locally

```bash
python manage.py runserver
```

**Visit:**
- Login page: `http://localhost:8000/accounts/login/`
- Register page: `http://localhost:8000/accounts/register/`

---

## 🧪 Testing Google OAuth

### Test Flow:

1. Go to `http://localhost:8000/accounts/login/`
2. Click "Sign in with Google"
3. You should be redirected to Google Login
4. After authentication, you should be automatically logged in
5. Should redirect to `/dashboard/`

### What Happens Behind the Scenes:

1. **Frontend** (JavaScript) sends Google JWT token to backend
2. **Backend** (`GoogleAuthView`) verifies token
3. **Backend** creates/updates user in database
4. **Backend** logs user in
5. **Frontend** redirects to dashboard

---

## 📁 File Structure

```
GoBus/
├── accounts/
│   ├── views.py ← (updated with Google OAuth)
│   ├── urls.py ← (updated with Google OAuth routes)
│   ├── services.py ← (NEW: Google OAuth service)
│   ├── admin.py
│   └── migrations/
│
├── templates/
│   └── accounts/
│       ├── login.html ← (NEW: Modern login with Google button)
│       ├── register.html ← (NEW: Modern signup with Google button)
│       ├── profile.html
│       ├── profile_edit.html
│       └── change_password.html
│
├── static/
│   └── images/
│       └── login_bus.png ← (ADD YOUR BUS IMAGE HERE)
│
├── config/
│   └── settings.py ← (add Google OAuth config)
│   └── urls.py ← (include accounts.urls)
│
├── .env ← (NEW: Store credentials here)
├── .gitignore ← (add .env)
└── requirements.txt ← (add google-auth)
```

---

## 🔐 Security Checklist

### Development:
- ✅ Store credentials in `.env`
- ✅ Add `.env` to `.gitignore`
- ✅ Never commit credentials to git
- ✅ Token verification on backend (GoogleAuthService)

### Production:
- [ ] Use environment variables (not .env file)
- [ ] Enable HTTPS only
- [ ] Update `ALLOWED_HOSTS` in settings
- [ ] Update `CORS_ALLOWED_ORIGINS` with production domain
- [ ] Add production domain to Google Console
- [ ] Set `DEBUG = False`
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Use a secrets manager (AWS Secrets Manager, etc.)

---

## 🐛 Troubleshooting

### Problem: Google button doesn't show

**Solution:**
```bash
# Check browser console (F12)
# Make sure script loaded: https://accounts.google.com/gsi/client
# Check that Client ID is correct
```

### Problem: "The redirect_uri parameter does not match"

**Solution:**
1. Go to Google Cloud Console
2. Edit your OAuth credential
3. Ensure redirect URI matches exactly:
   - `http://localhost:8000/accounts/google/callback/`

### Problem: "Invalid Client ID"

**Solution:**
- Copy Client ID again from Google Console
- Include `.apps.googleusercontent.com`
- Make sure it's in `data-client_id` attribute in HTML

### Problem: "Fetch error" in console

**Solution:**
```python
# Add CORS to settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
]
```

### Problem: User not being created

**Solution:**
```python
# Check GoogleAuthService.authenticate_user()
# Make sure email is in Google token
# Check Django logs for errors
```

---

## 📊 User Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER LOGIN FLOW                           │
└─────────────────────────────────────────────────────────────┘

                         Frontend
                            │
                    ┌────────┴─────────┐
                    │                  │
            Traditional Login    Sign in with Google
                    │                  │
                    ├──────────────────┤
                    │                  │
              Submit Form         Google JS SDK
              (email+pass)        (creates JWT)
                    │                  │
                    └────────┬─────────┘
                             │
                    POST /accounts/login/
                    (traditional) OR
                    POST /accounts/google/auth/
                    (with JWT token)
                             │
                    ┌────────▼────────┐
                    │  Django Backend │
                    └─────┬───────────┘
                          │
                ┌─────────┴─────────┐
                │                   │
         Traditional Auth    Google OAuth
         (check password)     (verify JWT)
                │                   │
                └─────────┬─────────┘
                          │
                   User Found/Created
                          │
                   ┌──────▼──────┐
                   │  login()    │
                   └──────┬──────┘
                          │
                  JSON Response:
                  {
                    "success": true,
                    "redirect_url": "/dashboard/"
                  }
                          │
                    ┌──────▼──────┐
                    │  Redirect   │
                    │ to Dashboard│
                    └─────────────┘
```

---

## 📚 Documentation Links

- **Google Identity Services**: https://developers.google.com/identity
- **OAuth 2.0 Guide**: https://developers.google.com/identity/protocols/oauth2
- **Django Documentation**: https://docs.djangoproject.com/
- **Bootstrap Documentation**: https://getbootstrap.com/docs/

---

## 🎨 Customization Ideas

### Styling:
- Change gradient colors in login.html
- Modify bus image size/position
- Adjust form layout for mobile

### Features to Add:
- Email verification
- Two-factor authentication
- Social login for other providers (Facebook, GitHub)
- User profile picture from Google
- Remember me functionality
- Password reset flow

### Integration:
- Send welcome email after signup
- Log login attempts for security
- Sync user profile data with Google
- Link multiple social accounts to one user

---

## ✅ What You Get

| Feature | Traditional | Google OAuth |
|---------|-----------|---|
| Email + Password Login | ✅ | ❌ |
| Google Sign In | ❌ | ✅ |
| Auto User Creation | ✅ | ✅ |
| Session Management | ✅ | ✅ |
| Logout | ✅ | ✅ |
| Profile Management | ✅ | ✅ |
| Password Change | ✅ | ❌ (use Google) |

---

## 🎯 Next Steps

1. **Complete Google Console setup** (follow GOOGLE_OAUTH_SETUP_GUIDE.md)
2. **Copy all files** to your project
3. **Update settings.py** with Google credentials
4. **Test locally** at localhost:8000
5. **Deploy to production** with proper HTTPS & environment variables

---

## 📞 Support

If you encounter issues:

1. Check browser console (F12) for JavaScript errors
2. Check Django logs for backend errors
3. Verify Google Console configuration
4. Test with `curl` or Postman if needed
5. Check `.env` file has correct credentials

---

**Happy coding! 🚀**