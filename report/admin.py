from django.contrib import admin
from .models import ChecklistItem, ChecklistResponse, ChecklistResponseItem

admin.site.register(ChecklistItem)
admin.site.register(ChecklistResponse)
admin.site.register(ChecklistResponseItem)



