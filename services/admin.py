from django.contrib import admin
from .models import complaint

# Register your models here.

class Com_(admin.ModelAdmin):
    list_display = ['user','comType','status']

admin.site.register(complaint,Com_)
