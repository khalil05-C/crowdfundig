from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from accounts.models import User
from projects.models import Project, Category
from pledges.models import Pledge

class PledgeModelTest(TestCase):

    def setUp(self):
        # Créer utilisateurs
        self.owner = User.objects.create_user(
            username   = 'owner@test.com',
            email      = 'owner@test.com',
            password   = 'TestPass123',
            role       = 'project_owner'
        )
        self.backer = User.objects.create_user(
            username   = 'backer@test.com',
            email      = 'backer@test.com',
            password   = 'TestPass123',
            role       = 'contributor'
        )
        # Créer catégorie
        self.category = Category.objects.create(
            name = 'Tech', slug = 'tech'
        )
        # Créer projet
        self.project = Project.objects.create(
            title             = 'Projet Test',
            slug              = 'projet-test',
            short_description = 'Description courte',
            description       = 'Description complète',
            owner             = self.owner,
            category          = self.category,
            goal_amount       = 10000,
            current_amount    = 0,
            end_date          = timezone.now() + timedelta(days=30),
            status            = 'active'
        )

    def test_pledge_creation(self):
        """Test création d'une contribution"""
        pledge = Pledge.objects.create(
            backer   = self.backer,
            project  = self.project,
            amount   = 500,
            status   = 'completed'
        )
        self.assertEqual(pledge.amount, 500)
        self.assertEqual(pledge.status, 'completed')

    def test_pledge_complete_payment(self):
        """Test que le montant du projet est mis à jour"""
        pledge = Pledge.objects.create(
            backer  = self.backer,
            project = self.project,
            amount  = 1000,
            status  = 'pending'
        )
        pledge.complete_payment('TEST_ID_123')
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_amount, 1000)
        self.assertEqual(self.project.backers_count, 1)

    def test_pledge_anonymous(self):
        """Test contribution anonyme"""
        pledge = Pledge.objects.create(
            backer       = self.backer,
            project      = self.project,
            amount       = 200,
            is_anonymous = True,
            status       = 'completed'
        )
        self.assertTrue(pledge.is_anonymous)

    def test_pledge_str(self):
        """Test représentation string"""
        pledge = Pledge.objects.create(
            backer  = self.backer,
            project = self.project,
            amount  = 300,
            status  = 'completed'
        )
        self.assertIn('300', str(pledge))

    def test_multiple_pledges(self):
        """Test plusieurs contributions sur un projet"""
        Pledge.objects.create(
            backer=self.backer, project=self.project,
            amount=500, status='pending'
        ).complete_payment('ID_1')

        Pledge.objects.create(
            backer=self.backer, project=self.project,
            amount=300, status='pending'
        ).complete_payment('ID_2')

        self.project.refresh_from_db()
        self.assertEqual(self.project.current_amount, 800)
        self.assertEqual(self.project.backers_count, 2)

    def test_project_progress(self):
        """Test progression du projet après contributions"""
        Pledge.objects.create(
            backer=self.backer, project=self.project,
            amount=5000, status='pending'
        ).complete_payment('ID_3')

        self.project.refresh_from_db()
        self.assertEqual(self.project.progress_percent, 50)

    def test_commission_for_100_dh(self):
        """Test qu'une contribution de 100 DH genere 1 DH de commission."""
        pledge = Pledge.objects.create(
            backer=self.backer,
            project=self.project,
            amount=Decimal("100.00"),
            status=Pledge.Status.PENDING,
        )

        self.assertEqual(pledge.gross_amount, Decimal("100.00"))
        self.assertEqual(pledge.platform_commission_amount, Decimal("1.00"))
        self.assertEqual(pledge.project_net_amount, Decimal("99.00"))

    def test_commission_for_250_dh(self):
        """Test qu'une contribution de 250 DH genere 2.50 DH de commission."""
        pledge = Pledge.objects.create(
            backer=self.backer,
            project=self.project,
            amount=Decimal("250.00"),
            status=Pledge.Status.PENDING,
        )

        self.assertEqual(pledge.platform_commission_amount, Decimal("2.50"))
        self.assertEqual(pledge.project_net_amount, Decimal("247.50"))

    def test_project_total_uses_gross_amount_consistently(self):
        """Test que current_amount conserve le brut pour la progression du projet."""
        Pledge.objects.create(
            backer=self.backer,
            project=self.project,
            amount=Decimal("100.00"),
            status=Pledge.Status.PENDING,
        ).complete_payment("GROSS_1")

        self.project.refresh_from_db()
        pledge = self.project.pledges.get(payment_id="GROSS_1")

        self.assertEqual(self.project.current_amount, Decimal("100.00"))
        self.assertEqual(pledge.project_net_amount, Decimal("99.00"))
