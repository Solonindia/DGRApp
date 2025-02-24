from django.db import models
from django.utils import timezone
import pytz

class VisitorLog(models.Model):
    name_of_plant = models.CharField(max_length=100)
    visitor_name = models.CharField(max_length=100)
    visitor_company_name = models.CharField(max_length=100)
    purpose_of_visit = models.CharField(max_length=255)
    valid_from_datetime = models.DateTimeField()
    valid_to_datetime = models.DateTimeField()
    contact_details = models.CharField(max_length=255)
    emergency_contact_details = models.CharField(max_length=255)
    emergency_mobile_contact = models.CharField(max_length=15)
    relationship = models.CharField(max_length=100)
    gate_pass_issue_datetime = models.DateTimeField()
    visitor_image = models.ImageField(upload_to='visitor_images/', blank=True, null=True)  # New field for image
    serial_number = models.PositiveIntegerField(blank=True, null=True, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    gatepass_id = models.CharField(max_length=255, blank=True, editable=False)
    dup_username = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        indian_timezone = pytz.timezone('Asia/Kolkata')
        
        # Convert UTC to IST before saving
        if self.valid_from_datetime:
            self.valid_from_datetime = self.valid_from_datetime.astimezone(indian_timezone)
        if self.valid_to_datetime:
            self.valid_to_datetime = self.valid_to_datetime.astimezone(indian_timezone)
        if self.gate_pass_issue_datetime:
            self.gate_pass_issue_datetime = self.gate_pass_issue_datetime.astimezone(indian_timezone)

        super().save(*args, **kwargs)

    def generate_gatepass_id(self):
        """Generates a unique Complaint ID based on year and serial number."""
        now = timezone.now()
        year = now.year  # Get the current year
        
        # Generate the base complaint ID in the format YYYY
        base_id = f"{year}"

        # Get the last complaint's serial number from the database
        last_gatepass = VisitorLog.objects.all().order_by('-serial_number').first()

        # If complaints exist, get the highest serial number and increment it by 1
        if last_gatepass and last_gatepass.serial_number is not None:
            serial_number = last_gatepass.serial_number + 1
        else:
            serial_number = 1  # Start from 1 if no complaints exist

        # Determine the correct length for the serial number based on the last one
        # If the last complaint serial number had 3 digits, make sure the new serial number has more than 3 digits if necessary
        serial_number_str = str(serial_number)

        # Format the Complaint ID as YYYY followed by the serial number
        gatepass_id = f"{base_id}{serial_number_str}"

        # Optionally, check for uniqueness if you're using the same serial number for multiple complaints
        count = 1
        unique_id = gatepass_id
        while VisitorLog.objects.filter(gatepass_id=unique_id).exists():
            # Ensure the uniqueness by adding an incremental counter if needed
            unique_id = f"{gatepass_id}{count}"
            count += 1

        # Assign the serial_number and generated Complaint ID to this instance
        self.serial_number = serial_number
        self.gatepass_id = unique_id

        return unique_id

    # def generate_gatepass_id(self):
    #     """Generates a unique Complaint ID based on year and serial number."""
    #     now = timezone.now()
    #     year = now.year  # Get the current year
        
    #     # Generate the base complaint ID in the format YYYY
    #     base_id = f"{year}"

    #     # Get the last complaint's serial number from the database
    #     last_gatepass = VisitorLog.objects.all().order_by('-serial_number').first()

    #     # If complaints exist, get the highest serial number and increment it by 1
    #     if last_gatepass and last_gatepass.serial_number is not None:
    #         serial_number = last_gatepass.serial_number + 1
    #     else:
    #         serial_number = 1  # Start from 1 if no complaints exist

    #     # Format the Complaint ID as YYYYSS (where SS is the serial number)
    #     gatepass_id = f"{base_id}{serial_number:02d}"  # Ensure serial number has 3 digits (001, 002, ..., 999)

    #     # Optionally, check for uniqueness if you're using the same serial number for multiple complaints in one day
    #     count = 1
    #     unique_id = gatepass_id
    #     while VisitorLog.objects.filter(gatepass_id=unique_id).exists():
    #         unique_id = f"{gatepass_id}{count:02d}"  # Append a counter to ensure uniqueness
    #         count += 1

    #     # Assign the serial_number and generated Complaint ID to this instance
    #     self.serial_number = serial_number
    #     self.gatepass_id = unique_id

    #     return unique_id

    # def generate_gatepass_id(self):
    #     """Generates a unique Gatepass ID based on the current year and a serial number."""
    #     now = timezone.now()
    #     year = now.year  # Get the current year
        
    #     # Generate the base gatepass ID as "YYYY"
    #     base_id = f"{year}"

    #     # Get the last visitor log for the given year and the highest serial number
    #     last_gatepass = VisitorLog.objects.filter(created_at__year=year).order_by('-serial_number').first()

    #     # If no visitor logs exist for the current year, start serial number from 1
    #     serial_number = 1 if not last_gatepass else last_gatepass.serial_number + 1

    #     # Create the base gatepass ID with the format YYYYSS (where SS is the serial number)
    #     gatepass_id = f"{base_id}{serial_number:02d}"  # Ensure the serial number is always two digits

    #     # Optionally, check for uniqueness if you want to handle conflicts more robustly
    #     count = 1
    #     unique_id = gatepass_id
    #     while VisitorLog.objects.filter(gatepass_id=unique_id).exists():
    #         unique_id = f"{gatepass_id}{count:03d}"  # Append a counter to ensure uniqueness
    #         count += 1

    #     # Return the generated unique gatepass ID
    #     return unique_id

    def save(self, *args, **kwargs):
        """Override the save method to generate the gatepass_id before saving."""
        if not self.gatepass_id:
            self.gatepass_id = self.generate_gatepass_id()

        # Ensure the serial number is also set before saving
        if not self.serial_number:
            self.serial_number = int(self.gatepass_id[-2:])  # Extract the serial number part

        # Proceed with the save
        super().save(*args, **kwargs)