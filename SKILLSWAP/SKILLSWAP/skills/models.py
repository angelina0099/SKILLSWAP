from django.db import models
from django.contrib.auth.models import User

class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('programming', 'Programming'),
        ('design', 'Design'),
        ('music', 'Music'),
        ('cooking', 'Cooking'),
        ('tutoring', 'Tutoring'),
        ('crafts', 'Crafts'),
        ('language', 'Language'),
        ('other', 'Other'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ExchangeRequest(models.Model):
    STATUS = (
        ('pending', 'pending'),
        ('accepted', 'accepted'),
        ('completed', 'completed'),
        ('refused', 'refused')
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"ExchangeRequest({self.sender} → {self.receiver} on {self.skill})"


class Report(models.Model):
    STATUS = (
        ('pending', 'pending'),
        ('reviewed', 'reviewed'),
        ('dismissed', 'dismissed'),
    )

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='reports')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report({self.reporter} on {self.skill} - {self.status})"