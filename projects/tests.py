import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import User
from projects.models import Project, Category
from django.utils import timezone
from datetime import timedelta

class ProjectModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='TestPass123',
            role='project_owner'
        )
        self.category = Category.objects.create(
            name='Technologie', slug='tech'
        )
        self.project = Project.objects.create(
            title             = 'Projet Test',
            slug              = 'projet-test',
            short_description = 'Description courte',
            description       = 'Description complète',
            owner             = self.user,
            category          = self.category,
            goal_amount       = 10000,
            current_amount    = 5000,
            end_date          = timezone.now() + timedelta(days=30),
            status            = 'active'
        )

    def test_project_creation(self):
        """Test création projet"""
        self.assertEqual(self.project.title, 'Projet Test')
        self.assertEqual(self.project.status, 'active')

    def test_progress_percent(self):
        """Test calcul progression"""
        self.assertEqual(self.project.progress_percent, 50)

    def test_days_remaining(self):
        """Test jours restants"""
        self.assertGreater(self.project.days_remaining, 0)

    def test_project_str(self):
        """Test représentation string"""
        self.assertEqual(str(self.project), 'Projet Test')

    def test_video_embed_url_from_youtube_watch_url(self):
        self.project.video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(
            self.project.video_embed_url,
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        )

    def test_video_embed_url_from_short_youtube_url(self):
        self.project.video_url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertEqual(
            self.project.video_embed_url,
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        )

    def test_video_embed_url_from_youtube_shorts_url(self):
        self.project.video_url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        self.assertEqual(
            self.project.video_embed_url,
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        )

    def test_video_embed_url_keeps_embed_url(self):
        self.project.video_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        self.assertEqual(
            self.project.video_embed_url,
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        )


class ProjectAdminDeleteTest(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()

        self.owner = User.objects.create_user(
            username="owner-delete@test.com",
            email="owner-delete@test.com",
            password="TestPass123",
            role="project_owner",
        )
        self.admin = User.objects.create_user(
            username="admin-delete@test.com",
            email="admin-delete@test.com",
            password="TestPass123",
            role="admin",
            is_staff=True,
        )
        self.category = Category.objects.create(name="Admin delete", slug="admin-delete")

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def create_active_project(self, title="Projet approuve"):
        return Project.objects.create(
            title=title,
            slug=title.lower().replace(" ", "-"),
            short_description="Description courte",
            description="Description complete",
            owner=self.owner,
            category=self.category,
            goal_amount=10000,
            end_date=timezone.now() + timedelta(days=30),
            status=Project.Status.ACTIVE,
            cover_image=SimpleUploadedFile(
                "cover.jpg",
                b"fake image content",
                content_type="image/jpeg",
            ),
        )

    def test_admin_can_delete_active_project_and_cover_image(self):
        project = self.create_active_project()
        cover_path = Path(project.cover_image.path)
        self.assertTrue(cover_path.exists())

        self.client.force_login(self.admin)
        response = self.client.post(reverse("projects:project_delete", kwargs={"slug": project.slug}))

        self.assertRedirects(response, reverse("projects:project_list"))
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())
        self.assertFalse(cover_path.exists())

    def test_owner_cannot_delete_active_project(self):
        project = self.create_active_project("Projet protege")

        self.client.force_login(self.owner)
        response = self.client.post(reverse("projects:project_delete", kwargs={"slug": project.slug}))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
