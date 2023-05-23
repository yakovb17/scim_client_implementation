import json

from django.db import models
from django.contrib.auth.models import User


class Employee(models.Model):
    # customer = models.ForeignKey(Customer, related_name="employees", on_delete=models.CASCADE)
    username = models.CharField(max_length=255)
    meta = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def serialize(self) -> dict:

        return {
            "id": self.id,
            "username": self.username,
            "meta": json.loads(self.meta),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
class RequestLogging(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    request_body = models.CharField(max_length=255)
    response_body = models.CharField(max_length=255)
    response_status_code = models.PositiveIntegerField()