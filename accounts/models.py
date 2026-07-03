from django.db import models
from django.contrib.auth.models import User


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, )
    active = models.BooleanField(default=False)
    expire_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username


# accounts/models.py

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.username


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    url = models.CharField(max_length=300,blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
