from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import complaint
from accounts.models import registration
from django.db.models import Q
# Create your views here.

def create_request(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, "You must be logged in to file a complaint.")
            return redirect('login')

        # Try to attach the logged-in citizen; if not found (e.g., worker session), save without user
        user = None
        try:
            user = registration.objects.get(email=email)
        except registration.DoesNotExist:
            user = None

        location = request.POST['location']
        comType = request.POST['comType']
        description = request.POST['description']
        image = request.FILES.get('image')
        datetime = request.POST['datetime']
        status_val = request.POST.get('status', 'NEW')

        complaint.objects.create(
            user=user,
            location=location,
            comType=comType,
            description=description,
            image=image,
            datetime=datetime,
            status=status_val
        )
        messages.success(request, 'Complaint Registered successfully')
        return redirect('profile')
    else:
        return render(request, 'create_request.html')
    
def request_list(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You must be logged in to view your complaints.")
        return redirect('login')

    user = registration.objects.get(email=email)

    # Handle complaint update
    if request.method == "POST":
        complaint_id = request.POST.get('complaint_id')
        comp = get_object_or_404(complaint, id=complaint_id, user=user)

        comp.location = request.POST.get('location', comp.location)
        comp.comType = request.POST.get('comType', comp.comType)
        comp.description = request.POST.get('description', comp.description)
        if request.FILES.get('image'):
            comp.image = request.FILES['image']
        comp.save()
        messages.success(request, "Complaint updated successfully.")
        return redirect('profile')

    user_complaints = complaint.objects.filter(user=user).order_by('-datetime')
    grouped = {
        'NEW': [c for c in user_complaints if c.status == complaint.Status.NEW],
        'ACTIVE': [c for c in user_complaints if c.status == complaint.Status.ACTIVE],
        'RESOLVED': [c for c in user_complaints if c.status == complaint.Status.RESOLVED],
    }
    return render(request, 'request_list.html', {
        'complaints_new': grouped['NEW'],
        'complaints_active': grouped['ACTIVE'],
        'complaints_resolved': grouped['RESOLVED'],
    })

def track_status(request):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You must be logged in to track your complaints.")
        return redirect('login')

    try:
        user = registration.objects.get(email=email)
    except registration.DoesNotExist:
        messages.error(request, "Only citizens can track complaints.")
        return redirect('login')

    query = request.GET.get('q', '').strip()
    complaints_qs = complaint.objects.filter(user=user).order_by('-datetime')
    if query:
        # Allow search by id, type, location, status
        complaints_qs = complaints_qs.filter(
            Q(id__icontains=query) |
            Q(comType__icontains=query) |
            Q(location__icontains=query) |
            Q(status__icontains=query)
        )

    return render(request, 'track_status.html', {
        'complaints': complaints_qs,
        'query': query,
    })
