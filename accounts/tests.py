from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from accounts.models import User
from accounts.views import get_user_badges
from pledges.models import Pledge
from projects.models import Category, Project

class UserModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username   = 'test@test.com',
            email      = 'test@test.com',
            password   = 'TestPass123',
            first_name = 'Test',
            last_name  = 'User',
            role       = 'contributor'
        )

    def test_user_creation(self):
        """Test que l'utilisateur est bien créé"""
        self.assertEqual(self.user.email, 'test@test.com')
        self.assertEqual(self.user.role, 'contributor')

    def test_user_str(self):
        """Test la représentation string"""
        self.assertIn('test@test.com', str(self.user))

    def test_login(self):
        """Test la connexion par email"""
        from django.contrib.auth import authenticate
        # Tester directement le backend
        user = authenticate(
            request  = None,
            username = 'test@test.com',
            password = 'TestPass123'
        )
        # Vérifier que l'authentification fonctionne
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@test.com')

    def test_register(self):
        """Test l'inscription"""
        client = Client()
        response = client.post('/accounts/register/', {
            'first_name': 'Khalil',
            'last_name' : 'Test',
            'email'     : 'khalil@test.com',
            'password1' : 'TestPass123!',
            'password2' : 'TestPass123!',
            'role'      : 'contributor',
            'terms'     : 'on'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            User.objects.filter(email='khalil@test.com').exists()
        )

    def test_wrong_password(self):
        """Test connexion avec mauvais mot de passe"""
        from django.contrib.auth import authenticate
        user = authenticate(
            request  = None,
            username = 'test@test.com',
            password = 'MauvaisMotDePasse'
        )
        self.assertIsNone(user)

    def test_user_role_contributor(self):
        """Test que le rôle par défaut est contributeur"""
        self.assertEqual(self.user.role, 'contributor')

    def test_user_is_active(self):
        """Test que l'utilisateur est actif"""
        self.assertTrue(self.user.is_active)

    def test_badge_is_kept_after_smaller_later_contribution(self):
        """Test qu'un badge gagne reste acquis apres une contribution plus petite."""
        owner = User.objects.create_user(
            username="owner_badge@test.com",
            email="owner_badge@test.com",
            password="TestPass123",
            role="project_owner",
        )
        category = Category.objects.create(name="Badge", slug="badge-retention")
        project = Project.objects.create(
            title="Projet badge",
            slug="projet-badge-retention",
            short_description="Description courte",
            description="Description complete",
            owner=owner,
            category=category,
            goal_amount=Decimal("10000.00"),
            end_date=timezone.now() + timedelta(days=30),
            status=Project.Status.ACTIVE,
        )

        Pledge.objects.create(
            backer=self.user,
            project=project,
            amount=Decimal("200.00"),
            status=Pledge.Status.COMPLETED,
        )
        small_pledge = Pledge.objects.create(
            backer=self.user,
            project=project,
            amount=Decimal("50.00"),
            status=Pledge.Status.COMPLETED,
        )

        badges = get_user_badges(self.user)

        self.assertIsNone(small_pledge.reward)
        self.assertIn("Bronze Supporter", [badge.title for badge in badges])
