from django.contrib import admin
from .models import Category, Project

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ('title', 'owner', 'category', 'goal_amount', 'current_amount', 'status')
    list_filter   = ('status', 'category', 'funding_type')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}