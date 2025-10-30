from django.db import models

# Create your models here.

class registration(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    mobileno = models.CharField(max_length=10)
    address = models.TextField(default=" ")
    password = models.CharField(max_length=8,default=" ")
    image = models.ImageField(upload_to='profile_image/', default='default.jpg')

    def __str__(self):
        return self.name
    
#class login(models.Model):
#    email = models.EmailField()
#    password = models.CharField(max_length=8,min=4,default=" ")

#    def __str__(self):
#        return self.email

