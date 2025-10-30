from django.shortcuts import render, redirect,HttpResponse,get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from accounts.models import registration
from services.models import complaint, WorkAssignment
from workers.models import wregistration

def admin_login(request):
    if request.method == "POST":
        print(request.POST)
        email = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = registration.objects.get(email=email)

            if user.name.lower() == 'admin' and user.email.lower() == 'admin@gmail.com':
                request.session['email'] = email
                return redirect('dashboard')
            else:
                messages.error(request, 'You are not authorized as Admin')
                return redirect('admin_login')

        except registration.DoesNotExist:
            messages.error(request, 'Invalid Admin Credentials')
            return redirect('admin_login')

    return render(request, 'admin_login.html')

# Create your views here.
def dashboard(request):
    #return HttpResponse('this is admin dashboard page')
    total_users = registration.objects.count()
    new_complaints_count = complaint.objects.filter(status=complaint.Status.NEW).count()
    total_workers = wregistration.objects.count()
    active_services = complaint.objects.filter(status=complaint.Status.ACTIVE).count()
    pending_issues = complaint.objects.filter(status=complaint.Status.NEW).count()
    resolved_complaints = complaint.objects.filter(status=complaint.Status.RESOLVED).count()
    return render(request,'dashboard.html',{
        'total_users': total_users,
        'new_complaints_count': new_complaints_count,
        'total_workers': total_workers,
        'active_services': active_services,
        'pending_issues': pending_issues,
        'resolved_complaints': resolved_complaints,
    })

def new_complaints(request):
    # Show only brand NEW complaints until assigned/resolved
    items_qs = complaint.objects.filter(status=complaint.Status.NEW).order_by('-id')
    # Mark as seen as soon as admin visits page
    complaint.objects.filter(id__in=items_qs.values_list('id', flat=True)).update(is_seen=True)
    return render(request, 'new_complaints.html', {
        'complaints': list(items_qs[:200]),
        'new_complaints_count': items_qs.count()
    })

def assign_work(request, complaint_id):
    comp = get_object_or_404(complaint, id=complaint_id)
    from workers.models import wregistration
    # Get all workers for the searchable dropdown
    all_workers = wregistration.objects.all().order_by('name')
    # Filter workers by department that matches the complaint type (simple mapping)
    # Assuming comType stores department/category text
    workers = wregistration.objects.filter(department__iexact=comp.comType)
    if request.method == 'POST':
        worker_id = request.POST.get('worker_id')
        notes = request.POST.get('notes')
        worker = get_object_or_404(wregistration, id=worker_id)
        WorkAssignment.objects.create(complaint=comp, worker=worker, notes=notes)
        comp.status = complaint.Status.ACTIVE
        comp.save()
        messages.success(request, f"Assigned complaint #{comp.id} to {worker.name}.")
        return redirect('new_complaints')
    return render(request, 'assign_work.html', {'complaint': comp, 'workers': workers, 'all_workers': all_workers})

def all_users(request):
    if request.method == "POST":
        # Handle inline edit
        if 'edit_user_id' in request.POST:
            user = get_object_or_404(registration, id=request.POST['edit_user_id'])
            user.name = request.POST.get('name')
            user.email = request.POST.get('email')
            user.mobileno = request.POST.get('mobileno')
            user.address = request.POST.get('address')
            if request.FILES.get('image'):
                user.image = request.FILES['image']
            user.save()
            messages.success(request, "User updated successfully.")
            return redirect('all_users')

        # When clicking ✏️ button to start edit
        elif 'start_edit_user_id' in request.POST:
            users = registration.objects.all()
            return render(request, 'all_users.html', {
                'users': users,
                'edit_id': int(request.POST['start_edit_user_id']),
                'new_complaints_count': complaint.objects.filter(status=complaint.Status.NEW).count()
            })

        # Handle new user addition
        else:
            name = request.POST.get('name')
            email = request.POST.get('email')
            mobileno = request.POST.get('mobileno')
            address = request.POST.get('address')
            image = request.FILES.get('image')
            if registration.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
            else:
                registration.objects.create(
                    name=name,
                    email=email,
                    mobileno=mobileno,
                    address=address,
                    image=image
                )
                messages.success(request, "User added successfully.")
            return redirect('all_users')

    users = registration.objects.all()
    new_complaints_count = complaint.objects.filter(status=complaint.Status.NEW).count()
    return render(request, 'all_users.html', {
        'users': users,
        'new_complaints_count': new_complaints_count
    })


def all_workers(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        mobileno = request.POST.get('mobileno')
        address = request.POST.get('address')
        department = request.POST.get('department')
        avaialbility = request.POST.get('avaialbility')
        image = request.FILES.get('image')

        if wregistration.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            wregistration.objects.create(
                name=name,
                email=email,
                mobileno=mobileno,
                address=address,
                department=department,
                avaialbility=avaialbility,
                image=image
            )
            messages.success(request, "worker added successfully.")
        return redirect('all_workers')  

    workers = wregistration.objects.all()
    new_complaints_count = complaint.objects.filter(status=complaint.Status.NEW).count()
    return render(request, 'all_workers.html', {
        'workers': workers,
        'new_complaints_count': new_complaints_count
    })

def delete_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(registration, id=user_id)
        user.delete()
        messages.success(request, "User deleted successfully.")
    return redirect('all_users')

def reset_password(request, user_id):
    # Try to find in citizens first; if not, try in workers
    user_obj = None
    is_worker = False
    try:
        user_obj = registration.objects.get(id=user_id)
    except registration.DoesNotExist:
        try:
            user_obj = wregistration.objects.get(id=user_id)
            is_worker = True
        except wregistration.DoesNotExist:
            return redirect('dashboard')

    if request.method == "POST":
        new_password = request.POST.get('new_password')
        if new_password:
            user_obj.password = make_password(new_password)
            user_obj.save()
            messages.success(request, f"Password reset for {user_obj.email} successfully.")
        else:
            messages.error(request, "Password field cannot be empty.")
        return redirect('wlogin' if is_worker else 'login')

    return render(request, 'reset_password.html', {
        'user': user_obj,
        'back_url_name': 'all_workers' if is_worker else 'all_users'
    })

def all_services(request):
    # Get all complaints with their related data
    complaints = complaint.objects.select_related('user').prefetch_related('assignments__worker').all().order_by('-datetime')
    
    # Create a list to store complaint data with worker information
    services_data = []
    for comp in complaints:
        # Get the assigned worker for resolved complaints
        assigned_worker = None
        if comp.status == complaint.Status.RESOLVED:
            assignment = comp.assignments.first()
            if assignment:
                assigned_worker = assignment.worker
        
        services_data.append({
            'complaint': comp,
            'assigned_worker': assigned_worker
        })
    
    return render(request, 'all_services.html', {
        'services_data': services_data,
        'new_complaints_count': complaint.objects.filter(status=complaint.Status.NEW).count()
    })


