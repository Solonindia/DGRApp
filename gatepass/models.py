from django.db import models

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

    def __str__(self):
        return f"Visitor: {self.visitor_name} - {self.name_of_plant}"
