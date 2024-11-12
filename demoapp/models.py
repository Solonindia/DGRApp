from django.db import models
from django.utils import timezone
import pytz
from datetime import datetime
import json
from django.contrib.auth.models import User

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Update', 'Update'),
    ]
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    CLAIM_CHOICES = [
        ('Under Warranty', 'Under Warranty'),
        ('Chargeable', 'Chargeable'),
    ]

    serial_number = models.PositiveIntegerField(blank=True, null=True, editable=False)
    dup_username = models.CharField(max_length=255, blank=True, null=True)
    id = models.BigAutoField(primary_key=True)
    equipment = models.CharField(max_length=255, blank=True, null=True)
    complaint_raised_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    complaint_id = models.CharField(max_length=255,blank=True, editable=False)
    company_name = models.CharField(max_length=255)
    site_name = models.CharField(max_length=255)
    attended_by = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    claim_type = models.CharField(max_length=20, choices=CLAIM_CHOICES)
    nature_of_complaint = models.TextField(blank=True, null=True)
    images = models.TextField(blank=False, null=True)
    location = models.CharField(max_length=50, default='Hyderabad')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    summary_of_action_taken = models.TextField(blank=True, null=True)
    root_cause = models.TextField(blank=True, null=True)
    preventive_action = models.TextField(blank=True, null=True)
    parts_replaced_for_rectification = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to='pdfs/', blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} - {self.site_name} ({self.status}, {self.priority}, {self.location}, {self.claim_type})"

    def get_images(self):
        """Returns a list of image URLs."""
        if self.images:
            return json.loads(self.images)
        return []

    def generate_complaint_id(self):
        """Generates a unique Complaint ID based on year and serial number."""
        now = timezone.now()
        year = now.year  # Get the current year
        
        # Generate the base complaint ID in the format YYYY
        base_id = f"{year}"

        # Get the last complaint for the given year and the highest serial number
        last_complaint = Complaint.objects.filter(
            created_at__year=year
        ).order_by('-serial_number').first()

        # If no complaints exist for the current year, start serial number from 1
        if last_complaint and last_complaint.serial_number is not None:
            serial_number = last_complaint.serial_number + 1
        else:
            serial_number = 1  # Start from 1 if no complaints exist for this year

        # Format the Complaint ID as YYYYSS (where SS is the serial number)
        complaint_id = f"{base_id}{serial_number:02d}"  # Ensure serial number has 2 digits (01, 02, ..., 99)

        # Optionally, check for uniqueness if you're using the same serial number for multiple complaints in one day
        count = 1
        unique_id = complaint_id
        while Complaint.objects.filter(complaint_id=unique_id).exists():
            unique_id = f"{complaint_id}{count:03d}"  # Append a counter to ensure uniqueness
            count += 1

        # Assign the serial_number and generated Complaint ID to this instance
        self.serial_number = serial_number
        self.complaint_id = unique_id

        return unique_id
    
    def save(self, *args, **kwargs):
        """Override save method to ensure complaint_id and serial_number are set."""
        if not self.complaint_id:
            self.complaint_id = self.generate_complaint_id()

        # Remove the get_next_serial_number method, since serial_number is already set
        super().save(*args, **kwargs)


