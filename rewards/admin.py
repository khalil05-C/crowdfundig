from django.contrib import admin
from .models import Reward

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "reward_type", "minimum_amount", "quantity_available", "is_active")
    list_filter = ("is_active", "reward_type")
    search_fields = ("title", "project__title")
