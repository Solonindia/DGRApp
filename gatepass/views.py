from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import VisitorLog
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
from django.core.files.storage import default_storage
from reportlab.lib.colors import navy
from django.utils import timezone
from django.http import JsonResponse

def visitor_log_view(request):
    gatepass_id = None  # Initialize gatepass_id as None

    if request.method == 'POST':
        try:
            # Get data from the form submission
            name_of_plant = request.POST.get('name_of_plant')
            visitor_name = request.POST.get('visitor_name')
            visitor_company_name = request.POST.get('visitor_company_name')
            purpose_of_visit = request.POST.get('purpose_of_visit')
            valid_from_datetime_str = request.POST.get('valid_from_datetime')
            valid_to_datetime_str = request.POST.get('valid_to_datetime')
            contact_details = request.POST.get('contact_details')
            emergency_contact_details = request.POST.get('emergency_contact_details')
            emergency_mobile_contact = request.POST.get('emergency_mobile_contact')
            relationship = request.POST.get('relationship')
            gate_pass_issue_datetime_str = request.POST.get('gate_pass_issue_datetime')
            visitor_image = request.FILES.get('visitor_image')

            # Convert datetime strings to datetime objects (ensure the correct format)
            valid_from_datetime = datetime.strptime(valid_from_datetime_str, '%Y-%m-%dT%H:%M')
            valid_to_datetime = datetime.strptime(valid_to_datetime_str, '%Y-%m-%dT%H:%M')
            gate_pass_issue_datetime = datetime.strptime(gate_pass_issue_datetime_str, '%Y-%m-%dT%H:%M')

            # Convert naive datetime to timezone-aware datetime
            valid_from_datetime = timezone.make_aware(valid_from_datetime)
            valid_to_datetime = timezone.make_aware(valid_to_datetime)
            gate_pass_issue_datetime = timezone.make_aware(gate_pass_issue_datetime)

            # Create VisitorLog instance and save it
            visitor_log = VisitorLog.objects.create(
                name_of_plant=name_of_plant,
                visitor_name=visitor_name,
                visitor_company_name=visitor_company_name,
                purpose_of_visit=purpose_of_visit,
                valid_from_datetime=valid_from_datetime,
                valid_to_datetime=valid_to_datetime,
                contact_details=contact_details,
                emergency_contact_details=emergency_contact_details,
                emergency_mobile_contact=emergency_mobile_contact,
                relationship=relationship,
                gate_pass_issue_datetime=gate_pass_issue_datetime,
                visitor_image=visitor_image
            )

            gatepass_id = visitor_log.gatepass_id  # Access generated gatepass_id

            return JsonResponse({
                'success': True,
                'data': {
                    'gatepass_id': gatepass_id
                }
            })
        except Exception as e:
            # Handle any errors, for example if datetime parsing fails or required fields are missing
            return JsonResponse({
                'success': False,
                'message': f"Error: {str(e)}"
            })
    if request.method == "GET":
        gatepass = VisitorLog(name_of_plant="Sample Company") 
        gatepass_id = gatepass.generate_gatepass_id()  # Generate the temporary complaint ID
        return render(request, 'visitor_log.html', {'gatepass_id': gatepass_id})

def visitor_log_list(request):
    visitor_logs = VisitorLog.objects.all().order_by('-gate_pass_issue_datetime')
    return render(request, 'visitor_log_list.html', {'visitor_logs': visitor_logs})

def download_visitor_log_pdf(request, log_id):
    visitor_log = get_object_or_404(VisitorLog, id=log_id)

    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="visitor_gate_pass_{visitor_log.id}.pdf"'

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    margin = 60
    image_width = 80
    image_height = 70
    image_x = width - image_width - margin
    image_y = height - image_height - margin - 30  # Move image down by 30 units

    # Main heading with blue color
    heading_text = "Visitor Gate Pass"
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(navy)  # Set text color to navy
    heading_x = width / 2
    heading_y = height - margin

    # Draw the heading text
    p.drawCentredString(heading_x, heading_y, heading_text)

    # Reset color to default for other text
    p.setFillColor('black')  # Reset text color to black (default)

    # Content area for details
    p.setFont("Helvetica", 12)
    content_x = margin
    content_y = height - margin - 40  # Starting point for the content section

    # Fields to be moved up
    fields = [
        ("Gatepass ID", visitor_log.gatepass_id),
        ("Name of Plant/Project", visitor_log.name_of_plant),
        ("Visitor Organization Name", visitor_log.visitor_company_name),
        ("Purpose of Visit", visitor_log.purpose_of_visit),
        ("Valid From", visitor_log.valid_from_datetime.strftime('%Y-%m-%d %H:%M')),
        ("Valid To", visitor_log.valid_to_datetime.strftime('%Y-%m-%d %H:%M')),
        ("Emergency Contact Name", visitor_log.emergency_contact_details),
        ("Emergency Contact Number", visitor_log.emergency_mobile_contact),
        ("Relationship", visitor_log.relationship),
        ("Gate Pass Issue Date and Time", visitor_log.gate_pass_issue_datetime.strftime('%Y-%m-%d %H:%M'))
    ]

    max_label_width = max(p.stringWidth(f"{label}:", "Helvetica-Bold", 12) for label, _ in fields)
    line_height = 18

    # Draw the field labels and values
    for label, value in fields:
        # Set label to bold
        p.setFont("Helvetica-Bold", 12)
        p.drawString(content_x, content_y, f"{label}:")
        
        # Set value to normal
        p.setFont("Helvetica", 12)
        p.drawString(content_x + max_label_width + 10, content_y, value)
        
        content_y -= line_height

    # Position for image and visitor details
    if visitor_log.visitor_image:
        img_url = visitor_log.visitor_image.url  # Use URL instead of path
        p.drawImage(img_url, image_x, image_y, width=image_width, height=image_height)

        # Position for visitor name below the image
        visitor_name_y = image_y - 20  # Adjust this value to position the name as needed

        # Set visitor name below the image
        p.setFont("Helvetica", 12)
        p.drawString(image_x, visitor_name_y, visitor_log.visitor_name)
        p.drawString(image_x, visitor_name_y - 15, visitor_log.contact_details)

    p.showPage()
    p.save()
    buffer.seek(0)
    response.write(buffer.getvalue())
    buffer.close()
    return response

def delete_visitor_log(request, log_id):
    if request.method == "POST":
        log = get_object_or_404(VisitorLog, id=log_id)
        log.delete()
        messages.success(request, 'Visitor log deleted successfully.')
    return redirect('visitor_log_list')

def visitor_log_user_view(request):
    username = request.user.username  # Get the username from the request
    gatepass_id = None  # Initialize gatepass_id as None

    if request.method == 'POST':
        try:
            # Get data from the form submission
            name_of_plant = request.POST.get('name_of_plant')
            visitor_name = request.POST.get('visitor_name')
            visitor_company_name = request.POST.get('visitor_company_name')
            purpose_of_visit = request.POST.get('purpose_of_visit')
            valid_from_datetime_str = request.POST.get('valid_from_datetime')
            valid_to_datetime_str = request.POST.get('valid_to_datetime')
            contact_details = request.POST.get('contact_details')
            emergency_contact_details = request.POST.get('emergency_contact_details')
            emergency_mobile_contact = request.POST.get('emergency_mobile_contact')
            relationship = request.POST.get('relationship')
            gate_pass_issue_datetime_str = request.POST.get('gate_pass_issue_datetime')
            visitor_image = request.FILES.get('visitor_image')

            # Convert datetime strings to datetime objects (ensure the correct format)
            valid_from_datetime = datetime.strptime(valid_from_datetime_str, '%Y-%m-%dT%H:%M')
            valid_to_datetime = datetime.strptime(valid_to_datetime_str, '%Y-%m-%dT%H:%M')
            gate_pass_issue_datetime = datetime.strptime(gate_pass_issue_datetime_str, '%Y-%m-%dT%H:%M')

            # Convert naive datetime to timezone-aware datetime
            valid_from_datetime = timezone.make_aware(valid_from_datetime)
            valid_to_datetime = timezone.make_aware(valid_to_datetime)
            gate_pass_issue_datetime = timezone.make_aware(gate_pass_issue_datetime)

            # Create VisitorLog instance and save it
            visitor_log = VisitorLog.objects.create(
                name_of_plant=name_of_plant,
                visitor_name=visitor_name,
                visitor_company_name=visitor_company_name,
                purpose_of_visit=purpose_of_visit,
                valid_from_datetime=valid_from_datetime,
                valid_to_datetime=valid_to_datetime,
                contact_details=contact_details,
                emergency_contact_details=emergency_contact_details,
                emergency_mobile_contact=emergency_mobile_contact,
                relationship=relationship,
                gate_pass_issue_datetime=gate_pass_issue_datetime,
                visitor_image=visitor_image,
                dup_username=username  # Pass the username as dup_username here
            )

            gatepass_id = visitor_log.pk  # Access the generated gatepass_id (using the primary key)

            return JsonResponse({
                'success': True,
                'data': {
                    'gatepass_id': gatepass_id
                }
            })
        except Exception as e:
            # Handle any errors, for example if datetime parsing fails or required fields are missing
            return JsonResponse({
                'success': False,
                'message': f"Error: {str(e)}"
            })
    
    elif request.method == "GET":
        gatepass = VisitorLog(name_of_plant="Sample Company") 
        gatepass_id = gatepass.generate_gatepass_id()  # Generate the temporary complaint ID
        return render(request, 'visitor_log.html', {'gatepass_id': gatepass_id})

        
def visitor_log_list_user(request):
    username = request.user.username
    print(username)
    visitor_logs = VisitorLog.objects.filter(dup_username=username).order_by('-gate_pass_issue_datetime')
    return render(request, 'visitor_log_list_user.html', {'visitor_logs': visitor_logs})