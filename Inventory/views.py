def dashboard(request):
    return render(request, 'dashboard.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Site, Inventory
import pandas as pd
from django.contrib.auth.models import User
from demoapp.views import admin_login_view,user_login_view
from django.contrib.auth.decorators import login_required
import math

@login_required(login_url='/superuser/login/')
def upload_inventory(request):
    excel_data = None
    columns = None
    site_name = None
    user_name = None
    # Count unread notifications
    unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

    if request.method == 'POST' and 'file' in request.FILES:
        file = request.FILES['file']
        site_name = request.POST.get('site_name')
        user_name = request.POST.get('user_name')

        try:
            user = User.objects.get(username=user_name)
        except User.DoesNotExist:
            messages.error(request, f"User '{user_name}' does not exist. Please register the user first.")
            return redirect('upload_inventory')

        if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            try:
                # Step 1: Read first few rows without header
                temp_df = pd.read_excel(file, header=None)
                
                # Step 2: Define expected column names
                expected_columns = ['Material Code', 'Material Description', 'Owner', 'Type', 'Category', 'UOM','Opening Stock']#,'Unit Value \n(INR)']

                # Step 3: Detect header row dynamically
                header_row_index = None
                for i in range(min(10, len(temp_df))):  # Check first 10 rows
                    row_values = temp_df.iloc[i].astype(str).str.strip().tolist()
                    if all(col in row_values for col in expected_columns):
                        header_row_index = i
                        break

                if header_row_index is None:
                    messages.error(request, "Header row with expected columns not found in uploaded Excel file.")
                    return redirect('upload_inventory')

                # Step 4: Re-read with correct header row
                df = pd.read_excel(file, header=header_row_index)
                # print(df)

                # Step 5: Clean the data
                df_cleaned = df.dropna(subset=['Material Description'])
                columns = df_cleaned.columns.tolist()
                print(columns)

                # Get or create the site
                site, created = Site.objects.get_or_create(name=site_name)


                # Save inventory data
                for _, row in df_cleaned.iterrows():

                    # Safely handle NaN or blank values
                    opening_stock_raw = row.get('Opening Stock', 0)

                    if pd.isna(opening_stock_raw) or str(opening_stock_raw).strip() == '':
                        opening_stock_value = 0
                    else:
                        try:
                            opening_stock_value = int(float(opening_stock_raw))  # Convert safely
                        except ValueError:
                            opening_stock_value = 0  # fallback if it still fails


                    unit_value_raw = row.get('Unit Value \n(INR)', 0)

                    if pd.isna(unit_value_raw) or str(unit_value_raw).strip() == '':
                        unit_value = 0
                    else:
                        try:
                            unit_value = float(unit_value_raw)  # use float, since unit value may be decimal
                        except ValueError:
                            unit_value = 0

                    Inventory.objects.create(
                        site=site,
                        material_code=row['Material Code'],
                        material_desc=row['Material Description'],
                        owner=row['Owner'],
                        type=row['Type'],
                        category=row['Category'],
                        uom=row['UOM'], 
                        opening_stock=opening_stock_value,#row['Opening Stock'],# \n(FY-2024-25)'],
                        unit_value=unit_value, 
                        user=user
                    )

                messages.success(request, 'Inventory data loaded and saved successfully.')

            except Exception as e:
                messages.error(request, f"Error reading the file: {e}")
        else:
            messages.error(request, 'Please upload a valid Excel file.')

    return render(request, 'upload_inventory.html', {
        'excel_data': excel_data,
        'columns': columns,
        'site_name': site_name,
        'unread_notifications': unread_notifications
    })




# def upload_inventory(request):
#     excel_data = None
#     columns = None
#     site_name = None
#     user_name = None
#     # Count unread notifications
#     unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

#     if request.method == 'POST' and 'file' in request.FILES:
#         file = request.FILES['file']
#         site_name = request.POST.get('site_name')
#         user_name = request.POST.get('user_name')

#         try:
#             user = User.objects.get(username=user_name)
#         except User.DoesNotExist:
#             messages.error(request, f"User '{user_name}' does not exist. Please register the user first.")
#             return redirect('upload_inventory')

#         if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
#             try:
#                 # Read the Excel file
#                 df = pd.read_excel(file, header=2)  # Skipping the first 2 rows
#                 print(df)

#                 # Cleaning the data: drop rows with missing 'Material Description'
#                 df_cleaned = df.dropna(subset=['Material Description'])
#                 columns = df_cleaned.columns.tolist()
#                 print(columns)

#                 # Get or create the site
#                 site, created = Site.objects.get_or_create(name=site_name)

#                 # Get the user based on user_name (either admin selecting a user or the current user)
#                 #user = User.objects.get(username=user_name)

#                 # Save inventory data to the database, linking to the site and user
#                 for _, row in df_cleaned.iterrows():
#                     Inventory.objects.create(
#                         site=site,
#                         material_code=row['Material Code'],
#                         material_desc=row['Material Description'],
#                         owner=row['Owner'],
#                         type=row['Type'],
#                         category=row['Category'],
#                         opening_stock=row['Opening Stock \n(FY-2024-25)'],
#                         user=user  # Link the data to the specific user
#                     )

#                 messages.success(request, 'Inventory data loaded and saved successfully.')
#             except Exception as e:
#                 messages.error(request, f"Error reading the file: {e}")
#         else:
#             messages.error(request, 'Please upload a valid Excel file.')

#     return render(request, 'upload_inventory.html', {'excel_data': excel_data, 'columns': columns, 'site_name': site_name,
#     'unread_notifications': unread_notifications})


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
    # Fetch the site based on the site_name passed in the URL
    # site = Site.objects.get(name=site_name)

     # Check if site_name is 'None' or empty
    if not site_name or site_name.lower() == "none":
        # If site_name is None or 'None', display an error message or redirect
        messages.error(request, "No valid site provided for editing.")
        return redirect('user')  # Redirect to user page or dashboard

    try:
        # Fetch the site based on the site_name passed in the URL
        site = Site.objects.get(name=site_name)
    except Site.DoesNotExist:
        # If the site does not exist, raise a 404 error
        raise Http404("Site not found")
    
    # Fetch inventory data for the specific site
    search_query = request.GET.get('material_code', '')

    if search_query:
        inventory_items = Inventory.objects.filter(site=site, user=request.user, material_code__icontains=search_query)
    else:
        inventory_items = Inventory.objects.filter(site=site, user=request.user)

    if request.method == 'POST':
        # Iterate over each inventory item and update the consumption value
        for inventory in inventory_items:
            consumption = request.POST.get(f'consumption_{inventory.id}')
            if consumption and int(consumption) != 0:
                consumption = int(consumption)  # Parse consumption value

                # Check if consumption exceeds opening stock
                if consumption > inventory.opening_stock:
                    messages.error(request, f"Consumption cannot exceed opening stock for material code {inventory.material_code}.")
                    return render(request, 'edit_inventory.html', {'site': site, 'inventory_items': inventory_items, 'search_query': search_query})

                # Calculate closing stock
                closing_stock = inventory.opening_stock - consumption

                # Get current time in IST
                utc_time = timezone.now()
                Kolkata_timezone = pytz.timezone('Asia/Kolkata')
                india_time = utc_time.astimezone(Kolkata_timezone)
                india_time = india_time.replace(tzinfo=Kolkata_timezone)  
                # india_time = timezone.make_aware(india_time, Kolkata_timezone)
                
                # Create notifications for the updated row
                Notification.objects.create(
                    site=site,
                    material_code=inventory.material_code,
                    material_desc = inventory.material_desc,
                    uom = inventory.uom,
                    opening_stock=inventory.opening_stock,
                    consumption=consumption,
                    closing_stock=closing_stock,
                    timestamp=india_time,
                    unit_value = inventory.unit_value

                )

                RealTimeNotification.objects.create(
                    site=site,
                    material_code=inventory.material_code,
                    material_desc = inventory.material_desc,
                    uom = inventory.uom,
                    opening_stock=inventory.opening_stock,
                    consumption=consumption,
                    closing_stock=closing_stock,
                    timestamp=india_time,
                    user=request.user  # Track the user who made the change
                )

                # Update inventory with new closing stock (and set opening stock to the new closing stock)
                inventory.opening_stock = closing_stock
                inventory.save()  # Save the updated inventory record

        messages.success(request, 'Inventory updated successfully.')
        return redirect('inventory_history', site_name=site_name)  # Redirect to inventory history page after update

    return render(request, 'edit_inventory.html', {'site': site, 'inventory_items': inventory_items, 'search_query': search_query})


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
from datetime import datetime

@login_required(login_url='/superuser/login/')
def notification_list(request):
    # Get the start_date and end_date from GET request
    selected_site = request.GET.get('site_name', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Fetch all available sites for the dropdown
    sites = Site.objects.all()

    # Initialize the notifications query set
    notifications = Notification.objects.all().order_by('-timestamp')

    # Filter by site name if selected
    if selected_site:
        notifications = notifications.filter(site__name=selected_site)

    # Apply filters based on start_date and end_date if provided
    if start_date and end_date:
        try:
            # Parse the dates to compare them
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            notifications = notifications.filter(timestamp__range=[start_date, end_date])
        except ValueError:
            # Handle invalid date format
            notifications = []

    
    # Count unread notifications
    unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

    # Render the template and pass the context
    return render(request, 'notification_list.html', {
        'notifications': notifications,
        'sites': sites,
        'selected_site': selected_site,
        'start_date': start_date,
        'end_date': end_date,
        'unread_notifications': unread_notifications
    })


import json
@login_required(login_url='/superuser/login/')
def site_analysis(request):
    sites = Site.objects.all()
    selected_site = None
    inventories = None
    chart_data = []
    chart_labels = []
    unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

    if request.method == 'POST' or 'site_name' in request.GET:
        site_name = request.POST.get('site_name') or request.GET.get('site_name')
        if site_name:
            selected_site = Site.objects.get(name=site_name)
            inventories = Inventory.objects.filter(site=selected_site)

            chart_labels = [inv.material_code for inv in inventories]
            chart_data = [inv.opening_stock for inv in inventories]

            for inv in inventories:
                unit_val = inv.unit_value or 0
                opening = inv.opening_stock or 0
                inv.total_value = unit_val * opening

    chart_labels_json = json.dumps(chart_labels)
    chart_data_json = json.dumps(chart_data)

    return render(request, 'site_analysis.html', {
        'sites': sites,
        'selected_site': selected_site,
        'inventories': inventories,
        'chart_labels': chart_labels_json,
        'chart_data': chart_data_json,
        'unread_notifications': unread_notifications
    })





# def site_analysis(request):
#     sites = Site.objects.all()
#     selected_site = None
#     inventories = None
#     chart_data = []
#     chart_labels = []
#     unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

#     if request.method == 'POST' or 'site_name' in request.GET:
#         site_name = request.POST.get('site_name') or request.GET.get('site_name')
#         if site_name:
#             selected_site = Site.objects.get(name=site_name)
#             inventories = Inventory.objects.filter(site=selected_site)

#             chart_labels = [inv.material_code for inv in inventories]
#             chart_data = [inv.opening_stock for inv in inventories]

#             for inv in inventories:
#                 unit_val = inv.unit_value or 0
#                 opening = inv.opening_stock or 0
#                 inv.total_value = unit_val * opening

#         # Handle stock update
#         if 'update_stock' in request.POST:
#             site_name = request.POST.get('site_name')
#             selected_site = Site.objects.get(name=site_name)
#             inventories = Inventory.objects.filter(site=selected_site)

#             for inventory in inventories:
#                 current_stock = inventory.opening_stock or 0
#                 current_unit_value = inventory.unit_value or 0.0

#                 # Get new values from form
#                 new_stock = request.POST.get(f"stock_{inventory.id}")
#                 new_unit_value = request.POST.get(f"unit_value_{inventory.id}")

#                 has_changes = False

#                 # Check and update stock
#                 if new_stock:
#                     try:
#                         new_stock = int(new_stock)
#                         if new_stock != current_stock:
#                             inventory.opening_stock = new_stock
#                             has_changes = True
#                     except ValueError:
#                         pass

#                 # Check and update unit value
#                 if new_unit_value:
#                     try:
#                         new_unit_value = float(new_unit_value)
#                         if new_unit_value != current_unit_value:
#                             inventory.unit_value = new_unit_value
#                             has_changes = True
#                     except ValueError:
#                         pass

#                 # Save and create notification only if there are changes
#                 if has_changes:
#                     inventory.save()

#                     Notification.objects.create(
#                         site=inventory.site,
#                         material_code=inventory.material_code,
#                         material_desc = inventory.material_desc,
#                         uom = inventory.uom,
#                         opening_stock=inventory.opening_stock,
#                         consumption=None,
#                         closing_stock=None,
#                         unit_value = inventory.unit_value
#                     )

#             return redirect('site_analysis')

#     # Convert chart data to JSON for chart rendering
#     chart_labels_json = json.dumps(chart_labels)
#     chart_data_json = json.dumps(chart_data)

#     return render(request, 'site_analysis.html', {
#         'sites': sites,
#         'selected_site': selected_site,
#         'inventories': inventories,
#         'chart_labels': chart_labels_json,
#         'chart_data': chart_data_json,
#         'unread_notifications': unread_notifications
#     })


from django.shortcuts import get_object_or_404
from django.urls import reverse

# def edit_inventory1(request, inventory_id):
#     inventory = get_object_or_404(Inventory, id=inventory_id)

#     if request.method == 'POST':
#         inventory.material_code = request.POST.get('material_code')
#         inventory.material_desc = request.POST.get('material_desc')
#         inventory.uom = request.POST.get('uom')
#         inventory.owner = request.POST.get('owner')
#         inventory.type = request.POST.get('type')
#         inventory.category = request.POST.get('category')
#         inventory.save()
#         return redirect('site_analysis')

#     return render(request, 'edit_inventory1.html', {'inventory': inventory})


# def edit_inventory1(request, inventory_id):
#     inventory = get_object_or_404(Inventory, id=inventory_id)
#     site_name = request.GET.get('site_name') or request.POST.get('site_name')

#     if request.method == 'POST':
#         inventory.material_code = request.POST.get('material_code')
#         inventory.material_desc = request.POST.get('material_desc')
#         inventory.uom = request.POST.get('uom')
#         inventory.owner = request.POST.get('owner')
#         inventory.type = request.POST.get('type')
#         inventory.category = request.POST.get('category')
#         inventory.save()
#         return redirect(f"{reverse('site_analysis')}?site_name={site_name}")

#     return render(request, 'edit_inventory1.html', {
#         'inventory': inventory,
#         'site_name': site_name
#     })

from django.shortcuts import get_object_or_404, redirect, render
from .models import Inventory, Site
from django.http import HttpResponseRedirect

# def edit_inventory1(request, inventory_id):
#     # Get the inventory item to edit
#     inventory = get_object_or_404(Inventory, id=inventory_id)
    
#     # Get the site name from the GET parameter
#     site_name = request.GET.get('site_name')
#     selected_site = get_object_or_404(Site, name=site_name) if site_name else None
    
#     if request.method == 'POST':
#         # Save the updated inventory details
#         inventory.material_code = request.POST.get('material_code')
#         inventory.material_desc = request.POST.get('material_desc')
#         inventory.uom = request.POST.get('uom')
#         inventory.owner = request.POST.get('owner')
#         inventory.type = request.POST.get('type')
#         inventory.category = request.POST.get('category')
#         inventory.save()
#         redirect_url = reverse('site_analysis') + f'?site_name={site_name}'
#         return HttpResponseRedirect(redirect_url)
#         # return redirect(f'/site-analysis/?site_name={site_name}')

#         # After saving, redirect back to the same site with the updated inventory
#         # return redirect('site_analysis')  # This automatically uses the site from the context of the previous page
#         # return redirect(reverse('site_analysis') + f'?site_name={site_name}')


#     # If the page is a GET request, render the edit page with the current inventory and selected site
#     return render(request, 'edit_inventory1.html', {
#         'inventory': inventory,
#         'site_name': site_name,  # Pass the site name to the form for redirection after saving
#         'selected_site': selected_site
#     })




from django.urls import reverse
from django.http import HttpResponseRedirect

def edit_inventory1(request, inventory_id):
    inventory = get_object_or_404(Inventory, id=inventory_id)
    site_name = request.GET.get('site_name')

    if request.method == 'POST':
        inventory.material_code = request.POST.get('material_code')
        inventory.material_desc = request.POST.get('material_desc')
        inventory.uom = request.POST.get('uom')
        inventory.owner = request.POST.get('owner')
        inventory.type = request.POST.get('type')
        inventory.category = request.POST.get('category')
        inventory.opening_stock = request.POST.get('opening_stock')
        inventory.unit_value = request.POST.get('unit_value')
        inventory.save()

        # redirect to same site
        redirect_url = reverse('site_analysis') + f'?site_name={site_name}'
        return HttpResponseRedirect(redirect_url)
    total_value = (inventory.opening_stock or 0) * (inventory.unit_value or 0)

    selected_site = get_object_or_404(Site, name=site_name) if site_name else None
    return render(request, 'edit_inventory1.html', {
        'inventory': inventory,
        'site_name': site_name,
        'selected_site': selected_site,
        'total_value': total_value
    })
