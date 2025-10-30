from django.contrib import admin
from .models import wregistration

# Register your models here.

class Wor_(admin.ModelAdmin):
    list_display = ['name','email','mobileno','department']

admin.site.register(wregistration,Wor_)

