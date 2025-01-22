# Dashboard View
def dashboard(request):
    return render(request, 'dashboard.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Site, Inventory
import pandas as pd
from django.contrib.auth.models import User

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

        # Only admin can upload for another user
        # if request.user.is_staff and user_name == request.user.username:
        #     messages.error(request, "you can not upload for this user and please register user")
        #     #messages.error(request, "You can only upload inventory for yourself.")
        #     return redirect('upload_inventory')

        if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            try:
                # Read the Excel file
                df = pd.read_excel(file, header=2)  # Skipping the first 2 rows

                # Cleaning the data: drop rows with missing 'Material Description'
                df_cleaned = df.dropna(subset=['Material Description'])
                columns = df_cleaned.columns.tolist()

                # Get or create the site
                site, created = Site.objects.get_or_create(name=site_name)

                # Get the user based on user_name (either admin selecting a user or the current user)
                #user = User.objects.get(username=user_name)

                # Save inventory data to the database, linking to the site and user
                for _, row in df_cleaned.iterrows():
                    Inventory.objects.create(
                        site=site,
                        material_code=row['Material Code'],
                        material_desc=row['Material Description'],
                        owner=row['Owner'],
                        type=row['Type'],
                        category=row['Category'],
                        opening_stock=row['Opening Stock \n(FY-2024-25)'],
                        user=user  # Link the data to the specific user
                    )

                messages.success(request, 'Inventory data loaded and saved successfully.')
            except Exception as e:
                messages.error(request, f"Error reading the file: {e}")
        else:
            messages.error(request, 'Please upload a valid Excel file.')

    return render(request, 'upload_inventory.html', {'excel_data': excel_data, 'columns': columns, 'site_name': site_name,
    'unread_notifications': unread_notifications})




def view_notifications(request):
    return render(request, 'view_notifications.html')



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Inventory, Site, Notification, RealTimeNotification
from django.utils import timezone
from django.utils.timezone import now
import pytz
from django.http import Http404
from django.contrib import messages

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
                india_time = india_time.replace(tzinfo=Kolkata_timezone)  # Ensure it's timezone-aware
                
                # Create notifications for the updated row
                Notification.objects.create(
                    site=site,
                    material_code=inventory.material_code,
                    opening_stock=inventory.opening_stock,
                    consumption=consumption,
                    closing_stock=closing_stock,
                    timestamp=india_time
                )

                RealTimeNotification.objects.create(
                    site=site,
                    material_code=inventory.material_code,
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





# from django.shortcuts import render, redirect
# from django.contrib import messages
# from .models import Inventory, Site, Notification, RealTimeNotification
# from django.utils import timezone
# from django.utils.timezone import now
# import pytz

# def edit_inventory(request, site_name):
#     # Fetch the site based on the site_name passed in the URL
#     site = Site.objects.get(name=site_name)
    
#     # Fetch inventory data for the specific site
#     #inventory_items = Inventory.objects.filter(site=site, user=request.user)

#     # Get the search query (e.g., material_code) from the GET request
#     search_query = request.GET.get('material_code', '')

#     # Fetch inventory data for the specific site and filter based on the search query if provided
#     if search_query:
#         inventory_items = Inventory.objects.filter(site=site, user=request.user, material_code__icontains=search_query)
#     else:
#         inventory_items = Inventory.objects.filter(site=site, user=request.user)

#     if request.method == 'POST':
#         # Iterate over each inventory item and update the consumption value
#         for inventory in inventory_items:
#             consumption = request.POST.get(f'consumption_{inventory.id}')
#             if consumption and int(consumption) != 0:
#                 consumption = int(consumption)  # Parse consumption value
#                 # Calculate closing stock
#                 closing_stock = inventory.opening_stock - consumption

#                 utc_time = timezone.now()

#                 # Convert UTC time to India Standard Time (IST)
#                 Kolkata_timezone = pytz.timezone('Asia/Kolkata')
#                 india_time = utc_time.astimezone(Kolkata_timezone)

#                 # Ensure that the india_time is timezone-aware before saving
#                 india_time = india_time.replace(tzinfo=Kolkata_timezone)  # Ensure it's timezone-aware
#                 print(india_time)

                


                
#                 # Create a Notification for the updated row
#                 Notification.objects.create(
#                     site=site,
#                     material_code=inventory.material_code,
#                     opening_stock=inventory.opening_stock,
#                     consumption=consumption,
#                     closing_stock=closing_stock,
#                     timestamp = india_time
#                     #timestamp = current_time1
#                     #timestamp=timezone.now()
#                 )

#                 # Create a Real-Time Notification for the updated row (Real-Time Notification)
#                 RealTimeNotification.objects.create(
#                     site=site,
#                     material_code=inventory.material_code,
#                     opening_stock=inventory.opening_stock,
#                     consumption=consumption,
#                     closing_stock=closing_stock,
#                     timestamp = india_time,
#                     #timestamp=current_time1,
#                     #timestamp=timezone.now(),
#                     user=request.user  # Track the user who made the change
#                 )
                
#                 # Update inventory with new closing stock (and set opening stock to the new closing stock)
#                 inventory.opening_stock = closing_stock
#                 inventory.save()  # Save the updated inventory record

#         messages.success(request, 'Inventory updated successfully.')
#         return redirect('inventory_history', site_name=site_name)  # Redirect to inventory history page after update

#     return render(request, 'edit_inventory.html', {'site': site, 'inventory_items': inventory_items,'search_query': search_query})


def inventory_history(request, site_name):
    # Fetch the site and updated inventory data
    site = Site.objects.get(name=site_name)
    inventory_items = Inventory.objects.filter(site=site, user=request.user)
    
    # Fetch notifications to display changes
    notifications = Notification.objects.filter(site=site).order_by('-timestamp')

    return render(request, 'inventory_history.html', {'site': site, 'inventory_items': inventory_items, 'notifications': notifications })


def real_time_notification_list(request):
    # Fetch all real-time notifications for the logged-in user
    #notifications = RealTimeNotification.objects.filter(user=request.user).order_by('-timestamp')
    notifications = RealTimeNotification.objects.all().order_by('-timestamp')

    # Count unread notifications
    unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()
    #print(unread_notifications)


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
        #'unread_notifications': unread_notifications
    }

    return render(request, 'real_time_notification_list.html', context)





# def real_time_notification_list(request):
#     # Fetch all real-time notifications for the logged-in user
#     notifications = RealTimeNotification.objects.all().order_by('-timestamp')

#     # Count unread notifications
#     unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

#     # Handle POST request actions (mark as read, delete)
#     if request.method == "POST":
#         if 'mark_as_read' in request.POST:
#             notification_id = request.POST.get('notification_id')
#             try:
#                 notification = RealTimeNotification.objects.get(id=notification_id)
#                 notification.is_read = True
#                 notification.save()
#             except RealTimeNotification.DoesNotExist:
#                 # Handle case where notification doesn't exist, maybe log this or notify user
#                 pass
#             return redirect('real_time_notification_list')

#         if 'delete' in request.POST:
#             notification_id = request.POST.get('notification_id')
#             try:
#                 notification = RealTimeNotification.objects.get(id=notification_id)
#                 notification.delete()
#             except RealTimeNotification.DoesNotExist:
#                 # Handle case where notification doesn't exist, maybe log this or notify user
#                 pass
#             return redirect('real_time_notification_list')

#     context = {
#         'notifications': notifications,
#         'unread_notifications': unread_notifications,
#     }

#     return render(request, 'real_time_notification_list.html', context)





from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect

# def home_page(request):
#     return render(request, 'home_page.html')

# def redirect_to_home(request):
#     return redirect('home')


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





# def user_page(request):
#     # Get the sites related to the logged-in user
#     sites = Site.objects.filter(inventory__user=request.user).distinct()  # Only fetch sites the user has access to

#     # If you want to pass the first site's name as a default or show all available sites
#     # If there's at least one site, pass the first one as a default
#     site_name = sites.first().name if sites.exists() else None

#     return render(request, 'user.html', {'sites': sites, 'site_name': site_name})



from django.shortcuts import render
from .models import Notification
from datetime import datetime

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
def site_analysis(request):
    sites = Site.objects.all()
    selected_site = None
    inventories = None
    chart_data = []
    chart_labels = []
    unread_notifications = RealTimeNotification.objects.filter(is_read=False).count()

    if request.method == 'POST':
        # Handle site selection
        if 'site_name' in request.POST:
            site_name = request.POST['site_name']
            selected_site = Site.objects.get(name=site_name)
            inventories = Inventory.objects.filter(site=selected_site)

            # Prepare data for the chart
            chart_labels = [inventory.material_code for inventory in inventories]
            chart_data = [inventory.opening_stock for inventory in inventories]

        # Handle stock updates
        if 'update_stock' in request.POST:
            # Iterate through the inventories and update stock values
            for inventory in inventories:
                # Retrieve the new stock value from the POST data
                new_stock = request.POST.get(f"stock_{inventory.id}")
                if new_stock:
                    new_stock = int(new_stock)
                    # Update the Inventory model
                    inventory.opening_stock = new_stock
                    inventory.save()

                    # Create a notification for the update
                    Notification.objects.create(
                        site=inventory.site,
                        material_code=inventory.material_code,
                        opening_stock=new_stock,
                        consumption=None,
                        closing_stock=None
                    )

            # After updating, reload the page with the updated inventories
            return redirect('site_analysis')  # Redirect to avoid re-posting on refresh

    # Convert lists to JSON format before passing them to the template
    chart_labels_json = json.dumps(chart_labels)
    chart_data_json = json.dumps(chart_data)

    return render(request, 'site_analysis.html', {
        'sites': sites,
        'selected_site': selected_site,
        'inventories': inventories,
        'chart_labels': chart_labels_json,  # Ensure data is passed in JSON format
        'chart_data': chart_data_json,  # Ensure data is passed in JSON format
        'unread_notifications': unread_notifications
    })


