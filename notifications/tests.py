from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.core import mail
from accounts.models import User
from pledges.models import Pledge
from projects.models import Project, Category
from notifications.models import Notification
from notifications.services import create_notification

class NotificationTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username = 'user@test.com',
            email    = 'user@test.com',
            password = 'TestPass123',
        )
        self.category = Category.objects.create(
            name='Tech', slug='tech'
        )
        self.project = Project.objects.create(
            title             = 'Projet Notif',
            slug              = 'projet-notif',
            short_description = 'Test',
            description       = 'Test',
            owner             = self.user,
            category          = self.category,
            goal_amount       = 5000,
            end_date          = timezone.now() + timedelta(days=30),
            status            = 'active'
        )

    def test_create_notification(self):
        """Test création notification"""
        notif = Notification.objects.create(
            recipient         = self.user,
            notification_type = 'pledge_received',
            title             = 'Test notif',
            message           = 'Message test',
        )
        self.assertEqual(notif.is_read, False)
        self.assertEqual(notif.recipient, self.user)

    def test_mark_as_read(self):
        """Test marquer comme lu"""
        notif = Notification.objects.create(
            recipient         = self.user,
            notification_type = 'project_approved',
            title             = 'Approuvé',
            message           = 'Votre projet est approuvé',
        )
        notif.mark_as_read()
        self.assertTrue(notif.is_read)

    def test_unread_count(self):
        """Test comptage non lus"""
        Notification.objects.create(
            recipient=self.user,
            notification_type='pledge_received',
            title='Test 1', message='Msg 1'
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type='project_funded',
            title='Test 2', message='Msg 2'
        )
        unread = self.user.notifications.filter(is_read=False).count()
        self.assertEqual(unread, 2)


class NotificationDeliveryTest(TestCase):
    """Tests for notification creation and delivery preferences."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_notif@test.com",
            email="owner_notif@test.com",
            password="TestPass123",
            role="project_owner",
            notification_preference="email",
        )
        self.backer = User.objects.create_user(
            username="backer_notif@test.com",
            email="backer_notif@test.com",
            password="TestPass123",
            role="contributor",
            phone="+212600000000",
            notification_preference="email",
        )
        self.category = Category.objects.create(name="Notif", slug="notif-tests")
        self.project = Project.objects.create(
            title="Projet notifications",
            slug="projet-notifications",
            short_description="Test",
            description="Test",
            owner=self.owner,
            category=self.category,
            goal_amount=Decimal("5000.00"),
            end_date=timezone.now() + timedelta(days=30),
            status=Project.Status.ACTIVE,
        )

    def test_notification_created_after_donation(self):
        """Test creation d'une notification apres donation."""
        self.client.force_login(self.backer)
        response = self.client.post(
            f"/pledges/create/{self.project.slug}/",
            {"amount": "200", "reward": "", "message": "", "is_anonymous": ""},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.backer,
                notification_type=Notification.Type.DONATION_CREATED,
            ).exists()
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_sent_when_preference_is_email(self):
        """Test qu'un email est envoye si la preference est email."""
        create_notification(
            recipient=self.backer,
            notification_type=Notification.Type.DONATION_CREATED,
            title="Donation creee",
            message="Votre donation est creee.",
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.backer.email])

    @patch("notifications.services.send_sms_notification")
    def test_sms_called_when_preference_is_phone(self, mocked_sms):
        """Test que la fonction SMS mockee est appelee si la preference est telephone."""
        self.backer.notification_preference = "phone"
        self.backer.save(update_fields=["notification_preference"])

        create_notification(
            recipient=self.backer,
            notification_type=Notification.Type.PAYMENT_CONFIRMED,
            title="Paiement confirme",
            message="Votre paiement est confirme.",
        )

        mocked_sms.assert_called_once_with(self.backer.phone, "Votre paiement est confirme.")

    def test_notification_marked_as_read(self):
        """Test qu'une notification peut etre marquee comme lue."""
        notification = Notification.objects.create(
            recipient=self.backer,
            notification_type=Notification.Type.PAYMENT_CONFIRMED,
            title="Paiement confirme",
            message="Votre paiement est confirme.",
        )
        self.client.force_login(self.backer)

        response = self.client.post(f"/notifications/mark-read/{notification.pk}/")
        notification.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(notification.is_read)
