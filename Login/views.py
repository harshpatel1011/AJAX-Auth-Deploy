import sys
import json
import django
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.middleware.csrf import get_token
from .models import User

# Create your views here.

def get_current_user(request):
    user_id = request.session.get("user_id")
    if user_id:
        return User.objects.filter(id=user_id).first()


def index(request):
    user = get_current_user(request)
    if not user:
        return redirect("login")
    
    # Extract client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(',')[0].strip()
    else:
        client_ip = request.META.get('REMOTE_ADDR')
        
    # Get session details
    session_expiry_date = request.session.get_expiry_date().strftime('%Y-%m-%d %H:%M:%S')
    session_expiry_age = request.session.get_expiry_age()
    session_expire_on_close = request.session.get_expire_at_browser_close()
    
    # Get DB configuration
    db_engine = settings.DATABASES['default']['ENGINE'].split('.')[-1]
    db_name = settings.DATABASES['default']['NAME']
    
    context = {
        "name": user.name,
        "email": user.email,
        "user_id": user.id,
        "password_hash": user.password,
        "session_key": request.session.session_key,
        "session_expiry_date": session_expiry_date,
        "session_expiry_age": session_expiry_age,
        "session_expire_on_close": "Yes" if session_expire_on_close else "No",
        "client_ip": client_ip,
        "user_agent": request.META.get('HTTP_USER_AGENT'),
        "request_url": request.build_absolute_uri(),
        "request_method": request.method,
        "status_code": 200,
        "csrf_token": get_token(request),
        "cookies_json": json.dumps(dict(request.COOKIES), indent=2),
        "accept_language": request.META.get('HTTP_ACCEPT_LANGUAGE'),
        "referer": request.META.get('HTTP_REFERER', 'None (Direct)'),
        "django_version": django.get_version(),
        "python_version": sys.version.split(' ')[0],
        "db_engine": db_engine,
        "db_name": db_name,
        "debug_mode": "Enabled" if settings.DEBUG else "Disabled",
        "timezone": settings.TIME_ZONE,
        "server_time": timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    return render(request, "index.html", context)


def login(request):
    if get_current_user(request):
        return redirect("index")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = User.objects.filter(email=email).first()

        if user:
            if check_password(password, user.password):
                request.session["user_id"] = user.id
                return JsonResponse({"status": "success", "redirect_url": "/"})

        return JsonResponse({"status": "error", "message": "Invalid email or password"})

    return render(request, "login.html")


def signup(request):
    if get_current_user(request):
        return redirect("index")

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("confirm_password")

        if password != password_confirm:
            return JsonResponse({"status": "error", "message": "Passwords do not match"})

        if not name or not email or not password or not password_confirm:
            return JsonResponse(
                {"status": "error", "message": "All fields are required"}
            )

        if "@" not in email:
            return JsonResponse(
                {"status": "error", "message": "Please enter a valid email address"}
            )

        if len(password) < 8:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Password must be at least 8 characters long",
                }
            )

        if User.objects.filter(email=email).exists():
            return JsonResponse(
                {"status": "error", "message": "Email is already registered"}
            )

        hashed_password = make_password(password)
        user = User.objects.create(name=name, email=email, password=hashed_password)
        request.session["user_id"] = user.id
        return JsonResponse({"status": "success", "redirect_url": "/"})

    return render(request, "signup.html")


def logout(request):
    request.session.flush()
    return redirect("login")
