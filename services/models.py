from django.db import models
from accounts.models import registration 
from workers.models import wregistration

# Create your models here.
class complaint(models.Model):
    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        ACTIVE = 'ACTIVE', 'Active'
        RESOLVED = 'RESOLVED', 'Resolved'

    user = models.ForeignKey(registration, on_delete=models.CASCADE, null=True, blank=True)
    location = models.CharField(max_length=50)
    comType = models.TextField()
    description = models.TextField(max_length=100)
    image = models.ImageField(upload_to='complaint_image/')
    datetime = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)

    def __str__(self):
        return f"{self.comType} by {self.user}"


class WorkAssignment(models.Model):
    complaint = models.ForeignKey(complaint, on_delete=models.CASCADE, related_name='assignments')
    worker = models.ForeignKey(wregistration, on_delete=models.CASCADE, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return f"Assignment c#{self.complaint_id} -> {self.worker.name}"

    