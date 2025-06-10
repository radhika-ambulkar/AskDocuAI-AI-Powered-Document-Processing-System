from django.db import models
from django.contrib.auth.models import User


class Recommendation(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        app_label = 'Recommendationsystem'

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recommendation')  # Prevent duplicate ratings
	 

class ExtractedText(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    document_name = models.CharField(max_length=255)
    text = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
