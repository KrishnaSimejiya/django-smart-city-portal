from django.contrib import admin
from .models import registration

# Register your models here.

class Reg_(admin.ModelAdmin):
    list_display = ['id','name','email']

admin.site.register(registration,Reg_)