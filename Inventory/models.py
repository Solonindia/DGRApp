from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# Model to store Site data
class Site(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


# Model to store Inventory data for each site
class Inventory(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    material_code = models.CharField(max_length=100)
    material_desc = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    uom = models.CharField(max_length=50,default="No's")
    opening_stock = models.IntegerField()
    fixed_stock = models.IntegerField(blank=True, null=True)
    unit_value = models.FloatField(default=0)
    
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Add this field



    def __str__(self):
        return f"{self.material_code} - {self.material_desc}"
    
    def save(self, *args, **kwargs):
        if self.fixed_stock is None:
            self.fixed_stock = self.opening_stock
        super().save(*args, **kwargs)


class Notification(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    material_code = models.CharField(max_length=100)
    material_desc = models.CharField(max_length=255,default=None)
    uom = models.CharField(max_length=50,default="No's")
    opening_stock = models.IntegerField(default=0)
    consumption = models.IntegerField(null=True, blank=True)
    closing_stock = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    unit_value = models.FloatField(default=0) 

    def __str__(self):
        return f"Notification for {self.material_code} at {self.timestamp}"


class RealTimeNotification(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    material_code = models.CharField(max_length=100)
    material_desc = models.CharField(max_length=255,default=None)
    uom = models.CharField(max_length=50,default="No's")
    opening_stock = models.IntegerField(default=0)
    consumption = models.IntegerField(null=True, blank=True)
    closing_stock = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False) 
    user = models.ForeignKey(User, on_delete=models.CASCADE)  

    def __str__(self):
        return f"Real-time Notification for {self.material_code} at {self.timestamp}"
