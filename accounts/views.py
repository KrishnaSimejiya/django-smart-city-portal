from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password,make_password
from django.contrib.auth import logout as auth_logout
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from .models import registration
from workers.models import wregistration
from services.models import complaint, WorkAssignment

# Create your views here.
def role(request):
    # Public landing page with real stats
    stats = {
        'citizens': registration.objects.count(),
        'active_workers': wregistration.objects.count(),
        'complaints_resolved': complaint.objects.filter(status=complaint.Status.RESOLVED).count(),
        'active_complaints': complaint.objects.filter(status=complaint.Status.ACTIVE).count(),
    }
    return render(request, 'role.html', { 'stats': stats })

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        mobileno = request.POST['mobileno']
        address = request.POST['address']
        password = request.POST['password']
        image = request.FILES.get('image')
        if name.lower() == 'admin' or email.lower() == 'admin@gmail.com':
            messages.error(request,"You can't register with admin email or name")
            return render(request, 'register.html')
        if registration.objects.filter(email=email).exists():
            messages.error(request,"user already exists with this email")
            return render(request, 'register.html')
        hashed_password = make_password(password)

        # Build create kwargs to keep logic simple and readable
        create_kwargs = {
            'name': name,
            'email': email,
            'mobileno': mobileno,
            'password': hashed_password,
            'address': address,
        }

        # If user uploaded an image, save it; otherwise store empty so template shows static default
        if image:
            create_kwargs['image'] = image
        else:
            create_kwargs['image'] = ''

        registration.objects.create(**create_kwargs)
        messages.success(request,'Registration completed successfully')
        return render(request,'login.html')
    else:
        return render(request, 'register.html')

def login(request):
    if request.method == "POST":
        print(request.POST)
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = registration.objects.get(email = email)
            if user.name.lower() == 'admin' and email.lower() == 'admin@gmail.com':
                return redirect('dashboard')
            if check_password(password,user.password):
                request.session['email'] = email
                # Redirect to udashboard to ensure statistics are computed on first render
                return redirect('udashboard')
            else:
                messages.error(request,'Invalid Credentials')
                return redirect('login')
        except registration.DoesNotExist:
            messages.error(request,'Invalid Credentials')
    return render(request,'login.html')

def profile(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You must be logged in.")
        return redirect('login')
    # Gracefully handle missing registration (e.g., worker session)
    try:
        user = registration.objects.get(email=email)
    except registration.DoesNotExist:
        messages.error(request, "User account not found. Please login as a citizen user.")
        return redirect('login')

    if request.method == "POST":
        user.name = request.POST.get('name', user.name)
        user.mobileno = request.POST.get('mobileno', user.mobileno)
        user.address = request.POST.get('address', user.address)
        if request.FILES.get('image'):
            user.image = request.FILES['image']
        user.save()
        messages.success(request, "Profile updated successfully.")
    
    return render(request, 'profile.html', {'user': user})
   
def udashboard(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You must be logged in.")
        return redirect('login')
    
    try:
        user = registration.objects.get(email=email)
    except registration.DoesNotExist:
        messages.error(request, "User account not found. Please login again.")
        return redirect('login')
    
    # Get complaint statistics for the user
    from services.models import complaint
    user_complaints = complaint.objects.filter(user=user)
    
    stats = {
        'total_complaints': user_complaints.count(),
        'new_complaints': user_complaints.filter(status=complaint.Status.NEW).count(),
        'active_complaints': user_complaints.filter(status=complaint.Status.ACTIVE).count(),
        'resolved_complaints': user_complaints.filter(status=complaint.Status.RESOLVED).count(),
    }
    
    return render(request, 'udashboard.html', {'user': user, 'stats': stats})




def logout(request):
    auth_logout(request)
    return render(request, 'home.html')

# --- Password Reset (Citizen) ---
def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()
        if not email:
            messages.error(request, "Please enter your email.")
            return render(request, 'password_reset_request.html')

        try:
            user = registration.objects.get(email=email)
        except registration.DoesNotExist:
            # Don't reveal whether the email exists
            messages.success(request, "If the email exists, a reset link has been sent.")
            return render(request, 'password_reset_request.html')

        payload = { 'user_id': user.id, 'scope': 'citizen_reset' }
        token = signing.dumps(payload, salt='accounts.password.reset')
        reset_url = request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={'token': token})
        )

        subject = 'Reset your Smart City Portal password'
        message = f"Hello {user.name},\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email."
        # Basic credential guard to avoid silent auth failures
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            masked_user = settings.EMAIL_HOST_USER or '(empty)'
            masked_pwd = '(set)' if settings.EMAIL_HOST_PASSWORD else '(empty)'
            messages.error(
                request,
                f"Email is not configured on the server. EMAIL_HOST_USER={masked_user} EMAIL_HOST_PASSWORD={masked_pwd}."
            )
            return render(request, 'password_reset_request.html')

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        except Exception as exc:
            messages.error(request, f"Email send failed: {exc}")
            return render(request, 'password_reset_request.html')

        messages.success(request, "If the email exists, a reset link has been sent.")
        return render(request, 'password_reset_request.html')

    return render(request, 'password_reset_request.html')

def password_reset_confirm(request, token):
    try:
        data = signing.loads(token, salt='accounts.password.reset', max_age=60*60*24)
        if data.get('scope') != 'citizen_reset':
            raise signing.BadSignature('Invalid scope')
    except signing.SignatureExpired:
        messages.error(request, 'This reset link has expired. Please request a new one.')
        return redirect('password_reset_request')
    except signing.BadSignature:
        messages.error(request, 'Invalid reset link.')
        return redirect('password_reset_request')

    user = get_object_or_404(registration, id=data.get('user_id'))

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        if not new_password:
            messages.error(request, 'Password cannot be empty.')
        else:
            user.password = make_password(new_password)
            user.save()
            messages.success(request, 'Your password has been reset. Please login.')
            return redirect('login')

    return render(request, 'password_reset_confirm.html', { 'user': user })