from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from pledges.models import Pledge
from projects.models import Category, Project

from .models import Reward


class RewardSelectionTest(TestCase):
    """Simple tests for automatic badges and physical reward stock."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="TestPass123",
            role="project_owner",
        )
        self.backer = User.objects.create_user(
            username="backer@example.com",
            email="backer@example.com",
            password="TestPass123",
            role="contributor",
        )
        self.category = Category.objects.create(name="Tech", slug="tech-rewards")
        self.project = Project.objects.create(
            title="Projet rewards",
            slug="projet-rewards",
            short_description="Description courte",
            description="Description complete",
            owner=self.owner,
            category=self.category,
            goal_amount=Decimal("10000.00"),
            end_date=timezone.now() + timedelta(days=30),
            status=Project.Status.ACTIVE,
        )

    def test_badge_is_assigned_by_amount(self):
        """A pledge of 500 MAD receives the Silver Supporter badge."""
        pledge = Pledge.objects.create(
            backer=self.backer,
            project=self.project,
            amount=Decimal("500.00"),
            status=Pledge.Status.PENDING,
        )

        self.assertIsNotNone(pledge.reward)
        self.assertEqual(pledge.reward.title, "Silver Supporter")
        self.assertEqual(pledge.reward.reward_type, Reward.RewardType.BADGE)

    def test_tshirt_is_available_from_1000_dh(self):
        """The official T-shirt is proposed only from 1000 MAD."""
        rewards_900 = Reward.available_for_amount(self.project, Decimal("900.00"))
        rewards_1000 = Reward.available_for_amount(self.project, Decimal("1000.00"))

        self.assertFalse(rewards_900.filter(title="T-shirt officiel").exists())
        self.assertTrue(rewards_1000.filter(title="T-shirt officiel").exists())

    def test_quantity_decreases_after_selection(self):
        """Selecting a limited reward decreases available quantity."""
        reward = Reward.objects.create(
            project=self.project,
            title="Pack limite",
            description="Reward avec stock limite.",
            minimum_amount=Decimal("200.00"),
            reward_type=Reward.RewardType.PHYSICAL,
            quantity_available=3,
        )

        Pledge.objects.create(
            backer=self.backer,
            project=self.project,
            amount=Decimal("200.00"),
            reward=reward,
            status=Pledge.Status.PENDING,
        )

        reward.refresh_from_db()
        self.assertEqual(reward.quantity_available, 2)
