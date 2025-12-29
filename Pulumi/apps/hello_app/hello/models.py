from django.db import models

# Create your models here.
class Aplicatie(models.Model):
    nume = models.CharField(max_length=100)
    link = models.URLField()
    
    def __str__(self):
        return f"{self.nume}"