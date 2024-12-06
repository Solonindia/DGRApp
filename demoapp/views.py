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
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from azure.storage.blob import BlobServiceClient
import json
from azure.storage.blob import BlobServiceClient
from django.http import JsonResponse
from django.shortcuts import render
import os
from azure.storage.blob import BlobServiceClient
import logging

def fix_base64_padding(key):
    """Ensure the base64 account key has the correct padding."""
    if key is None:
        raise ValueError("Account key must not be None.")
    return key + '=' * (4 - len(key) % 4) if len(key) % 4 != 0 else key

# Get the Azure Storage account key
account_key = os.getenv('AZURE_ACCOUNT_KEY')

# Log if the account key is not set
if account_key is None:
    logging.error("AZURE_ACCOUNT_KEY environment variable is not set.")
    raise ValueError("AZURE_ACCOUNT_KEY environment variable must be set.")

# Fix padding on the account key
fixed_account_key = fix_base64_padding(account_key)

# Retrieve the container name from environment variables
container_name = os.getenv('AZURE_CONTAINER')
if not container_name:
    logging.error("AZURE_CONTAINER environment variable is not set.")
    raise ValueError("AZURE_CONTAINER environment variable must be set.")

# Set up the connection string
connection_string = (
    f"DefaultEndpointsProtocol=https;"
    f"AccountName=filescomplaints;"
    f"AccountKey={fixed_account_key};"
    f"EndpointSuffix=core.windows.net"
)

# Initialize BlobServiceClient
try:
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    logging.info("BlobServiceClient initialized successfully.")

    # Check if the container exists
    container_client = blob_service_client.get_container_client(container_name)
    try:
        container_client.get_container_properties()
        logging.info(f"Container '{container_name}' exists.")
    except Exception as e:
        logging.error(f"Container '{container_name}' does not exist or cannot be accessed: {e}")
        raise
except Exception as e:
    logging.error(f"Failed to initialize BlobServiceClient: {e}")
    raise

import os
import json
from django.conf import settings
from azure.storage.blob import BlobServiceClient

def upload_to_azure(blob_service_client, container_name, file_path, file_content):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_path)
    blob_client.upload_blob(file_content, overwrite=True)
    return blob_client.url

def complaint_form(request):
    username = request.user.username

    if request.method == "POST":
        # Handle the POST request: form submission
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

        # Create and save the complaint instance
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
            dup_username=username
        )
        complaint.save()

        # Initialize Azure Blob Service Client
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_name = settings.AZURE_CONTAINER

        # Handle image uploads
        image_urls = []
        if images:
            for image in images[:2]:  # Limit to first two images
                image_name = f"{username}_{image.name}"
                blob_path = f"images/{image_name}"
                image_url = upload_to_azure(blob_service_client, container_name, blob_path, image)
                image_urls.append(image_url)

        # Save image URLs in the complaint instance
        complaint.images = json.dumps(image_urls)
        complaint.save()

        # Return success response
        return JsonResponse({
            'success': True,
            'data': {
                'complaint_id': complaint.complaint_id,
                'company_name': company_name,
                'site_name': site_name,
                'priority': priority,
                'claim_type': claim_type,
                'nature_of_complaint': nature_of_complaint,
                'location': location,
                'equipment': equipment,
                'complaint_raised_by': complaint_raised_by,
                'start_date': start_date,
                'images': image_urls,
            }
        })

    if request.method == "GET":
        # Generate temporary complaint ID for GET requests
        complaint = Complaint(company_name="Sample Company")  # Default instance
        complaint_id = complaint.generate_complaint_id()
        return render(request, 'new_complaint.html', {'complaint_id': complaint_id})



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
        # Extract form data
        attended_by = request.POST.get('attended_by')
        end_date = request.POST.get('end_date')
        claim_type = request.POST.get('claim_type')
        summary_of_action_taken = request.POST.get('summary_of_action_taken')
        root_cause = request.POST.get('root_cause')
        preventive_action = request.POST.get('preventive_action')
        parts_replaced_for_rectification = request.POST.get('parts_replaced_for_rectification')
        nature_of_complaint = request.POST.get('nature_of_complaint')

        # Handle PDF file upload (save to Azure Storage via Django Storages)
        pdf_file = request.FILES.get('pdf_file')  # Get the uploaded PDF file (match the model field name)

        if pdf_file:
            # Save the PDF to the complaint's pdf_upload field (match the model field name)
            complaint.pdf_file = pdf_file  # This will automatically use the Azure storage backend
            print(f"PDF file {pdf_file.name} uploaded successfully to Azure.")
        
        # Update other fields
        complaint.attended_by = attended_by
        complaint.end_date = end_date
        complaint.claim_type = claim_type
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
                    'end_date': end_date,
                    'claim_type': claim_type,
                    'summary_of_action_taken': summary_of_action_taken,
                    'root_cause': root_cause,
                    'preventive_action': preventive_action,
                    'parts_replaced_for_rectification': parts_replaced_for_rectification,
                    'nature_of_complaint': nature_of_complaint
                })

        # Save the updated complaint
        complaint.status = 'Update'
        complaint.save()

        # Redirect to complaints page after successful update
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
        if complaint.pdf_file:
            complaint.pdf_file.delete(save=False)

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

import csv
from django.http import HttpResponse
from .models import Complaint

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

def export_complaints_to_csv(request, type, site_name):
    # Check for 'All' and adjust site_name accordingly
    if site_name == 'All':
        site_name = ''  # or handle as required
    
    # Fetch complaints
    if type == 'open':
        complaints = Complaint.objects.filter(status__in=['Accepted', 'Pending'])
    elif type == 'closed':
        complaints = Complaint.objects.filter(status='Update')

    if site_name:
        complaints = complaints.filter(site_name=site_name)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=complaints_data.csv'

    writer = csv.writer(response)

    # Write header row without 'Images' and 'PDFs'
    writer.writerow([
        'Complaint ID', 'Location', 'Equipment', 'Project Owner', 'Site Name',
        'Priority', 'Complaint Raised By', 'Nature of Complaint', 'Complaint Open Date',
        'Summary of Action Taken', 'Root Cause', 'Preventive Action', 'Claim Type',
        'Parts Replaced for Rectification', 'Attended By', 'Complaint Closed Date'
    ])

    # Write complaint data without 'Images' and 'PDFs' columns
    for complaint in complaints:
        row = [
            complaint.complaint_id,
            complaint.location,
            complaint.equipment,
            complaint.company_name,
            complaint.site_name,
            complaint.priority,
            complaint.complaint_raised_by,
            complaint.nature_of_complaint,
            complaint.start_date.strftime("%Y-%m-%d"),
            complaint.summary_of_action_taken if type == 'closed' else '',
            complaint.root_cause if type == 'closed' else '',
            complaint.preventive_action if type == 'closed' else '',
            complaint.claim_type if type == 'closed' else '',
            complaint.parts_replaced_for_rectification if type == 'closed' else '',
            complaint.attended_by if type == 'closed' else '',
            complaint.end_date.strftime("%Y-%m-%d") if type == 'closed' else ''
        ]
        writer.writerow(row)

    return response