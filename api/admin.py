from django.contrib import admin

from .models import PullRequest, Team, User


# Register your models here.
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "member_count")
    search_fields = ("name",)

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = "Members"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "username", "team", "is_active")
    list_filter = ("team", "is_active")
    search_fields = ("username", "user_id")
    list_editable = ("is_active",)


@admin.register(PullRequest)
class PullRequestAdmin(admin.ModelAdmin):
    list_display = (
        "pull_request_id",
        "pull_request_name",
        "author",
        "status",
        "created_at",
        "merged_at",
    )
    list_filter = ("status", "author", "reviewers")
    search_fields = (
        "pull_request_id",
        "pull_request_name",
        "author__username",
    )
    readonly_fields = ("created_at", "merged_at")
    filter_horizontal = ("reviewers",)
