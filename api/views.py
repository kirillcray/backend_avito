import random

from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PullRequest, Team, User
from .serializers import (
    PullRequestSerializer,
    PullRequestShortSerializer,
    TeamSerializer,
    UserSerializer,
)


class TeamViewSet(viewsets.GenericViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    @action(detail=False, methods=["post"], url_path="add")
    def add_team(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            team = serializer.save()
        except IntegrityError:
            return Response(
                {
                    "error": {
                        "code": "TEAM_EXISTS",
                        "message": "team_name already exists",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"team": self.get_serializer(team).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="get")
    def get_team(self, request):
        name = request.query_params.get("team_name")
        try:
            team = Team.objects.get(name=name)
        except Team.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "resource not found",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(team)
        return Response(serializer.data)


class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=["post"], url_path="setIsActive")
    def set_active(self, request):
        user_id = request.data.get("user_id")
        is_active = request.data.get("is_active")
        try:
            user = User.objects.get(user_id=user_id)
            user.is_active = is_active
            user.save()
            serializer = self.get_serializer(user)

            return Response(
                {"user": serializer.data}, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "resource not found",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"], url_path="getReview")
    def get_review(self, request):
        user_id = request.query_params.get("user_id")
        try:
            user = User.objects.get(user_id=user_id)
            user_prs = PullRequest.objects.filter(reviewers=user)
            serializer = PullRequestShortSerializer(user_prs, many=True)
            serializer.data.pop("assigned_reviewers", None)
            return Response(
                {"user_id": user_id, "pull_requests": serializer.data},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "resource not found",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )


class PullRequestViewSet(viewsets.GenericViewSet):
    queryset = PullRequest.objects.all()

    @action(detail=False, methods=["post"], url_path="create")
    def create_pull_request(self, request):

        serializer = PullRequestSerializer(data=request.data)
        serializer.is_valid()
        if PullRequest.objects.filter(
            pull_request_id=request.data.get("pull_request_id")
        ).exists():
            return Response(
                {
                    "error": {
                        "code": "PR_EXISTS",
                        "message": "PR id already exists",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        pull_request = serializer.save()
        data = PullRequestSerializer(pull_request).data
        data.pop("created_at", None)
        data.pop("merged_at", None)
        return Response(
            {"pr": data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="merged")
    def merge_pull_request(self, request):
        pr_id = request.data.get("pull_request_id")
        try:
            pr = PullRequest.objects.get(pull_request_id=pr_id)
            pr.status = "MERGED"
            pr.merged_at = timezone.now()
            pr.save()
            data = PullRequestSerializer(pr).data
            data.pop("created_at", None)

            return Response(
                {"pr": data},
                status=status.HTTP_200_OK,
            )
        except PullRequest.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "resource not found",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["post"], url_path="reassign")
    def reassign_reviewers(self, request):
        pr_id = request.data.get("pull_request_id")
        old_reviewer_id = request.data.get("old_reviewer_id")

        # Получаем PR или 404
        try:
            pr = get_object_or_404(PullRequest, pull_request_id=pr_id)
            old_reviewer = get_object_or_404(User, user_id=old_reviewer_id)
        except Http404:
            return Response(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "resource not found",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        # Проверка статуса
        if pr.status == "MERGED":
            return Response(
                {
                    "error": {
                        "code": "PR_MERGED",
                        "message": "cannot reassign on merged PR",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        if old_reviewer not in pr.reviewers.all():
            return Response(
                {
                    "error": {
                        "code": "NOT_ASSIGNED",
                        "message": "reviewer is not assigned to this PR",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        current_reviewers = list(pr.reviewers.all())
        excluded_ids = [pr.author.user_id] + [
            r.user_id for r in current_reviewers
        ]
        print(excluded_ids)
        current_reviewers.remove(old_reviewer)

        candidates = list(
            User.objects.filter(team=pr.author.team, is_active=True).exclude(
                user_id__in=excluded_ids
            )
        )
        if not candidates:
            return Response(
                {
                    "error": {
                        "code": "NO_CANDIDATE",
                        "message": "no active replacement candidate in team",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        new_reviewer = random.choice(candidates)
        # Добавляем нового ревьюера
        current_reviewers.append(new_reviewer)
        pr.reviewers.set(current_reviewers)

        data = PullRequestSerializer(pr).data
        data.pop("created_at", None)
        data.pop("merged_at", None)
        return Response(
            {
                "pr": data,
                "replaced_by": new_reviewer.user_id,
            },
            status=status.HTTP_200_OK,
        )
