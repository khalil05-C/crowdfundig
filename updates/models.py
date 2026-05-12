from django.db import models
from django.conf import settings

class ProjectUpdate(models.Model):
    project    = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='project_updates')
    author     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    title      = models.CharField(max_length=200)
    content    = models.TextField()
    is_public  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} – {self.project.title}"


class Comment(models.Model):
    project    = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='comments')
    parent     = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content    = models.TextField()
    is_hidden  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire de {self.author} sur {self.project.title}"