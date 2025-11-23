from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from api.views import PullRequestViewSet, TeamViewSet, UserViewSet

router = routers.DefaultRouter()
router.register(r"team", TeamViewSet)
router.register(r"users", UserViewSet)
router.register(r"pullRequests", PullRequestViewSet)
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]
