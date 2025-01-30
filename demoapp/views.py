from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from .forms import CustomUserCreationForm  
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from Inventory.models import Site

def home_page(request):
    return render(request, 'home_page.html')

def redirect_to_home(request):
    return redirect('home')

def user_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('user')  
        else:
            return render(request, 'user_login.html', {'error_message': 'Invalid credentials'})
    return render(request, 'user_login.html')


def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin')  
        else:
            return render(request, 'admin_login.html', {'error_message': 'Invalid credentials'})

    return render(request, 'admin_login.html')

@login_required(login_url='/superuser/login/')  # Ensure only logged-in users can access this view
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'register.html', {'success_message': 'User created successfully'})
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required(login_url='/superuser/login/') 
def admin_page(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: You do not have admin privileges.")
    
    return render(request, 'admin.html')

@login_required(login_url='/user/login/')  # Redirect to login if not logged in
def user_page(request):
    # Restrict access to superusers
    if request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: This page is for users only.")
    
    # Retrieve sites linked to the user's inventory
    sites = Site.objects.filter(inventory__user=request.user).distinct()
    
    # Get the first site's name or set to None if no sites exist
    site_name = sites.first().name if sites.exists() else None
    
    # Render the user page with site information
    return render(request, 'user.html', {'sites': sites, 'site_name': site_name})
    
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from .models import Complaint
from django.utils import timezone
from django.core.paginator import Paginator
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

import logging

logger = logging.getLogger(__name__)

@login_required(login_url='/user/login/')
def complaint_form(request):
    if not request.user.is_authenticated:
        logger.info("User is not authenticated")
        return redirect('/user/login/')
    
    logger.info(f"Authenticated user: {request.user.username}")
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

    elif request.method == "GET":
        # Generate temporary complaint ID for GET requests
        complaint = Complaint(company_name="Sample Company")  # Default instance
        complaint_id = complaint.generate_complaint_id()

        # Render the form for logged-in users only
        return render(request, 'new_complaint.html', {'complaint_id': complaint_id})
    
@login_required(login_url='/superuser/login/') 
def approval_complaints(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: You do not have admin privileges.")
    complaints_list = Complaint.objects.filter(status='Pending').order_by('-created_at')
    return render(request, 'approval_complaints.html', {'complaints': complaints_list})

# @login_required(login_url='/superuser/login/')
# def accept_complaint(request, complaint_id):
#     if not request.user.is_superuser:
#         return HttpResponseForbidden("Access Denied: You do not have admin privileges.")

#     complaint = get_object_or_404(Complaint, id=complaint_id)

#     if request.method == 'POST':
#         remarks = request.POST.get('remarks')
#         if remarks:
#             complaint.remarks = remarks  # Update remarks if provided

#         # Update complaint status to 'Accepted'
#         complaint.status = 'Accepted'
#         complaint.save()

#         # Redirect to the approval complaints page to show updated list
#         return redirect('approval_complaints')  # Replace 'approval_complaints' with your URL name if different

#     # If the request is not POST, redirect back to the complaints page
#     return redirect('approval_complaints')




@login_required(login_url='/superuser/login/')
def accept_complaint(request, complaint_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: You do not have admin privileges.")

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == 'POST':
        remarks = request.POST.get('remarks')  # Get the remarks entered in the form
        action = request.POST.get('action')  # Get the action (approve or reject)

        if remarks:
            complaint.remarks = remarks  # Update remarks if provided

        # Handle the action
        if action == 'approve':
            complaint.status = 'Accepted'  # Update status to Accepted
            complaint.save()
            return redirect('approval_complaints')  # Redirect to approval complaints page

        elif action == 'reject':
            complaint.status = 'Rejected'  # Update status to Rejected
            complaint.save()
            return redirect('approval_complaints')  # Redirect to rejected complaints page

    # If not POST, redirect back to the complaints page
    return redirect('approval_complaints')




@login_required(login_url='/user/login/')
def rejected_complaints(request):
    username = request.user.username
    complaints_list = Complaint.objects.filter(status='Rejected', dup_username=username).order_by('-created_at')
    complaints = complaints_list
    return render(request, 'rejected_complaints.html', {'complaints': complaints})



from django.core.files.storage import default_storage
@login_required(login_url='/user/login/')
def delete_user_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Check if the current user is the one who created the complaint (or any other permissions)
    if complaint.dup_username == request.user.username:
        
        # Delete images if they exist
        if complaint.images:
            try:
                image_list = json.loads(complaint.images)
                for image_url in image_list:
                    image_path = image_url.replace('/media/', '')  # Adjust this based on your media URL settings
                    if default_storage.exists(image_path):
                        default_storage.delete(image_path)
            except json.JSONDecodeError:
                pass  # Handle cases where the images field isn't a valid JSON
        
        # Delete the PDF file if it exists
        if complaint.pdf_file:
            complaint.pdf_file.delete(save=False)

        # Delete the complaint instance from the database
        complaint.delete()

    # Redirect back to the complaints list after deletion 
    return redirect('rejected_complaints')  # Update with the correct URL name if necessary






@login_required(login_url='/user/login/')
def existing_complaints(request):
    username = request.user.username
    complaints_list = Complaint.objects.filter(status='Accepted', dup_username=username).order_by('-created_at')
    complaints = complaints_list
    return render(request, 'existing_complaints.html', {'complaints': complaints})

@login_required(login_url='/user/login/')
def edit_complaint(request, complaint_id):
    # Fetch the complaint, ensuring it belongs to the logged-in user
    complaint = get_object_or_404(Complaint, id=complaint_id, dup_username=request.user.username)

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
        pdf_file = request.FILES.get('pdf_file')

        if pdf_file:
            # Save the PDF to the complaint's pdf_upload field
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

@login_required(login_url='/superuser/login/')  # Ensure only logged-in users can access this view
def final_complaints(request):
    # Ensure only superusers can access this page
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: You do not have admin privileges.")
    
    # Fetch complaints with 'Update' status, ordered by creation date (latest first)
    accepted_complaints = Complaint.objects.filter(status='Update').order_by('-created_at')
    return render(request, 'final_complaints.html', {'accepted_complaints': accepted_complaints})

@login_required(login_url='/user/login')
def final_complaints_user(request):
    username = request.user.username
    # Filter complaints that have 'Update' status and belong to the logged-in user
    accepted_usercomplaints = Complaint.objects.filter(status='Update', dup_username=username).order_by('-created_at')
    
    return render(request, 'final_complaints_user.html', {
        'accepted_usercomplaints': accepted_usercomplaints
    })


from django.shortcuts import get_object_or_404, redirect
from django.core.files.storage import default_storage
import json
import os
@login_required(login_url='/superuser/login/')  # Ensure only logged-in users can access this view
def delete_complaint(request, complaint_id):
    # Ensure only superusers can perform this action
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: You do not have admin privileges.")
    
    if request.method == "POST":
        # Fetch the complaint object or return 404 if not found
        complaint = get_object_or_404(Complaint, id=complaint_id)

        # Delete images if they exist
        if complaint.images:
            try:
                image_list = json.loads(complaint.images)
                for image_url in image_list:
                    # Extract the path from the URL
                    image_path = image_url.replace('/media/', '')  # Adjust this based on your media URL settings
                    # Delete the file using Django's storage
                    if default_storage.exists(image_path):
                        default_storage.delete(image_path)
            except json.JSONDecodeError:
                # Handle invalid JSON format in the images field
                pass

        # Delete the PDF file if it exists
        if complaint.pdf_file:
            complaint.pdf_file.delete(save=False)

        # Delete the complaint instance from the database
        complaint.delete()

        # Redirect back to the final_complaints page after deletion
        return redirect('final_complaints')  # Replace 'final_complaints' with your URL name if different

    # Redirect to final_complaints if the request method is not POST
    return redirect('final_complaints')

from django.db.models import Count
from django.db.models.functions import ExtractYear

@login_required(login_url='/superuser/login/') 
def complaint_analysis(request):
    site_name = request.GET.get('site_name', 'All')  # Get the selected site name from query parameters

    if site_name == 'All':
        open_complaints = Complaint.objects.filter(status__in=['Accepted', 'Pending'])
        closed_complaints = Complaint.objects.filter(status='Update')
    else:
        open_complaints = Complaint.objects.filter(status__in=['Accepted', 'Pending'], site_name=site_name)
        closed_complaints = Complaint.objects.filter(status='Update', site_name=site_name)

    # Aggregate by year for open complaints
    open_complaints_per_year = (
        open_complaints.annotate(year=ExtractYear('start_date'))
        .values('year')
        .annotate(count=Count('id'))
        .order_by('year')
    )

    # Aggregate by year for closed complaints
    closed_complaints_per_year = (
        closed_complaints.annotate(year=ExtractYear('start_date'))
        .values('year')
        .annotate(count=Count('id'))
        .order_by('year')
    )

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

@login_required(login_url='/superuser/login/') 
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

@login_required(login_url='/superuser/login/') 
def export_complaints_to_csv(request, type, site_name):
    # Fetch complaints based on type
    if type == 'open':
        complaints = Complaint.objects.filter(status__in=['Accepted', 'Pending'])
    elif type == 'closed':
        complaints = Complaint.objects.filter(status='Update')
    else:
        complaints = Complaint.objects.none()

    # Filter by site name if not 'All'
    if site_name != 'All':
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

from django.contrib.auth import views as auth_views

class CustomLogoutView(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "Logout successful")
        return super().dispatch(request, *args, **kwargs)
