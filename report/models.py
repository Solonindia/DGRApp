from datetime import date
from django.db import models

class ChecklistItem(models.Model):
    FREQUENCY_CHOICES = [
        (1, 'Daily'),
        (2, 'Weekly'),
        (3, 'Monthly'),
        (4, 'Quarterly'),
        (5, 'Half Yearly'),
        (6, 'Annually'),
    ]


    REPORT_CHOICES = [
        ('Module Mounting Structure (MMS)', 'MMS'),
        ('Solar PV (SPV)', 'SPV'),
        ('String Cable', 'String Cable'),
        ('String Monitoring Box (SMB)', 'SMB'),
        ('Module Cleaning System (MCS)', 'MCS'),
        ('Power/HT Cables AC (ACPC)', 'ACPC'),
        ('LT Cables AC (LTC)', 'LTC'),
        ('Inverter (INV)', 'INV'),
        ('Transformer (TRAFO)', 'TRAFO'),
        ('VCB', 'VCB'),
        ('HT Panel (HTP)', 'HTP'),
        ('LT Panel (LTP)', 'LTP'),
        ('UPS', 'UPS'),
        ('Battery Charger', 'Battery Charger'),
        ('Battery Bank', 'Battery Bank'),
        ('Street Light', 'Street Light'),
        ('Lightning Arrester (LA)', 'LA'),
        ('Earthpit (EP)', 'EP'),
        ('Fire & Safety System (FSS)', 'FSS'),
        ('Metering Yard', 'Metering Yard'),
        ('OH Line (OHL)', 'OHL'),
        ('Bay Extension (BE)', 'BE'),
        ('House Keeping', 'House Keeping'),
    ]

    report_type = models.CharField(max_length=50, choices=REPORT_CHOICES)
    checkpoint = models.TextField()
    frequency_level = models.IntegerField(choices=FREQUENCY_CHOICES, default=6)  # Use this only
    Date = models.DateField(default=date.today, null=True, blank=True)  # Added Date field

    def save(self, *args, **kwargs):
        # Update the Date field to the current date if it's being updated
        if not self.Date:
            self.Date = date.today()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.report_type} - {self.checkpoint}"


from django.core.validators import FileExtensionValidator

class ChecklistResponse(models.Model):
    report_type = models.CharField(max_length=50)
    project_name = models.CharField(max_length=100)
    project_location = models.CharField(max_length=100)
    date_of_submission = models.DateField(auto_now_add=True)
    inspection_date = models.DateField(null=True, blank=True)
    next_inspection_date = models.DateField(null=True, blank=True)
    make =  models.CharField(max_length=20,null=True, blank=True)
    Type =  models.CharField(max_length=20,null=True, blank=True)
    s_no =  models.CharField(max_length=10,null=True, blank=True)
    rating =  models.CharField(max_length=20,null=True, blank=True)
    is_draft = models.BooleanField(default=True,null=True, blank=True)

    PERIOD_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Half Yearly', 'Half Yearly'),
        ('Annually', 'Annually'),
    ]
    period_of_inspection = models.CharField(max_length=50, choices=PERIOD_CHOICES)

    image1 = models.ImageField(upload_to='uploads/', null=True, blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    image2 = models.ImageField(upload_to='uploads/', null=True, blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    image3 = models.ImageField(upload_to='uploads/', null=True, blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    image4 = models.ImageField(upload_to='uploads/', null=True, blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    image5 = models.ImageField(upload_to='uploads/', null=True, blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    image6 = models.ImageField(upload_to='uploads/', null=True, blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])

    customer_name = models.CharField(max_length=30,null=True, blank=True)
    solon_name = models.CharField(max_length=30,null=True, blank=True)
    signature_pad_data = models.ImageField(upload_to='signatures/', null=True, blank=True)
    signature = models.ImageField(upload_to='uploads/', null=True, blank=True)
    signature_pad_data1 = models.ImageField(upload_to='signatures/', null=True, blank=True)
    signature1 = models.ImageField(upload_to='uploads/', null=True, blank=True)
    comments = models.TextField(max_length=500, blank=True, null=True)
    email_to = models.EmailField(blank=True, null=True)

    # sender_email = models.EmailField(max_length=100, null=True, blank=True)
    # receiver_email = models.EmailField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.report_type} - {self.project_name} ({self.date_of_submission})"


class ChecklistResponseItem(models.Model):
    response = models.ForeignKey(ChecklistResponse, on_delete=models.CASCADE)
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    remark = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.response.project_name} - {self.checklist_item.checkpoint[:30]} - {self.status}"

class ChecklistHistory(models.Model):
    checklist = models.ForeignKey(ChecklistResponse, on_delete=models.CASCADE)
    submitted_on = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='checklist_pdfs/')