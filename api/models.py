from django.db import models


class User(models.Model):
    user_id = models.CharField(max_length=100, primary_key=True)
    username = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    team = models.ForeignKey(
        "Team",
        on_delete=models.CASCADE,
        related_name="members",
    )

    def __str__(self):
        return self.username


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class PullRequest(models.Model):
    pull_request_id = models.CharField(max_length=100, primary_key=True)

    STATUS_CHOICES = [("OPEN", "Open"), ("MERGED", "Merged")]
    pull_request_name = models.CharField(max_length=200)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="authored_prs"
    )
    reviewers = models.ManyToManyField(
        User, related_name="assigned_prs", blank=True
    )
    status = models.CharField(
        max_length=6, choices=STATUS_CHOICES, default="OPEN"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    merged_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title
