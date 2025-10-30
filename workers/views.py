from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password,make_password
from .models import wregistration
from services.models import WorkAssignment, complaint
from django.views.decorators.http import require_http_methods
from django.core import signing
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

def whome(request):
    return render(request, 'whome.html')

def wdashboard(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You must be logged in.")
        return redirect('wlogin')
    user = get_object_or_404(wregistration, email=email)
    assignments = WorkAssignment.objects.filter(worker=user).order_by('-assigned_at')[:200]
    new_work_count = WorkAssignment.objects.filter(worker=user, is_seen=False).count()
    
    # Get worker statistics
    worker_assignments = WorkAssignment.objects.filter(worker=user)
    
    stats = {
        'total_assignments': worker_assignments.count(),
        'new_assignments': worker_assignments.filter(is_seen=False).count(),
        'active_assignments': worker_assignments.filter(complaint__status=complaint.Status.ACTIVE).count(),
        'completed_assignments': worker_assignments.filter(complaint__status=complaint.Status.RESOLVED).count(),
    }
    
    return render(request, 'wdashboard.html', {
        'user': user, 
        'assignments': assignments, 
        'new_work_count': new_work_count,
        'stats': stats
    })

def wregister(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        mobileno = request.POST['mobileno']
        address = request.POST['address']
        password = request.POST['password']
        image = request.FILES.get('image')
        department = request.POST['department']
        avaialbility = request.POST['avaialbility']
        if name.lower() == 'admin' or email.lower() == 'admin@gmail.com':
            messages.error(request,"You can't register with admin email or name")
            return render(request, 'wregister.html')
        if wregistration.objects.filter(email=email).exists():
            messages.error(request,"user already exists with this email")
            return render(request, 'wregister.html')
        hashed_password = make_password(password)
        wregistration.objects.create(
            name=name,
            email=email,
            mobileno=mobileno,
            password=hashed_password,
            address=address,
            image=image,
            department=department,
            avaialbility=avaialbility
        )
        messages.success(request,'Registration completed successfully')
        return redirect('wlogin')
    else:
        return render(request, 'wregister.html')

def wlogin(request):
    if request.method == "POST":
        print(request.POST)
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = wregistration.objects.get(email = email)
            if user.name.lower() == 'admin' and email.lower() == 'admin@gmail.com':
                return redirect('dashboard')
            if check_password(password,user.password):
                request.session['email'] = user.email
                # Redirect to wdashboard to ensure statistics are computed on first render
                return redirect('wdashboard')
            else:
                messages.error(request,'Invalid Credentials')
                return redirect('wlogin')
        except wregistration.DoesNotExist:
            messages.error(request,'Invalid Credentials')
    return render(request,'wlogin.html')


def new_work(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You must be logged in.")
        return redirect('wlogin')
    
    user = get_object_or_404(wregistration, email=email)
    assignments = WorkAssignment.objects.filter(worker=user).order_by('-assigned_at')
    
    WorkAssignment.objects.filter(worker=user, is_seen=False).update(is_seen=True)
    
    return render(request, 'new_work.html', {'user': user, 'assignments': assignments})

@require_http_methods(["GET", "POST"])
def update_complaint_status(request, complaint_id):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You must be logged in.")
        return redirect('wlogin')

    worker = get_object_or_404(wregistration, email=email)
    comp = get_object_or_404(complaint, id=complaint_id)

    is_assigned = WorkAssignment.objects.filter(worker=worker, complaint=comp).exists()
    if not is_assigned:
        messages.error(request, "You are not assigned to this complaint.")
        return redirect('new_work')

    if request.method == "POST":
        new_status = request.POST.get('status')
        if new_status not in dict(complaint.Status.choices).keys():
            messages.error(request, "Invalid status.")
            return redirect('update_complaint_status', complaint_id=complaint_id)

        comp.status = new_status
        comp.save()
        messages.success(request, f"Complaint {comp.id} status updated to {new_status}.")
        return redirect('new_work')

    return render(request, 'worker_update_status.html', {
        'user': worker,
        'comp': comp,
        'status_choices': complaint.Status.choices
    })

def completed_complaints(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You must be logged in.")
        return redirect('wlogin')

    worker = get_object_or_404(wregistration, email=email)
    assignments = WorkAssignment.objects.filter(worker=worker, complaint__status=complaint.Status.RESOLVED).order_by('-assigned_at')

    return render(request, 'completed_complaints.html', {
        'user': worker,
        'assignments': assignments
    })

def wprofile(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You must be logged in.")
        return redirect('wlogin')

    user = get_object_or_404(wregistration, email=email)

    if request.method == "POST":
        user.name = request.POST.get('name', user.name)
        user.mobileno = request.POST.get('mobileno', user.mobileno)
        user.address = request.POST.get('address', user.address)
        user.department = request.POST.get('department', user.department)
        user.avaialbility = request.POST.get('avaialability', user.avaialbility)
        if request.FILES.get('image'):
            user.image = request.FILES['image']
        user.save()
        messages.success(request, "Profile updated successfully.")
    
    return render(request, 'wprofile.html', {'user': user})

# --- Password Reset (Worker) ---
def wpassword_reset_request(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()
        if not email:
            messages.error(request, "Please enter your email.")
            return render(request, 'wpassword_reset_request.html')

        try:
            user = wregistration.objects.get(email=email)
        except wregistration.DoesNotExist:
            messages.success(request, "If the email exists, a reset link has been sent.")
            return render(request, 'wpassword_reset_request.html')

        payload = { 'user_id': user.id, 'scope': 'worker_reset' }
        token = signing.dumps(payload, salt='workers.password.reset')
        reset_url = request.build_absolute_uri(
            reverse('wpassword_reset_confirm', kwargs={'token': token})
        )

        subject = 'Reset your Smart City Portal worker password'
        message = f"Hello {user.name},\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email."
        # Basic credential guard to avoid silent auth failures
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            masked_user = settings.EMAIL_HOST_USER or '(empty)'
            masked_pwd = '(set)' if settings.EMAIL_HOST_PASSWORD else '(empty)'
            messages.error(
                request,
                f"Email is not configured on the server. EMAIL_HOST_USER={masked_user} EMAIL_HOST_PASSWORD={masked_pwd}."
            )
            return render(request, 'wpassword_reset_request.html')

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        except Exception as exc:
            messages.error(request, f"Email send failed: {exc}")
            return render(request, 'wpassword_reset_request.html')

        messages.success(request, "If the email exists, a reset link has been sent.")
        return render(request, 'wpassword_reset_request.html')

    return render(request, 'wpassword_reset_request.html')

def wpassword_reset_confirm(request, token):
    try:
        data = signing.loads(token, salt='workers.password.reset', max_age=60*60*24)
        if data.get('scope') != 'worker_reset':
            raise signing.BadSignature('Invalid scope')
    except signing.SignatureExpired:
        messages.error(request, 'This reset link has expired. Please request a new one.')
        return redirect('wpassword_reset_request')
    except signing.BadSignature:
        messages.error(request, 'Invalid reset link.')
        return redirect('wpassword_reset_request')

    user = get_object_or_404(wregistration, id=data.get('user_id'))

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        if not new_password:
            messages.error(request, 'Password cannot be empty.')
        else:
            user.password = make_password(new_password)
            user.save()
            messages.success(request, 'Your password has been reset. Please login.')
            return redirect('wlogin')

    return render(request, 'wpassword_reset_confirm.html', { 'user': user })