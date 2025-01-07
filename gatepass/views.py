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
    # Get the 'gatepass_id' parameter from the GET request
    gatepass_id = request.GET.get('gatepass_id', None)
    
    if gatepass_id:
        # Filter by Gatepass ID if a search query is provided
        visitor_logs = VisitorLog.objects.filter(gatepass_id__icontains=gatepass_id).order_by('-gate_pass_issue_datetime')
    else:
        # If no search query, show all logs
        visitor_logs = VisitorLog.objects.all().order_by('-gate_pass_issue_datetime')
    
    return render(request, 'visitor_log_list.html', {'visitor_logs': visitor_logs})


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import navy
from io import BytesIO
from django.http import HttpResponse


def download_visitor_log_pdf(request, log_id):
    visitor_log = get_object_or_404(VisitorLog, id=log_id)

    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="visitor_gate_pass_{visitor_log.id}.pdf"'

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Adjust margins and spacing
    margin = 60
    line_height = 18
    image_width = 80
    image_height = 70
    image_x = width - image_width - margin
    image_y = height - image_height - margin - 30  # Move image down by 30 units
    content_x = margin
    content_y = height - margin - 40  # Starting point for content

    # Define main heading with blue color
    heading_text = "Visitor Gate Pass"
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(navy)  # Set heading color
    heading_x = width / 2
    heading_y = height - margin
    p.drawCentredString(heading_x, heading_y, heading_text)

    # Reset color for body text
    p.setFillColor('black')

    # Fields to be displayed on the PDF
    fields = [
        ("Gatepass ID", visitor_log.gatepass_id),
        ("Name of Plant/Project", visitor_log.name_of_plant),
        ("Visitor Organization Name", visitor_log.visitor_company_name),
        ("Valid From", visitor_log.valid_from_datetime.strftime('%Y-%m-%d %H:%M')),
        ("Valid To", visitor_log.valid_to_datetime.strftime('%Y-%m-%d %H:%M')),
        ("Emergency Contact Name", visitor_log.emergency_contact_details),
        ("Emergency Contact Number", visitor_log.emergency_mobile_contact),
        ("Relationship", visitor_log.relationship),
        ("Purpose of Visit", visitor_log.purpose_of_visit),
        ("Gate Pass Issue Date and Time", visitor_log.gate_pass_issue_datetime.strftime('%Y-%m-%d %H:%M'))
    ]

    max_label_width = max(p.stringWidth(f"{label}:", "Helvetica-Bold", 12) for label, _ in fields)

    # Function to wrap text within the page width
    def wrap_text(text, max_width, font="Helvetica", font_size=12):
        text_object = p.beginText(content_x + max_label_width + 10, content_y)
        text_object.setFont(font, font_size)
        text_object.setTextOrigin(content_x + max_label_width + 10, content_y)
        lines = []

        # Word wrapping logic
        words = text.split(" ")
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if p.stringWidth(test_line, font, font_size) < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        # Append any leftover text
        if current_line:
            lines.append(current_line)

        return lines

    # Loop to draw fields and their corresponding values on the PDF
    for label, value in fields:
        # Draw the field label in bold
        p.setFont("Helvetica-Bold", 12)
        p.drawString(content_x, content_y, f"{label}:")
        
        # Set font to normal for field values
        p.setFont("Helvetica", 12)

        # Wrap text for the value
        wrapped_text = wrap_text(value, width - margin * 2 - max_label_width - 10)

        # Draw the wrapped text for the field value
        for line in wrapped_text:
            p.drawString(content_x + max_label_width + 10, content_y, line)
            content_y -= line_height  # Move down for the next line

        # **Do not add extra space after each field, only adjust once for the wrapped lines**
        # No extra space added, only decremented for wrapped lines
        # Move to the next field

        # Check if we need to create a new page
        if content_y < margin:
            p.showPage()  # Create a new page
            content_y = height - margin  # Reset content position for the new page

    # If a visitor image exists, display it
    if visitor_log.visitor_image:
        img_url = visitor_log.visitor_image.url  # Use URL to load image
        p.drawImage(img_url, image_x, image_y, width=image_width, height=image_height)

        # Adjust visitor's name and contact details below the image
        visitor_name = visitor_log.visitor_name
        
        # Split visitor name by commas and wrap each part separately
        visitor_name_parts = visitor_name.split(',')
        wrapped_name = []
        
        for part in visitor_name_parts:
            wrapped_name.extend(wrap_text(part.strip(), width - margin * 2 - image_width - 10))

        # Start position for visitor's name
        visitor_name_y = image_y - 20

        p.setFont("Helvetica", 12)

        # Draw wrapped visitor's name
        for line in wrapped_name:
            # Check if the name fits in the remaining space
            if visitor_name_y - line_height < margin:
                p.showPage()  # Move to next page if space is insufficient
                visitor_name_y = height - margin  # Reset Y-position for new page
            p.drawString(image_x, visitor_name_y, line)
            visitor_name_y -= line_height

        # Draw visitor contact details (make sure this doesn't overlap)
        contact_details = visitor_log.contact_details
        wrapped_contact = wrap_text(contact_details, width - margin * 2 - image_width - 10)

        # Draw wrapped contact details below the name
        for line in wrapped_contact:
            # Check if the contact details fit in the remaining space
            if visitor_name_y - line_height < margin:
                p.showPage()  # Move to next page if space is insufficient
                visitor_name_y = height - margin  # Reset Y-position for new page
            p.drawString(image_x, visitor_name_y, line)
            visitor_name_y -= line_height

    # Finalize and return the PDF response
    p.save()

    buffer.seek(0)
    response.write(buffer.read())
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
        return render(request, 'visitor_log_user.html', {'gatepass_id': gatepass_id})

def visitor_log_list_user(request):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        # If the user is not authenticated, redirect them to the login page or show an error message
        return redirect('login')  # You can replace 'login' with the actual name of your login URL

    username = request.user.username
    print(f"Fetching visitor logs for: {username}")

    # Filter visitor logs for the specific user (dup_username = username)
    visitor_logs = VisitorLog.objects.filter(dup_username=username).order_by('-gate_pass_issue_datetime')

    # Check if there are no visitor logs for the user
    if not visitor_logs.exists():
        print("No visitor logs found for this user.")
    
    # Pass the filtered visitor logs to the template
    return render(request, 'visitor_log_list_user.html', {'visitor_logs': visitor_logs})