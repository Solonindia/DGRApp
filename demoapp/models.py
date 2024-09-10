from django.db import models
from django.utils import timezone
import pytz
import json
from datetime import datetime

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Update','Update'),
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
    id = models.BigAutoField(primary_key=True)
    equipment = models.CharField(max_length=255, blank=True, null=True)
    complaint_raised_by = models.CharField(max_length=255, blank=True, null=True)

    # Fields for the complaint
    created_at = models.DateTimeField(auto_now_add=True,blank=True) 
    complaint_id = models.CharField(max_length=255, unique=True, blank=True, editable=False)
    company_name = models.CharField(max_length=255)
    site_name = models.CharField(max_length=255)
    attended_by = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    claim_type = models.CharField(max_length=20, choices=CLAIM_CHOICES)
    nature_of_complaint = models.TextField(blank=True, null=True)
    images = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=50, default='Hyderabad')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    summary_of_action_taken = models.TextField(blank=True, null=True)
    root_cause = models.TextField(blank=True, null=True)
    preventive_action = models.TextField(blank=True, null=True)
    parts_replaced_for_rectification = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} - {self.site_name} ({self.status}, {self.priority}, {self.location}, {self.claim_type})"

    def get_images(self):
        """Returns a list of image URLs."""
        if self.images:
            return json.loads(self.images)
        return []

    def generate_complaint_id(self):
        """Generates a unique Complaint ID based on company name, date, and time in IST timezone."""
        now = timezone.now()
        ist_tz = pytz.timezone('Asia/Kolkata')
        now = now.astimezone(ist_tz)
        date_str = now.strftime('%Y%m%d')
        time_str = now.strftime('%H%M')
        site_name = self.site_name.strip().replace(' ', '-') if self.site_name else 'UNKNOWN'
        
        base_id = f"{site_name}-{date_str}-{time_str}"

        # Check if the ID already exists and handle collisions
        count = 1
        unique_id = base_id
        while Complaint.objects.filter(complaint_id=unique_id).exists():
            unique_id = f"{base_id}-{count:04d}"
            count += 1

        return unique_id

    def save(self, *args, **kwargs):
        if not self.complaint_id:
            self.complaint_id = self.generate_complaint_id()
        super().save(*args, **kwargs)

    @staticmethod
    def extract_datetime_from_complaint_id(complaint_id):
        """Extract datetime from complaint_id"""
        try:
            parts = complaint_id.split('-')
            date_str = parts[-2]
            time_str = parts[-1]
            return datetime.strptime(date_str + time_str, '%Y%m%d%H%M')
        except (ValueError, IndexError):
            return None

    @classmethod
    def order_by_complaint_datetime(cls, status):
        return cls.objects.filter(status=status).order_by('-created_at')
