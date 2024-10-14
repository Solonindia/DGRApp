from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from .forms import CustomUserCreationForm  # Make sure LoginForm is imported from the correct path

def home_page(request):
    return render(request, 'home_page.html')

def redirect_to_home(request):
    return redirect('home')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('user')  # Redirect to the success page
        else:
            return render(request, 'user_login.html', {'error_message': 'Invalid credentials'})
    return render(request, 'user_login.html')

FIXED_USERNAME = 'Solonindia'
FIXED_PASSWORD = 'Sipl$2024'

def login1_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the provided username and password match the fixed ones
        if username == FIXED_USERNAME and password == FIXED_PASSWORD:
            # Redirect to the admin page or any other page you want
            return redirect('admin')  # Adjust this to the correct URL name for the admin page
        else:
            # If credentials do not match
            return render(request, 'admin_login.html', {'error_message': 'Invalid credentials'})
    return render(request, 'admin_login.html')

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'register.html', {'success_message': 'User created successfully'})
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def admin_page(request):
    return render(request,'admin.html')

def user_page(request):
    return render(request,'user.html')
    

from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from .models import Complaint
import json
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def complaint_form(request):
    username = request.user.username
    if request.method == "POST":
        # Get form data
        company_name = request.POST.get('company_name')
        site_name = request.POST.get('site_name')
        priority = request.POST.get('priority')
        claim_type = request.POST.get('claim_type')
        nature_of_complaint = request.POST.get('nature_of_complaint')
        location = request.POST.get('location')
        equipment = request.POST.get('equipment', '').strip()
        complaint_raised_by = request.POST.get('complaint_raised_by', '').strip()
        images = request.FILES.getlist('images')
        start_date = request.POST.get('start_date')
        pdf_file = request.FILES.get('pdf_upload')

        complaint = Complaint(
            company_name=company_name,
            site_name=site_name,
            priority=priority,
            claim_type=claim_type,
            nature_of_complaint=nature_of_complaint,
            location=location,
            start_date=start_date,
            equipment=equipment,
            complaint_raised_by=complaint_raised_by,
            dup_username = username
        )
        complaint.save()

        # Handle image uploads (same as before)
        image_urls = []
        for image in images:
            if image.size > 1024 * 1024:
                continue
            if not image.name.endswith('.jpeg') and not image.name.endswith('.jpg'):
                continue

            fs = FileSystemStorage()
            filename = fs.save(f'images/{image.name}', image)
            image_url = fs.url(filename)
            image_urls.append(image_url)

        complaint.images = json.dumps(image_urls[:2])
        complaint.save()

        # Handle PDF upload
        if pdf_file:
            if pdf_file.size <= 3 * 1024 * 1024:  # Limit to 3MB
                fs = FileSystemStorage()
                pdf_filename = fs.save(f'pdfs/{pdf_file.name}', pdf_file)
                complaint.pdf_upload = pdf_filename  # Save the PDF file path
                complaint.save()

        return JsonResponse({
            'success': True,
            'data': {
                'company_name': company_name,
                'site_name': site_name,
                'priority': priority,
                'claim_type': claim_type,
                'nature_of_complaint': nature_of_complaint,
                'location': location,
                'equipment': equipment,
                'complaint_raised_by': complaint_raised_by,
                'start_date': start_date,
                'images': image_urls[:2],
                'pdf_upload': complaint.pdf_upload.url if complaint.pdf_upload else None  # Return PDF URL if exists
            }
        })
    return render(request, 'new_complaint.html', {})


def approval_complaints(request):
    complaints_list = Complaint.objects.filter(status='Pending').order_by('-created_at')
    paginator = Paginator(complaints_list, 3)  # Show 3 complaints per page
    page_number = request.GET.get('page')
    complaints = paginator.get_page(page_number)
    return render(request, 'approval_complaints.html', {'complaints': complaints})

def accept_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == 'POST':
        remarks = request.POST.get('remarks')
        #print(remarks)
        complaint.remarks = remarks
    complaint.status = 'Accepted'
    complaint.save()
    complaints = Complaint.objects.filter(status='Pending')
    return render(request,'approval_complaints.html', {'complaints': complaints})

def existing_complaints(request):
    username = request.user.username
    complaints_list = Complaint.objects.filter(status='Accepted', dup_username=username).order_by('-created_at')
    paginator = Paginator(complaints_list, 3)
    page_number = request.GET.get('page')
    complaints = paginator.get_page(page_number)
    return render(request, 'existing_complaints.html', {'complaints': complaints})

def edit_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == "POST":
        
        attended_by = request.POST.get('attended_by')
        end_date = request.POST.get('end_date')
        claim_type = request.POST.get('claim_type')  # Get the claim type from the form
        summary_of_action_taken = request.POST.get('summary_of_action_taken')
        root_cause = request.POST.get('root_cause')
        preventive_action = request.POST.get('preventive_action')
        parts_replaced_for_rectification = request.POST.get('parts_replaced_for_rectification')
        nature_of_complaint = request.POST.get('nature_of_complaint') 

        # Update complaint fields
        complaint.attended_by = attended_by
        complaint.end_date = end_date  # Update the end date
        complaint.claim_type = claim_type  # Update the claim type
        complaint.summary_of_action_taken = summary_of_action_taken
        complaint.root_cause = root_cause
        complaint.preventive_action = preventive_action
        complaint.parts_replaced_for_rectification = parts_replaced_for_rectification
        complaint.nature_of_complaint = nature_of_complaint

        # Validate end date
        if end_date:
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            if end_date < complaint.start_date:
                return render(request, 'edit_complaint.html', {
                    'complaint': complaint,
                    'error': 'End date cannot be before start date.',
                    'attended_by': attended_by,
                    'end_date': end_date,  # Show the entered end_date
                    'claim_type': claim_type,
                    'summary_of_action_taken': summary_of_action_taken,
                    'root_cause': root_cause,
                    'preventive_action': preventive_action,
                    'parts_replaced_for_rectification':parts_replaced_for_rectification,
                    'nature_of_complaint': nature_of_complaint 
                })
        complaint.status = 'Update'
        complaint.save()
        return redirect('existing_complaints')
    return render(request, 'edit_complaint.html', {'complaint': complaint})

def final_complaints(request):
    accepted_complaints = Complaint.objects.filter(status='Update').order_by('-created_at')
    return render(request, 'final_complaints.html', {
        'accepted_complaints': accepted_complaints#,
    })

def final_complaints_user(request):
    username = request.user.username
    accepted_usercomplaints = Complaint.objects.filter(status='Update', dup_username=username).order_by('-created_at')
    return render(request, 'final_complaints_user.html', {
        'accepted_usercomplaints': accepted_usercomplaints
    })

# def delete_complaint(request, complaint_id):
#     if request.method == "POST":
#         # Get the complaint object and delete it
#         complaint = get_object_or_404(Complaint, id=complaint_id)
#         complaint.delete()
#     # Redirect back to the final_complaints page after deletion
#     return redirect('final_complaints')

from django.shortcuts import get_object_or_404, redirect
from django.core.files.storage import default_storage
import json
import os

def delete_complaint(request, complaint_id):
    if request.method == "POST":
        # Get the complaint object
        complaint = get_object_or_404(Complaint, id=complaint_id)

        # Delete images if they exist
        if complaint.images:
            image_list = json.loads(complaint.images)
            for image_url in image_list:
                # Extract the path from the URL
                image_path = image_url.replace('/media/', '')  # Adjust this based on your media URL settings
                # Use Django's default storage to delete the file
                if default_storage.exists(image_path):
                    default_storage.delete(image_path)

        # Delete the PDF file if it exists
        if complaint.pdf_upload:
            complaint.pdf_upload.delete(save=False)

        # Delete the complaint instance
        complaint.delete()

        # Redirect back to the final_complaints page after deletion
        return redirect('final_complaints')



from django.db.models import Count
from django.db.models.functions import ExtractYear

def complaint_analysis(request):
    site_name = request.GET.get('site_name', 'All')  # Get the selected site name from query parameters

    if site_name == 'All':
        open_complaints = Complaint.objects.filter(status__in=['Accepted', 'Pending'])
        closed_complaints = Complaint.objects.filter(status='Update')
    else:
        open_complaints = Complaint.objects.filter(status__in=['Accepted', 'Pending'], site_name=site_name)
        closed_complaints = Complaint.objects.filter(status='Update', site_name=site_name)

    # Aggregate by year for open complaints
    open_complaints_per_year = open_complaints.annotate(year=ExtractYear('start_date')) \
                                              .values('year') \
                                              .annotate(count=Count('id')) \
                                              .order_by('year')
    
    # Aggregate by year for closed complaints
    closed_complaints_per_year = closed_complaints.annotate(year=ExtractYear('start_date')) \
                                                  .values('year') \
                                                  .annotate(count=Count('id')) \
                                                  .order_by('year')

    # Prepare data for charts
    years_open = [str(item['year']) for item in open_complaints_per_year]
    counts_open = [item['count'] for item in open_complaints_per_year]
    
    years_closed = [str(item['year']) for item in closed_complaints_per_year]
    counts_closed = [item['count'] for item in closed_complaints_per_year]

    # Merge years to ensure both open and closed data cover all years
    all_years = sorted(set(years_open) | set(years_closed))

    # Ensure counts are aligned with years
    open_counts_dict = dict(zip(years_open, counts_open))
    closed_counts_dict = dict(zip(years_closed, counts_closed))
    
    open_counts = [open_counts_dict.get(year, 0) for year in all_years]
    closed_counts = [closed_counts_dict.get(year, 0) for year in all_years]

    # Total counts for pie chart
    total_open = open_complaints.count()
    total_closed = closed_complaints.count()

    return render(request, 'complaint_analysis.html', {
        'years_json': json.dumps(all_years),
        'open_counts_json': json.dumps(open_counts),
        'closed_counts_json': json.dumps(closed_counts),
        'total_open': total_open,
        'total_closed': total_closed,
        'selected_site': site_name,
        'sites': Complaint.objects.values_list('site_name', flat=True).distinct()
    })

def ComplaintDetailView(request, type, site_name):
    # Determine complaint status based on the type
    if type == 'open':
        complaints = Complaint.objects.filter(status__in=['Accepted', 'Pending'])
    elif type == 'closed':
        complaints = Complaint.objects.filter(status='Update')
    
    # Filter by site name if not 'All'
    if site_name != 'All':
        complaints = complaints.filter(site_name=site_name)

    return render(request, 'complaint_detail.html', {
        'complaints': complaints,
        'complaint_type': type,  # Pass the complaint type (open or closed)
    })
