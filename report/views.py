from django.shortcuts import render
from django.http import HttpResponse

def my_button_view(request):
    reports = [
        "Module Mounting Structure (MMS)", "Solar PV (SPV)", "String Cable", "String Monitoring Box (SMB)",
        "Module Cleaning System (MCS)", "Power/HT Cables AC (ACPC)", "LT Cables AC (LTC)", "Inverter (INV)",
        "Transformer (TRAFO)", "VCB", "HT Panel (HTP)", "LT Panel (LTP)", "UPS", "Battery Charger", "Battery Bank",
        "Street Light", "Lightning Arrester (LA)", "Earthpit (EP)", "Fire & Safety System (FSS)", "Metering Yard",
        "OH Line (OHL)", "Bay Extension (BE)", "House Keeping","Scada Monitoring System"
    ]

    user_type = "admin" if request.user.is_superuser else "user"

    return render(request, 'report.html', {
        'reports': reports,
        'user_type': user_type
    })


short_codes = {
    "Module Mounting Structure (MMS)": "MMS", "Solar PV (SPV)": "SPV", "String Cable": "SC", "String Monitoring Box (SMB)": "SMB", "Module Cleaning System (MCS)": "MCS",
    "Power/HT Cables AC (ACPC)": "ACPC", "LT Cables AC (LTC)": "LTC", "Inverter (INV)": "INV", "Transformer (TRAFO)": "TRAFO", "VCB": "VCB",
    "HT Panel (HTP)": "HTP", "LT Panel (LTP)": "LTP", "UPS": "UPS", "Battery Charger": "BC",
    "Battery Bank": "BB", "Street Light": "SL", "Lightning Arrester (LA)": "LA", "Earthpit (EP)": "EP",
    "Fire & Safety System (FSS)": "FSS", "Metering Yard": "MY", "OH Line (OHL)": "OHL", "Bay Extension (BE)": "BE", "House Keeping": "HK", "Scada Monitoring System":"SMS"
}

from .forms import ChecklistItemForm
from django.contrib import messages

def add_checklist_item_view(request):
    if request.method == 'POST':
        form = ChecklistItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Checklist item added successfully.')
            return redirect('add_checklist_item')  # redirect to same page
    else:
        form = ChecklistItemForm()

    return render(request, 'add_checklist_item.html', {'form': form})

inspection_period_options = [
    {"name": "Daily", "days": 1},
    {"name": "Weekly", "days": 8},
    {"name": "Monthly", "days": 31},
    {"name": "Quarterly", "days": 92},
    {"name": "Half Yearly", "days": 183},
    {"name": "Annually", "days": 365},
]

from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from .models import ChecklistItem, ChecklistResponse, ChecklistResponseItem
from datetime import date,datetime
from .utils import parse_date_safe  # assuming you have this helper
from django.core.files.base import ContentFile
import base64

def parse_date_safe(date_str):
    try:
        return date.fromisoformat(date_str)
    except (TypeError, ValueError):
        return None


from django.http import HttpResponseForbidden
from django.db import transaction
from django.core.cache import cache


def checklist_form_view(request):
    ip = request.META.get('REMOTE_ADDR', 'unknown')

    report_type = (
        request.GET.get('report_type')
        or request.POST.get('report_type')
        or cache.get(f'report_type_{ip}')
    )

    FREQUENCY_LEVELS = {
        'Daily': 1,
        'Weekly': 2,
        'Monthly': 3,
        'Quarterly': 4,
        'Half Yearly': 5,
        'Annually': 6,
    }

    edit_id = request.GET.get('edit_id') or request.POST.get('edit_id')

    # selected frequency
    selected_freq = (
        request.GET.get('inspection_period')
        or request.POST.get('inspection_period')
        or (
            ChecklistResponse.objects.filter(id=edit_id).values_list('period_of_inspection', flat=True).first()
            if edit_id else None
        )
        or 'Annually'
    )
    selected_level = FREQUENCY_LEVELS.get(selected_freq, 6)

    checklist_items = ChecklistItem.objects.filter(
        report_type=report_type,
        frequency_level__lte=selected_level
    ).order_by('-id')  # latest first

    latest_date = checklist_items.first().Date if checklist_items.exists() else date.today()

    component = short_codes.get(report_type, report_type) or "Component"
    comments = (
        f"1) This is a Generalised Check Sheet for {component}. Some check points may not be applicable to {component} under consideration. "
        f"Please put Not Applicable (NA) in remark column for such points.\n"
        f"2) Please put appropriate remark wherever required.\n"
        f"3) Please also refer to OEM Manual & Manufacturer’s Recommendation (MR) for Inspection, Maintenance & Testing of {component}."
    )

    # -----------------------------
    # POST: preview => save draft
    # -----------------------------
    if request.method == 'POST' and 'preview' in request.POST:
        inspection_date = parse_date_safe(request.POST.get('inspection_date'))
        next_inspection_date = parse_date_safe(request.POST.get('next_inspection_date'))

        with transaction.atomic():
            if edit_id:
                response = get_object_or_404(ChecklistResponse, id=edit_id)

                # 🔒 permission: only admin or owner can edit
                if request.user.is_authenticated and not request.user.is_superuser:
                    if response.created_by_id and response.created_by_id != request.user.id:
                        return HttpResponseForbidden("You are not allowed to edit this report.")
                # if response.created_by is NULL (old data), you can decide policy:
                # here: allow edit but set owner now (below).

                response.project_name = request.POST.get('project_name')
                response.project_location = request.POST.get('project_location')
                response.inspection_date = inspection_date
                response.next_inspection_date = next_inspection_date
                response.period_of_inspection = request.POST.get('inspection_period')
                response.make = request.POST.get('make', '').strip() or 'N/A'
                response.Type = request.POST.get('Type', '').strip() or 'N/A'
                response.s_no = request.POST.get('s_no', '').strip() or 'N/A'
                response.rating = request.POST.get('rating', '').strip() or 'N/A'
                response.comments = comments
                response.email_to = request.POST.get('email_to') or response.email_to
                response.customer_name = request.POST.get('customer_name')
                response.solon_name = request.POST.get('solon_name')
                response.Date = latest_date
                response.is_draft = True

            else:
                response = ChecklistResponse(
                    report_type=report_type,
                    project_name=request.POST.get('project_name'),
                    project_location=request.POST.get('project_location'),
                    inspection_date=inspection_date,
                    next_inspection_date=next_inspection_date,
                    period_of_inspection=request.POST.get('inspection_period'),
                    make=request.POST.get('make', '').strip() or 'N/A',
                    Type=request.POST.get('Type', '').strip() or 'N/A',
                    s_no=request.POST.get('s_no', '').strip() or 'N/A',
                    rating=request.POST.get('rating', '').strip() or 'N/A',
                    comments=comments,
                    email_to=request.POST.get('email_to'),
                    customer_name=request.POST.get('customer_name'),
                    solon_name=request.POST.get('solon_name'),
                    Date=latest_date,
                    is_draft=True,
                )

            # ✅ Set owner (don’t overwrite an existing owner)
            if request.user.is_authenticated and not response.created_by_id:
                response.created_by = request.user

            # --- Images: image1..image6 + captured_image_1..6
            for i in range(1, 7):
                img_field = f'image{i}'
                captured_field = f'captured_image_{i}'

                if img_field in request.FILES:
                    setattr(response, img_field, request.FILES[img_field])

                elif request.POST.get(captured_field):
                    try:
                        fmt, imgstr = request.POST[captured_field].split(';base64,')
                        ext = fmt.split('/')[-1]
                        image_file = ContentFile(
                            base64.b64decode(imgstr),
                            name=f"captured_{response.id or 'new'}_{i}.{ext}"
                        )
                        setattr(response, img_field, image_file)
                    except Exception as e:
                        print(f"Error decoding base64 image for {captured_field}: {e}")

            # --- Signatures
            if 'signature' in request.FILES:
                response.signature = request.FILES['signature']
            if request.POST.get('signature_pad_data'):
                fmt, imgstr = request.POST['signature_pad_data'].split(';base64,')
                ext = fmt.split('/')[-1]
                response.signature.save(
                    f"sign_{response.id or 'new'}.{ext}",
                    ContentFile(base64.b64decode(imgstr)),
                    save=False
                )

            if 'signature1' in request.FILES:
                response.signature1 = request.FILES['signature1']
            if request.POST.get('signature_pad_data1'):
                fmt, imgstr = request.POST['signature_pad_data1'].split(';base64,')
                ext = fmt.split('/')[-1]
                response.signature1.save(
                    f"sign_{response.id or 'new'}_1.{ext}",
                    ContentFile(base64.b64decode(imgstr)),
                    save=False
                )

            # Save once (creates id if new)
            response.save()

            # Replace response items
            ChecklistResponseItem.objects.filter(response=response).delete()

            items_to_create = []
            # NOTE: we ordered checklist_items by -id above. If you need form indexes to match the display,
            # make sure your template loops in same order. Otherwise change order_by('id').
            for idx, item in enumerate(checklist_items, start=1):
                idx_str = str(idx)
                status = request.POST.get(f'status_{idx_str}') or request.POST.get(f'status_select_{idx_str}')
                remark = request.POST.get(f'remark_{idx_str}')
                items_to_create.append(ChecklistResponseItem(
                    response=response,
                    checklist_item=item,
                    status=status or '',
                    remark=remark or ''
                ))

            ChecklistResponseItem.objects.bulk_create(items_to_create)

        email_to = request.POST.get('email_to', '')
        return redirect(f'/service-report/checklist/preview/{response.id}/?email_to={email_to}')

    # -----------------------------
    # GET / edit: load form data
    # -----------------------------
    form_data = {}
    if edit_id:
        response = get_object_or_404(ChecklistResponse, id=edit_id)

        # 🔒 permission (important)
        if request.user.is_authenticated and not request.user.is_superuser:
            if response.created_by_id and response.created_by_id != request.user.id:
                return HttpResponseForbidden("You are not allowed to view/edit this report.")

        form_data = {
            "project_name": response.project_name,
            "project_location": response.project_location,
            "inspection_date": response.inspection_date,
            "next_inspection_date": response.next_inspection_date,
            "inspection_period": response.period_of_inspection,
            "component": component,
            "make": response.make,
            "Type": response.Type,
            "s_no": response.s_no,
            "rating": response.rating,
            "comments": response.comments or comments,
            "Date": latest_date,
            "signature": response.signature.url if response.signature else "",
            "signature1": response.signature1.url if response.signature1 else "",
            "email_to": response.email_to or "",
            "customer_name": response.customer_name,
            "solon_name": response.solon_name,
        }

        # existing statuses/remarks
        existing_items = ChecklistResponseItem.objects.filter(response=response)
        for idx, item in enumerate(checklist_items, start=1):
            idx_str = str(idx)
            item_data = existing_items.filter(checklist_item=item).first()
            if item_data:
                form_data[f'status_{idx_str}'] = item_data.status
                form_data[f'remark_{idx_str}'] = item_data.remark

        for i in range(1, 7):
            img = getattr(response, f"image{i}", None)
            if img:
                form_data[f"image{i}"] = img.url

    return render(request, 'checklist_form.html', {
        'report_type': report_type,
        'format_no': f"SIPL/O&M/{short_codes.get(report_type, report_type)}/37" if report_type else "",
        'component': component,
        'Date': latest_date,
        'form_data': form_data,
        'checklist': checklist_items,
        'edit_id': edit_id or '',
        'inspection_period_options': inspection_period_options,
        'na_fields': ['make', 'Type', 's_no', 'rating'],
        'comments': comments,
        'selected_level': selected_level,
        'frequency_levels': FREQUENCY_LEVELS,
    })


def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    except ValueError:
        return None

from django.shortcuts import render, redirect, get_object_or_404
from .models import ChecklistResponse, ChecklistResponseItem, ChecklistItem, ChecklistHistory
from datetime import date
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.files.base import ContentFile
import uuid
import pdfkit
import base64
 
def checklist_preview_view(request, response_id):
    response = get_object_or_404(ChecklistResponse, id=response_id)
    if not request.user.is_superuser:
        if response.created_by_id != request.user.id:
            return HttpResponseForbidden("Not allowed")
    show_modal = False
    response = get_object_or_404(ChecklistResponse, id=response_id)
    report_type = response.report_type
    FREQUENCY_LEVELS = {
        'Daily': 1,
        'Weekly': 2,
        'Monthly': 3,
        'Quarterly': 4,
        'Half Yearly': 5,
        'Annually': 6,
    }
    selected_freq = response.period_of_inspection or 'Annually'
    selected_level = FREQUENCY_LEVELS.get(selected_freq, 6)
    component = short_codes.get(response.report_type, response.report_type)
    comments = (
        f"1) This is a Generalised Check Sheet for {component}. Some check points may not be applicable to {component} under consideration. "
        f"Please put Not Applicable (NA) in remark column for such points.\n"
        f"2) Please put appropriate remark wherever required.\n"
        f"3) Please also refer to OEM Manual & Manufacturer’s Recommendation (MR) for Inspection, Maintenance & Testing of {component}."
    )

    email_to = request.GET.get('email_to', '')
    checklist_items_master = ChecklistItem.objects.filter(
        report_type=response.report_type,
        frequency_level__lte=selected_level
    )

    # Get the latest date from ChecklistItem
    latest_date = checklist_items_master.order_by('-Date').first().Date if checklist_items_master.exists() else date.today()

    checklist_items = ChecklistResponseItem.objects.filter(response=response, checklist_item__report_type=report_type)
    inspection_period_options = [
        {'name': 'Daily', 'days': 1},
        {'name': 'Weekly', 'days': 8},
        {'name': 'Monthly', 'days': 31},
        {'name': 'Quarterly', 'days': 91},
        {'name': 'Half Yearly', 'days': 183},
        {'name': 'Annually', 'days': 366},
    ]

    if request.method == 'POST':
        if 'edit' in request.POST:
            form_data = {
                'project_name': response.project_name,
                'project_location': response.project_location,
                'inspection_date': response.inspection_date.strftime('%Y-%m-%d') if response.inspection_date else '',
                'next_inspection_date': response.next_inspection_date.strftime('%Y-%m-%d') if response.next_inspection_date else '',
                'inspection_period': response.period_of_inspection,
                'component': component,
                'make': response.make,
                'Type': response.Type,
                's_no': response.s_no,
                'rating': response.rating,
                'Date': latest_date,  # Use the latest date here
                'comments': response.comments or comments,
                'email_to': response.email_to,
                'customer_name': response.customer_name,
                'solon_name': response.solon_name,
            }

            na_fields = ['make', 'Type', 's_no', 'rating']
            for field in na_fields:
                key = field if field != 'Type' else 'type'
                value = getattr(response, field, '')
                if value == 'N/A':
                    form_data[key] = 'N/A'

            for idx, item in enumerate(checklist_items, start=1):
                idx_str = str(idx)
                if item.status in ['YES', 'NO']:
                    form_data[f'status_select_{idx_str}'] = item.status
                    form_data[f'status_{idx_str}'] = ''
                else:
                    form_data[f'status_select_{idx_str}'] = 'CUSTOM'
                    form_data[f'status_{idx_str}'] = item.status
                form_data[f'remark_{idx_str}'] = item.remark

            for i in range(1, 7):
                img_field = f'image{i}'
                img_obj = getattr(response, img_field, None)
                if img_obj:
                    form_data[img_field] = img_obj.url

            if response.signature:
                form_data['signature'] = response.signature.url
            if hasattr(response, 'signature_pad_data') and response.signature_pad_data:
                form_data['signature_pad_data'] = response.signature_pad_data

            if response.signature1:
                form_data['signature1'] = response.signature1.url
            if hasattr(response, 'signature_pad_data1') and response.signature_pad_data1:
                form_data['signature_pad_data1'] = response.signature_pad_data1

            return render(request, 'checklist_form.html', {
                'report_type': response.report_type,
                'format_no': f"SIPL/O&M/{short_codes.get(response.report_type, response.report_type)}/37",
                'component': component,
                'comments': comments,
                'Date': latest_date,  # Use the latest date here
                'form_data': form_data,
                'checklist': checklist_items_master,
                'edit_id': response.id,
                'inspection_period_options': inspection_period_options,
                'na_fields': na_fields
            })

        elif 'preview' in request.POST:
            response.project_name = request.POST.get('project_name')
            response.project_location = request.POST.get('project_location')
            response.make = request.POST.get('make', '').strip() or 'N/A'
            response.Type = request.POST.get('Type', '').strip() or 'N/A'
            response.s_no = request.POST.get('s_no', '').strip() or 'N/A'
            response.rating = request.POST.get('rating', '').strip() or 'N/A'
            response.comments = request.POST.get('comments') or comments
            response.inspection_date = request.POST.get('inspection_date') or None
            response.period_of_inspection = request.POST.get('inspection_period')
            response.next_inspection_date = request.POST.get('next_inspection_date') or None
            response.email_to = request.POST.get('email_to') 
            response.customer_name = request.POST.get('customer_name')
            response.solon_name = request.POST.get('solon_name')

            for i in range(1, 7):
                img_field = f'image{i}'
                file = request.FILES.get(img_field)
                captured_data = request.POST.get(f'captured_image_{i}')

                if file:
                    # 📁 Use uploaded file if available
                    setattr(response, img_field, file)
                elif captured_data and captured_data.startswith('data:image'):
                    # 📷 Use captured image if no file uploaded
                    format, imgstr = captured_data.split(';base64,')
                    ext = format.split('/')[-1]
                    file_name = f"captured_{uuid.uuid4()}.{ext}"
                    file_data = ContentFile(base64.b64decode(imgstr), name=file_name)
                    setattr(response, img_field, file_data)

            # ✍️ Handle drawn signature
            if request.FILES.get('signature'):
                response.signature = request.FILES.get('signature')
            elif request.POST.get('signature_pad_data'):
                sign_data = request.POST['signature_pad_data']
                if sign_data.startswith('data:image'):
                    format, imgstr = sign_data.split(';base64,')
                    ext = format.split('/')[-1]
                    response.signature.save(
                        f"sign_{response.id}.{ext}",
                        ContentFile(base64.b64decode(imgstr)),
                        save=False
                    )
            if request.FILES.get('signature1'):
                response.signature1 = request.FILES.get('signature1')
            elif request.POST.get('signature_pad_data1'):
                sign_data1 = request.POST['signature_pad_data1']
                if sign_data1.startswith('data:image'):
                    format, imgstr = sign_data1.split(';base64,')
                    ext = format.split('/')[-1]
                    response.signature1.save(
                        f"sign_{response.id}.{ext}",
                        ContentFile(base64.b64decode(imgstr)),
                        save=False
                    )

            response.save()

            ChecklistResponseItem.objects.filter(response=response).delete()

            selected_freq = request.POST.get('inspection_period', 'Annually')
            selected_level = FREQUENCY_LEVELS.get(selected_freq, 5)

            # 🔁 Filter checklist items based on this level
            checklist_items_master = ChecklistItem.objects.filter(
                report_type=response.report_type,
                frequency_level__lte=selected_level
            )

            # 🗑️ Clear old items
            ChecklistResponseItem.objects.filter(response=response).delete()

            # 📝 Save new items with status and remark
            for idx, item in enumerate(checklist_items_master, start=1):
                idx_str = str(idx)
                status = request.POST.get(f'status_select_{idx_str}', '')
                if status == 'CUSTOM':
                    status = request.POST.get(f'status_{idx_str}', '')
                remark = request.POST.get(f'remark_{idx_str}', '')
                ChecklistResponseItem.objects.create(
                    response=response,
                    checklist_item=item,
                    status=status,
                    remark=remark
                )
                
            checklist_items = ChecklistResponseItem.objects.filter(response=response)
            return render(request, 'checklist_preview.html', {
                'preview_data': response,
                'checklist': checklist_items, 
                'component': component,
                'report_type': response.report_type,
                'Date': latest_date,
                'preview_mode': True,
                'show_download_button': True,
                'comments': response.comments,
                'format_no': f"SIPL/O&M/{short_codes.get(response.report_type, response.report_type)}/37",
            })
        elif 'final_save' in request.POST:
            # Mark the checklist as final by setting is_draft to False
            response.is_draft = False
            response.save()

            # Display a success message to the user
            messages.success(request, "Checklist saved successfully!")

            # Retrieve the checklist items related to the response
            checklist_items = ChecklistResponseItem.objects.filter(response=response)

            # Build the logo and image URLs to include in the PDF
            logo_url = request.build_absolute_uri(static('logo.png'))
            image_urls = []
            for i in range(1, 7):
                img = getattr(response, f'image{i}', None)
                if img:
                    image_urls.append(request.build_absolute_uri(img.url))

            # Build the signature URLs for the PDF (if they exist)
            signature_url = request.build_absolute_uri(response.signature.url) if response.signature else None
            signature1_url = request.build_absolute_uri(response.signature1.url) if response.signature1 else None

            # Generate the format number (based on report type)
            format_no = f"SIPL/O&M/{short_codes.get(response.report_type, response.report_type)}/37"

            # Prepare the context to pass to the PDF template
            context = {
                'logo_url': logo_url,
                'response': response,
                'Date': latest_date,
                'checklist': checklist_items,
                'component': component,
                'image_urls': image_urls,
                'signature_url': signature_url,
                'signature1_url': signature1_url,
                'format_no': format_no,
                'comments': comments
            }

            # Generate the PDF content using a template
            template = get_template('checklist_pdf_template.html')
            html = template.render(context)
            pdf_file = BytesIO()
            pisa.CreatePDF(html, dest=pdf_file)
            pdf_file.seek(0)

            # Create a new ChecklistHistory object to store the PDF
            history = ChecklistHistory.objects.create(
                checklist=response
            )
            history.pdf_file.save(f'Service Report_{response.project_name}.pdf', ContentFile(pdf_file.read()))

            # Reset the pointer in the PDF file
            pdf_file.seek(0)

            # Retrieve the email address to send the PDF to
            email_to = request.POST.get('email_to') or response.email_to

            # Validate the email address before proceeding
            if not email_to or email_to == 'None':
                messages.error(request, "Email address is missing or invalid.")
                return redirect('checklist_preview', response_id=response.id)

            # Store the email in the database before sending
            response.email_to = email_to
            response.save()

            show_modal = True

            # Send the PDF as an email attachment
            options = {
                'enable-local-file-access': '',
                'page-size': 'A4',
                'encoding': 'UTF-8',
                'enable-local-file-access': '',
                'margin-top': '10mm',
                'margin-bottom': '10mm',
                'margin-left': '10mm',
                'margin-right': '10mm',
                'no-outline': None,
            }

            # Generate the PDF
            pdf_data = BytesIO()

            # Set the file path for the watermark image
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'Images', 'logo.png')

            # Apply watermark to the PDF (this function should be defined elsewhere in your code)
            pdf_file.seek(0)
            final_pdf = BytesIO()
            add_image_watermark_to_pdf(pdf_file, final_pdf, logo_path)

            # Send email
            subject = f'Service Report - {response.project_name}'
            message = (
                "Hi Sir/Madam,\n\n"
                f"Please find attached the Service Report for '{response.report_type}' conducted on {response.inspection_date}.\n\n"
                "Regards,\n"
                "OandM,\n"
                "SOLON India Pvt Ltd"
            )
            email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [email_to])
            email.attach(f'Checklist_{response.project_name}.pdf', final_pdf.getvalue(), 'application/pdf')
            email.send()

    return render(request, 'checklist_preview.html', {
        'preview_data': response,
        'checklist': checklist_items,
        'report_type': response.report_type,
        'Date': latest_date,
        'component': component,
        'preview_mode': True,
        'show_modal': show_modal,
        'format_no': f"SIPL/O&M/{short_codes.get(response.report_type, response.report_type)}/37",
        'email_to': email_to,
        'comments': comments,
    })

from django.http import HttpResponse
from django.contrib.staticfiles import finders
from django.utils.html import strip_tags
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from .models import ChecklistResponse, ChecklistResponseItem
from django.templatetags.static import static
import os

def download_pdf_view(request, response_id):
    # Retrieve response object only once
    response = get_object_or_404(ChecklistResponse, id=response_id)
    if request.user.is_authenticated and not request.user.is_superuser:
        if response.created_by_id and response.created_by_id != request.user.id:
            return HttpResponseForbidden("Not allowed")

    report_type = response.report_type
    FREQUENCY_LEVELS = {
        'Daily': 1,
        'Weekly': 2,
        'Monthly': 3,
        'Quarterly': 4,
        'Half Yearly': 5,
        'Annually': 6,
    }

    # Determine frequency level and default to 'Annually'
    selected_freq = response.period_of_inspection or 'Annually'
    selected_level = FREQUENCY_LEVELS.get(selected_freq, 6)

    # Set up logo URL
    logo_url = request.build_absolute_uri(static('/logo.png'))

    # Get checklist items for the report
    checklist_items_master = ChecklistItem.objects.filter(
        report_type=response.report_type,
        frequency_level__lte=selected_level
    )
    
    # Get the latest date from ChecklistItem
    latest_date = checklist_items_master.order_by('-Date').first().Date if checklist_items_master.exists() else date.today()

    # Generate component-specific text
    component = short_codes.get(response.report_type, response.report_type)
    comments = (
        f"1) This is a Generalised Check Sheet for {component}. Some check points may not be applicable to {component} under consideration. "
        f"Please put Not Applicable (NA) in remark column for such points.\n"
        f"2) Please put appropriate remark wherever required.\n"
        f"3) Please also refer to OEM Manual & Manufacturer’s Recommendation (MR) for Inspection, Maintenance & Testing of {component}."
    )

    # Get checklist response items
    checklist_items = ChecklistResponseItem.objects.filter(response=response)

    # Generate format number for the report
    format_no = f"SIPL/O&M/{short_codes.get(response.report_type, response.report_type)}/37"

    # Prepare image URLs
    image_urls = []
    for i in range(1, 7):
        img = getattr(response, f'image{i}', None)
        if img:
            image_urls.append(request.build_absolute_uri(img.url))

    # Prepare signature URLs
    signature_url = request.build_absolute_uri(response.signature.url) if response.signature else None
    signature1_url = request.build_absolute_uri(response.signature1.url) if response.signature1 else None

    # Sanitize all response fields
    def sanitize_text(value):
        if value is None or str(value).strip() == "":
            return "-"
        return strip_tags(str(value))

    response.project_name = sanitize_text(response.project_name)
    response.project_location = sanitize_text(response.project_location)
    response.make = sanitize_text(response.make)
    response.inspection_date = response.inspection_date.strftime("%d-%m-%Y") if response.inspection_date else "-"
    response.next_inspection_date = response.next_inspection_date.strftime("%d-%m-%Y") if response.next_inspection_date else "-"
    response.Type = sanitize_text(response.Type)
    response.period_of_inspection = sanitize_text(response.period_of_inspection)
    response.s_no = sanitize_text(response.s_no)
    response.rating = sanitize_text(response.rating)
    response.comments = sanitize_text(response.comments)
    response.email_to = sanitize_text(response.email_to)
    response.customer_name = sanitize_text(response.customer_name)
    response.solon_name = sanitize_text(response.solon_name)

    for item in checklist_items:
        item.status = sanitize_text(item.status)
        item.remark = sanitize_text(item.remark)

    # Prepare context for rendering
    context = {
        'logo_url': logo_url,
        'response': response,
        'checklist': checklist_items,
        'component': component,
        'image_urls': image_urls,
        'signature_url': signature_url,
        'signature1_url': signature1_url,
        'format_no': format_no,
        'comments': comments,
        'Date': latest_date
    }

    # Render HTML to PDF using the context
    template = get_template('checklist_pdf_template.html')
    html = template.render(context)

    # Convert HTML to PDF
    base_pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=base_pdf)
    base_pdf.seek(0)

    # Apply watermark (if required)
    watermarked_pdf = BytesIO()
    watermark_path = os.path.join(settings.BASE_DIR, 'static', 'Images', 'logo.png')
    print("Watermark path:", watermark_path)
    add_image_watermark_to_pdf(base_pdf, watermarked_pdf, watermark_path)

    # Send the watermarked PDF as a response for download
    response_obj = HttpResponse(watermarked_pdf.getvalue(), content_type='application/pdf')
    response_obj['Content-Disposition'] = f'attachment; filename="Checklist_{response.project_name}.pdf"'
    return response_obj


from pypdf import PdfReader, PdfWriter
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

def add_image_watermark_to_pdf(pdf_data, output_buffer, watermark_image_path):
    pdf_reader = PdfReader(pdf_data)
    pdf_writer = PdfWriter()

    # Get the size of the first page of the actual PDF
    first_page = pdf_reader.pages[0]
    width = float(first_page.mediabox.width)
    height = float(first_page.mediabox.height)

    # Create watermark PDF using same size
    watermark_buffer = BytesIO()
    c = canvas.Canvas(watermark_buffer, pagesize=(width, height))

    c.setFillAlpha(0.1)
    
    # Center watermark
    watermark_width = 400  # adjust size
    watermark_height = 150
    x_center = (width - watermark_width) / 2
    y_center = (height - watermark_height) / 2

    c.drawImage(watermark_image_path, x_center, y_center, width=watermark_width, height=watermark_height, mask='auto')
    c.save()

    # Load watermark and apply to all pages
    watermark_buffer.seek(0)
    watermark_reader = PdfReader(watermark_buffer)
    watermark_page = watermark_reader.pages[0]

    for page in pdf_reader.pages:
        page.merge_page(watermark_page)
        pdf_writer.add_page(page)

    pdf_writer.write(output_buffer)
    output_buffer.seek(0)

from django.contrib.auth.decorators import login_required
from django.db.models import Value
from django.shortcuts import render

@login_required
def history_page(request):
    selected_type = request.GET.get('type')
    selected_project = request.GET.get('project')

    # Base queryset
    all_histories = ChecklistHistory.objects.select_related('checklist')

    # 🔒 Permission scope:
    # Admin: everything
    # User: only their own created reports
    if not request.user.is_superuser:
        all_histories = all_histories.filter(checklist__created_by=request.user)

    # Dropdown values (scoped)
    report_types = (
        all_histories
        .values_list('checklist__report_type', flat=True)
        .distinct()
        .order_by('checklist__report_type')
    )

    # Projects dropdown depends on selected type (scoped)
    if selected_type:
        project_names = (
            all_histories
            .filter(checklist__report_type=selected_type)
            .values_list('checklist__project_name', flat=True)
            .distinct()
            .order_by('checklist__project_name')
        )
    else:
        project_names = []

    # Main table results
    histories = []
    if selected_type:
        filtered = all_histories.filter(checklist__report_type=selected_type)
        if selected_project:
            filtered = filtered.filter(checklist__project_name=selected_project)
        histories = filtered.order_by('-submitted_on')

    return render(request, 'history.html', {
        'report_types': report_types,
        'selected_type': selected_type,
        'histories': histories,
        'project_names': project_names,
        'selected_project': selected_project,
        'all_histories': all_histories,
    })
