from django.contrib import admin
from .models import Pledge

@admin.register(Pledge)
class PledgeAdmin(admin.ModelAdmin):
    list_display = (
        "backer",
        "project",
        "amount",
        "platform_commission_amount",
        "project_net_amount",
        "platform_commission_rate",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    readonly_fields = ("gross_amount", "platform_commission_amount", "project_net_amount", "platform_commission_rate")
