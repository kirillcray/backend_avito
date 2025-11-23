import random

from rest_framework import serializers

from .models import PullRequest, Team, User


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_id", "username", "is_active"]
        extra_kwargs = {
            "user_id": {"validators": []}  # отключаем проверку unique
        }


class TeamSerializer(serializers.ModelSerializer):
    members = TeamMemberSerializer(many=True, required=False)
    team_name = serializers.CharField(source="name")

    class Meta:
        model = Team
        fields = ["team_name", "members"]

    def create(self, validated_data):

        members_data = validated_data.pop("members", [])

        team = Team.objects.create(**validated_data)
        for member_data in members_data:
            user, _ = User.objects.update_or_create(
                user_id=member_data["user_id"],
                defaults={
                    "username": member_data["username"],
                    "is_active": member_data.get("is_active", True),
                    "team": team,
                },
            )

        return team


class UserSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)

    class Meta:
        model = User
        fields = ["user_id", "username", "is_active", "team_name"]


class PullRequestShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = PullRequest
        fields = [
            "pull_request_id",
            "pull_request_name",
            "author_id",
            "status",
        ]


class PullRequestSerializer(serializers.ModelSerializer):
    author_id = serializers.CharField()
    assigned_reviewers = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PullRequest
        fields = [
            "pull_request_id",
            "pull_request_name",
            "author_id",
            "status",
            "assigned_reviewers",
            "created_at",
            "merged_at",
        ]

    def get_assigned_reviewers(self, obj):
        return [user.user_id for user in obj.reviewers.all()]

    def validate(self, attrs):
        author_id = attrs["author_id"]
        pr_id = attrs.get("pull_request_id")

        # проверка автора
        if not User.objects.filter(user_id=author_id).exists():
            raise serializers.ValidationError(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "author not found",
                    }
                }
            )

        # проверка уникальности PR
        if PullRequest.objects.filter(pull_request_id=pr_id).exists():
            raise serializers.ValidationError(
                {
                    "error": {
                        "code": "PR_EXISTS",
                        "message": "PR id already exists",
                    }
                }
            )

        return super().validate(attrs)

    def create(self, validated_data):
        author_id = validated_data.pop("author_id")
        author = User.objects.get(user_id=author_id)

        reviewers = self.assign_reviewers(author.team, author_id)
        pr = PullRequest.objects.create(author=author, **validated_data)
        pr.reviewers.set(reviewers)
        return pr

    def assign_reviewers(self, team, author_id, ex_reviewers=None):
        reviewers = list(
            User.objects.filter(team=team, is_active=True)
            .exclude(user_id=author_id)
            .exclude(user_id__in=ex_reviewers or [])
        )
        print(reviewers)
        return random.sample(reviewers, min(2, len(reviewers)))

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["author_id"] = instance.author.user_id  # перезаписываем значение
        return rep
