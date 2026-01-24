from django.shortcuts import render, redirect

def dashboard(request):
    return render(request, 'dashboard.html')


from django.contrib import messages
from .models import Site, Inventory
from django.contrib.auth.models import User
from demoapp.views import admin_login_view,user_login_view
from django.contrib.auth.decorators import login_required
import math
from django.views.decorators.cache import never_cache


@login_required
def upload_inventory(request):
    import pandas as pd
    excel_data = None
    columns = None
    site_name = None

    unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

    if request.method == 'POST' and 'file' in request.FILES:
        file = request.FILES['file']
        site_name = (request.POST.get('site_name') or '').strip()
        user_name = (request.POST.get('user_name') or '').strip()

        # ✅ Decide user based on role
        if request.user.is_superuser:
            # Admin must choose user
            if not user_name:
                messages.error(request, "Please select a user.")
                return redirect('upload_inventory')

            try:
                user = User.objects.get(username=user_name)
            except User.DoesNotExist:
                messages.error(request, f"User '{user_name}' does not exist. Please register the user first.")
                return redirect('upload_inventory')
        else:
            # Normal user => always self
            user = request.user

        # Basic validation
        if not site_name:
            messages.error(request, "Please enter site name.")
            return redirect('upload_inventory')

        if not (file.name.endswith('.xlsx') or file.name.endswith('.xls')):
            messages.error(request, 'Please upload a valid Excel file.')
            return redirect('upload_inventory')

        try:
            # Step 1: Read first few rows without header
            temp_df = pd.read_excel(file, header=None)

            expected_columns = [
                'Material Code', 'Material Description', 'Owner', 'Type',
                'Category', 'UOM', 'Opening Stock'
            ]

            header_row_index = None
            for i in range(min(10, len(temp_df))):
                row_values = temp_df.iloc[i].astype(str).str.strip().tolist()
                if all(col in row_values for col in expected_columns):
                    header_row_index = i
                    break

            if header_row_index is None:
                messages.error(request, "Header row with expected columns not found in uploaded Excel file.")
                return redirect('upload_inventory')

            # Step 4: Re-read with correct header row
            df = pd.read_excel(file, header=header_row_index)

            # Step 5: Clean the data
            df_cleaned = df.dropna(subset=['Material Description'])
            columns = df_cleaned.columns.tolist()

            # Get or create the site
            site, created = Site.objects.get_or_create(name=site_name)

            # OPTIONAL: If you want normal user only for their site, enforce here
            # if not request.user.is_superuser and site.name != request.user.userprofile.site.name:
            #     return HttpResponseForbidden("Not allowed for this site.")

            # Save inventory data
            for _, row in df_cleaned.iterrows():
                opening_stock_raw = row.get('Opening Stock', 0)
                if pd.isna(opening_stock_raw) or str(opening_stock_raw).strip() == '':
                    opening_stock_value = 0
                else:
                    try:
                        opening_stock_value = int(float(opening_stock_raw))
                    except ValueError:
                        opening_stock_value = 0

                unit_value_raw = row.get('Unit Value \n(INR)', 0)
                if pd.isna(unit_value_raw) or str(unit_value_raw).strip() == '':
                    unit_value = 0
                else:
                    try:
                        unit_value = float(unit_value_raw)
                    except ValueError:
                        unit_value = 0

                Inventory.objects.create(
                    site=site,
                    material_code=row.get('Material Code', ''),
                    material_desc=row.get('Material Description', ''),
                    owner=row.get('Owner', ''),
                    type=row.get('Type', ''),
                    category=row.get('Category', ''),
                    uom=row.get('UOM', ''),
                    opening_stock=opening_stock_value,
                    unit_value=unit_value,
                    fixed_stock=opening_stock_value,
                    user=user
                )

            messages.success(request, 'Inventory data loaded and saved successfully.')
            return redirect('upload_inventory')

        except Exception as e:
            messages.error(request, f"Error reading the file: {e}")
            return redirect('upload_inventory')

    return render(request, 'upload_inventory.html', {
        'excel_data': excel_data,
        'columns': columns,
        "site_name": site_name,
        'unread_notifications': unread_notifications
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Inventory, Site, Notification, RealTimeNotification
from django.utils import timezone
from django.utils.timezone import now
import pytz
from django.http import Http404
from django.contrib import messages

@login_required(login_url='/user/login/')
def edit_inventory(request, site_name):

    if not site_name or site_name.lower() == "none":
        messages.error(request, "No valid site provided for editing.")
        return redirect('user')

    try:
        site = Site.objects.get(name=site_name)
    except Site.DoesNotExist:
        raise Http404("Site not found")

    search_query = request.GET.get('material_desc', '')

    if search_query:
        inventory_items = Inventory.objects.filter(
            site=site, user=request.user,
            material_desc__icontains=search_query
        )
    else:
        inventory_items = Inventory.objects.filter(site=site, user=request.user)

    # helper
    def to_int(v, default=0):
        try:
            v = (v or '').strip()
            return int(v) if v != '' else default
        except (ValueError, TypeError):
            return default

    if request.method == 'POST':

        # IST time
        Kolkata_timezone = pytz.timezone('Asia/Kolkata')
        india_time = timezone.now().astimezone(Kolkata_timezone)

        for inventory in inventory_items:

            # ✅ NEW: user inward stock
            adding_stock = to_int(request.POST.get(f'adding_stock_{inventory.id}'), 0)
            if adding_stock < 0:
                adding_stock = 0

            # existing outward
            consumption = to_int(request.POST.get(f'consumption_{inventory.id}'), 0)
            if consumption < 0:
                consumption = 0

            # If no change in this row, skip
            if adding_stock == 0 and consumption == 0:
                continue

            # ✅ FIRST: apply adding_stock atomically (same as admin)
            if adding_stock > 0:
                Inventory.objects.filter(id=inventory.id).update(
                    invar=F('invar') + adding_stock,
                    opening_stock=F('opening_stock') + adding_stock
                )
                inventory.refresh_from_db(fields=['opening_stock', 'invar'])

            # ✅ THEN: validate + apply consumption
            if consumption > 0:
                if consumption > inventory.opening_stock:
                    messages.error(
                        request,
                        f"Consumption cannot exceed available stock for material code {inventory.material_code}."
                    )
                    return render(request, 'edit_inventory.html', {
                        'site': site,
                        'inventory_items': inventory_items,
                        'search_query': search_query
                    })

                closing_stock = inventory.opening_stock - consumption

                # save notifications (same structure as you already use)
                Notification.objects.create(
                    site=site,
                    material_code=inventory.material_code,
                    material_desc=inventory.material_desc,
                    uom=inventory.uom,
                    opening_stock=inventory.opening_stock,
                    consumption=consumption,
                    closing_stock=closing_stock,
                    timestamp=india_time,
                    unit_value=inventory.unit_value
                )

                RealTimeNotification.objects.create(
                    site=site,
                    material_code=inventory.material_code,
                    material_desc=inventory.material_desc,
                    uom=inventory.uom,
                    opening_stock=inventory.opening_stock,
                    consumption=consumption,
                    closing_stock=closing_stock,
                    timestamp=india_time,
                    user=request.user
                )

                # update opening_stock after consumption
                inventory.opening_stock = closing_stock
                inventory.save(update_fields=['opening_stock'])

            # ✅ OPTIONAL: If you want to store inward in history too
            # (only if your models have adding_stock field, else skip)
            # if adding_stock > 0:
            #     Notification.objects.create(... action="INWARD" ...)
            #     RealTimeNotification.objects.create(... action="INWARD" ...)

        messages.success(request, 'Inventory updated successfully.')
        if search_query:
            return redirect(f"{request.path}?material_desc={search_query}")
        return redirect(request.path)

    return render(request, 'edit_inventory.html', {
        'site': site,
        'inventory_items': inventory_items,
        'search_query': search_query
    })


from django.contrib.auth.decorators import login_required
from django.utils import timezone
import pytz
from .models import Notification, Site
from django.shortcuts import render, redirect
from django.http import Http404
from .models import Site, Inventory
from django.contrib import messages
from django.db.models import Sum
from datetime import datetime, timedelta

@login_required(login_url='/user/login/')
def stock_report_view(request, site_name):
    if not site_name or site_name.lower() == "none":
        messages.error(request, "No valid site provided for report.")
        return redirect('user')

    try:
        site = Site.objects.get(name=site_name)
    except Site.DoesNotExist:
        raise Http404("Site not found")

    search_query = request.GET.get('material_desc', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    inventory_items = Inventory.objects.filter(site=site, user=request.user)
    if search_query:
        inventory_items = inventory_items.filter(material_desc__icontains=search_query)

    report_data = []

    for item in inventory_items:
        notif_filter = {
            'site': site,
            'material_code': item.material_code,
        }

        # ✅ Filter by timestamp range if provided
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                notif_filter['timestamp__gte'] = start
                notif_filter['timestamp__lt'] = end
            except ValueError:
                pass  

        closing_stock_agg = Notification.objects.filter(**notif_filter).aggregate(total=Sum('consumption'))
        closing_stock = closing_stock_agg['total'] or 0

        report_data.append({
            'material_code': item.material_code,
            'material_desc': item.material_desc,
            'owner':item.owner,
            'type':item.type,
            'uom':item.uom,
            'category':item.category,
            'fixed_stock' : item.fixed_stock,
            'opening_stock': item.opening_stock,
            'invar': item.invar,                 # ✅ NEW: Inward (invar)
            'closing_stock': closing_stock
        })

    return render(request, 'stock_report.html', {
        'site': site,
        'inventory_items': report_data,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date
    })



from django.http import HttpResponse, Http404
from django.utils.timezone import now
from openpyxl import Workbook
from io import BytesIO
from .models import Site, Inventory, Notification

@login_required(login_url='/user/login/')
def export_stock_report_excel(request, site_name):
    if not site_name or site_name.lower() == "none":
        return HttpResponse("Invalid site name", status=400)

    try:
        site = Site.objects.get(name=site_name)
    except Site.DoesNotExist:
        raise Http404("Site not found")

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    inventory_items = Inventory.objects.filter(site=site, user=request.user)

    report_data = []
    for item in inventory_items:
        notif_filter = {
            "site": site,
            "material_code": item.material_code,
        }

        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                notif_filter["timestamp__gte"] = start
                notif_filter["timestamp__lt"] = end
            except ValueError:
                pass

        closing_stock_agg = Notification.objects.filter(**notif_filter).aggregate(total=Sum("consumption"))
        closing_stock = closing_stock_agg["total"] or 0

        report_data.append([
            item.material_code,
            item.material_desc,
            item.owner,
            item.type,
            item.category,
            item.uom,
            item.fixed_stock,
            closing_stock,
            item.invar,            # ✅ NEW: Inward (invar)
            item.opening_stock
        ])

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock Report"

    # Write header
    headers = [
        "Material Code", "Material Description", "Owner", "Type", "Category",
        "UOM", "Opening Stock", "Consumption","Inward (invar)", "Available Stock"
    ]
    ws.append(headers)

    # Write data
    for row in report_data:
        ws.append(row)

    # Filename
    today = now().date().isoformat()
    filename = f"Inventory_Stock_Report_{today}.xlsx"

    # Save to memory
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    # Return response
    response = HttpResponse(
        excel_file.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response



@login_required(login_url='/user/login/')
def inventory_history(request, site_name):
    # Fetch the site and updated inventory data
    site = Site.objects.get(name=site_name)
    inventory_items = Inventory.objects.filter(site=site, user=request.user)
    
    # Fetch notifications to display changes
    notifications = Notification.objects.filter(site=site).order_by('-timestamp')

    return render(request, 'inventory_history.html', {'site': site, 'inventory_items': inventory_items, 'notifications': notifications })


@login_required(login_url='/superuser/login/')
def real_time_notification_list(request):
    # Fetch all real-time notifications for the logged-in user
    #notifications = RealTimeNotification.objects.filter(user=request.user).order_by('-timestamp')
    notifications = RealTimeNotification.objects.all().order_by('-timestamp')

    unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

    if request.method == "POST":
        if 'mark_as_read' in request.POST:
            notification_id = request.POST.get('notification_id')
            notification = RealTimeNotification.objects.get(id=notification_id)
            notification.is_read = True
            notification.save()
            return redirect('real_time_notification_list')

        if 'delete' in request.POST:
            notification_id = request.POST.get('notification_id')
            notification = RealTimeNotification.objects.get(id=notification_id)
            notification.delete()
            return redirect('real_time_notification_list')

    context = {
        'notifications': notifications,
    }

    return render(request, 'real_time_notification_list.html', context)


from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render
from .models import Notification
from datetime import datetime, timedelta
from django.http import HttpResponse
import csv

@login_required(login_url='/superuser/login/')
def notification_list(request):
    # Read raw GET strings so inputs stay sticky
    selected_site = request.GET.get('site_name', '')
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    sites = Site.objects.all()

    notifications = Notification.objects.select_related('site').all().order_by('-timestamp')

    if selected_site:
        notifications = notifications.filter(site__name=selected_site)

    # Date filters (inclusive)
    try:
        if start_date_str and end_date_str:
            start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # include end-date full day
            notifications = notifications.filter(timestamp__gte=start_dt, timestamp__lt=end_dt)
        elif start_date_str:
            start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
            notifications = notifications.filter(timestamp__date__gte=start_date_str)
        elif end_date_str:
            end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
            notifications = notifications.filter(timestamp__date__lte=end_date_str)
    except ValueError:
        notifications = Notification.objects.none()  # invalid date -> empty

    # Export (Excel CSV) if requested
    if request.GET.get('export') == '1':
        return _export_notifications_csv(
            notifications, start_date_str, end_date_str, selected_site
        )

    unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

    return render(request, 'notification_list.html', {
        'notifications': notifications,
        'sites': sites,
        'selected_site': selected_site,
        # pass strings so <input type="date"> keeps values
        'start_date': start_date_str,
        'end_date': end_date_str,
        'unread_notifications': unread_notifications,
    })


def _export_notifications_csv(qs, start_date_str, end_date_str, selected_site):
    """Download the filtered table as Excel-compatible CSV."""
    # filename like: notifications_[Site]_2025-08-01_2025-08-26.csv
    parts = ["notifications"]
    if selected_site:
        parts.append(selected_site.replace(" ", "_"))
    if start_date_str or end_date_str:
        parts.append((start_date_str or "start"))
        parts.append((end_date_str or "end"))
    filename = "_".join(parts) + ".csv"

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    # headers match table columns
    writer.writerow([
        "Site Name", "Material Code", "Material Desc", "UOM",
        "Opening Stock", "Consumption", "Closing Stock",
        "Timestamp", "Unit Value"
    ])

    for n in qs.select_related('site'):
        writer.writerow([
            getattr(n.site, "name", ""),
            n.material_code,
            n.material_desc,
            n.uom,
            n.opening_stock,
            n.consumption,
            n.closing_stock,
            n.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            n.unit_value,
        ])

    return response




# OLD CODE
# @login_required(login_url='/superuser/login/')
# def notification_list(request):
#     # Get the start_date and end_date from GET request
#     selected_site = request.GET.get('site_name', '')
#     start_date = request.GET.get('start_date', '')
#     end_date = request.GET.get('end_date', '')

#     # Fetch all available sites for the dropdown
#     sites = Site.objects.all()

#     # Initialize the notifications query set
#     notifications = Notification.objects.all().order_by('-timestamp')

#     # Filter by site name if selected
#     if selected_site:
#         notifications = notifications.filter(site__name=selected_site)

#     # Apply filters based on start_date and end_date if provided
#     if start_date and end_date:
#         try:
#             # Parse the dates to compare them
#             start_date = datetime.strptime(start_date, '%Y-%m-%d')
#             end_date = datetime.strptime(end_date, '%Y-%m-%d')
#             notifications = notifications.filter(timestamp__range=[start_date, end_date])
#         except ValueError:
#             # Handle invalid date format
#             notifications = []


#     unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

#     return render(request, 'notification_list.html', {
#         'notifications': notifications,
#         'sites': sites,
#         'selected_site': selected_site,
#         'start_date': start_date,
#         'end_date': end_date,
#         'unread_notifications': unread_notifications
#     })

#updated code
import json
@login_required(login_url='/superuser/login/')
def site_analysis(request):

    # ✅ Carry-forward once per new year:
    # current_yr = timezone.now().year
    # Inventory.objects.filter(fixed_stock_year__lt=current_yr).update(
    #     fixed_stock=F('opening_stock'),
    #     fixed_stock_year=current_yr
    # )


    sites = Site.objects.all()
    selected_site = None
    inventories = None
    unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()
    total_site_value = 0

    if request.method == 'POST' or 'site_name' in request.GET:
        site_name = request.POST.get('site_name') or request.GET.get('site_name')
        if site_name:
            try:
                selected_site = Site.objects.get(name=site_name)
                inventories = Inventory.objects.filter(site=selected_site)

                for inv in inventories:
                    unit_val = inv.unit_value or 0
                    available = inv.opening_stock or 0      # A
                    initial  = inv.fixed_stock or 0         # S0
                    inward   = getattr(inv, 'invar', 0) or 0  # I (defaults to 0 if field exists)

                    # table values
                    inv.total_value = unit_val * available

                    # ✅ Correct consumption:
                    # Consumption = (initial + inward) - available
                    inv.final_stock = max((initial + inward) - available, 0)

                total_site_value = sum(
                    (inv.unit_value or 0) * (inv.opening_stock or 0)
                    for inv in inventories
                )

            except Site.DoesNotExist:
                selected_site = None

    return render(request, 'site_analysis.html', {
        'sites': sites,
        'selected_site': selected_site,
        'inventories': inventories,
        'unread_notifications': unread_notifications,
        'total_site_value': total_site_value
    })




# 1ST
# def site_analysis(request):
#     sites = Site.objects.all()
#     selected_site = None
#     inventories = None
#     unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()
#     total_site_value = 0  # <- Add this line

#     if request.method == 'POST' or 'site_name' in request.GET:
#         site_name = request.POST.get('site_name') or request.GET.get('site_name')
#         if site_name:
#             try:
#                 selected_site = Site.objects.get(name=site_name)
#                 inventories = Inventory.objects.filter(site=selected_site)

#                 for inv in inventories:
#                     unit_val = inv.unit_value or 0
#                     opening = inv.opening_stock or 0
#                     fixed = inv.fixed_stock or 0
#                     inv.total_value = unit_val * opening
#                     inv.final_stock = max(fixed - opening,0)

#                 # ✅ Sum all total values
#                 total_site_value = sum((inv.unit_value or 0) * (inv.opening_stock or 0) for inv in inventories)

#             except Site.DoesNotExist:
#                 selected_site = None

#     return render(request, 'site_analysis.html', {
#         'sites': sites,
#         'selected_site': selected_site,
#         'inventories': inventories,
#         'unread_notifications': unread_notifications,
#         'total_site_value': total_site_value  # <- Pass to template
#     })


from django.shortcuts import get_object_or_404, redirect, render
from .models import Inventory, Site
from django.urls import reverse
from django.http import HttpResponseRedirect


# def edit_inventory1(request, inventory_id):
#     inventory = get_object_or_404(Inventory, id=inventory_id)
#     site_name = request.GET.get('site_name')

#     # ✅ Always fetch site safely
#     selected_site = None
#     if site_name:
#         try:
#             selected_site = Site.objects.get(name=site_name)
#         except Site.DoesNotExist:
#             selected_site = None  # Or handle error if you want

#     if request.method == 'POST':
#         inventory.material_code = request.POST.get('material_code')
#         inventory.material_desc = request.POST.get('material_desc')
#         inventory.uom = request.POST.get('uom')
#         inventory.owner = request.POST.get('owner')
#         inventory.type = request.POST.get('type')
#         inventory.category = request.POST.get('category')
#         inventory.opening_stock = request.POST.get('opening_stock')
#         inventory.unit_value = request.POST.get('unit_value')
#         inventory.save()

#         redirect_url = reverse('site_analysis') + f'?site_name={site_name}'
#         return HttpResponseRedirect(redirect_url)

#     total_value = (inventory.opening_stock or 0) * (inventory.unit_value or 0)

#     # ✅ Only calculate sum if site is found
#     total_site_value = 0
#     if selected_site:
#         inventory_items = Inventory.objects.filter(site=selected_site)
#         total_site_value = sum((item.opening_stock or 0) * (item.unit_value or 0) for item in inventory_items)

#     return render(request, 'edit_inventory1.html', {
#         'inventory': inventory,
#         'site_name': site_name,
#         'selected_site': selected_site,
#         'total_value': total_value,
#         'total_site_value': total_site_value
#     })


# updTED CODE
from django.db.models import F
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse

def edit_inventory1(request, inventory_id):
    inventory = get_object_or_404(Inventory, id=inventory_id)
    site_name = request.GET.get('site_name')

    selected_site = None
    if site_name:
        selected_site = Site.objects.filter(name=site_name).first()

    def to_int(val, default=0):
        try:
            val = (val or '').strip()
            return int(val) if val != '' else default
        except (ValueError, TypeError):
            return default

    def to_float(val, default=0.0):
        try:
            val = (val or '').strip()
            return float(val) if val != '' else default
        except (ValueError, TypeError):
            return default

    if request.method == 'POST':
        # basic text fields
        inventory.material_code = request.POST.get('material_code', '') or ''
        inventory.material_desc = request.POST.get('material_desc', '') or ''
        inventory.uom = request.POST.get('uom', '') or ''
        inventory.owner = request.POST.get('owner', '') or ''
        inventory.type = request.POST.get('type', '') or ''
        inventory.category = request.POST.get('category', '') or ''

        # numeric fields
        inventory.opening_stock = to_int(request.POST.get('opening_stock'), 0)
        inventory.unit_value = to_float(request.POST.get('unit_value'), 0.0)

        # ✅ Add Stock (inward)
        adding_stock = to_int(request.POST.get('adding_stock'), 0)
        if adding_stock < 0:
            adding_stock = 0

        # Save edited base fields first
        inventory.save()

        # ✅ Atomically add stock to BOTH invar + opening_stock
        if adding_stock > 0:
            Inventory.objects.filter(id=inventory.id).update(
                invar=F('invar') + adding_stock,
                opening_stock=F('opening_stock') + adding_stock
            )
            # refresh values for totals / UI (if you ever render instead of redirect)
            inventory.refresh_from_db(fields=['invar', 'opening_stock'])

        redirect_url = reverse('site_analysis') + (f'?site_name={site_name}' if site_name else '')
        return HttpResponseRedirect(redirect_url)

    total_value = (inventory.opening_stock or 0) * (inventory.unit_value or 0)

    total_site_value = 0
    if selected_site:
        inventory_items = Inventory.objects.filter(site=selected_site)
        total_site_value = sum(
            (item.opening_stock or 0) * (item.unit_value or 0)
            for item in inventory_items
        )

    return render(request, 'edit_inventory1.html', {
        'inventory': inventory,
        'site_name': site_name,
        'selected_site': selected_site,
        'total_value': total_value,
        'total_site_value': total_site_value
    })
