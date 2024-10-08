"""
URL configuration for exako project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.http import Http404
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI

from exako.apps.card.api.routers import card_router
from exako.apps.term.api.routers.term import term_router
from exako.apps.user.auth.api import auth_router
from exako.apps.user.auth.exception import InvalidToken

api = NinjaAPI()

api.add_router('term/', term_router)
api.add_router('auth/', auth_router)
api.add_router('card/', card_router)

urlpatterns = (
    [
        path('admin/', admin.site.urls),
        path('api/', api.urls),
        path('', include('exako.apps.term.urls')),
        path('cardset/', include('exako.apps.card.urls')),
        path('auth/', include('exako.apps.user.urls')),
        path('exercise/', include('exako.apps.exercise.urls')),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)


@api.exception_handler(InvalidToken)
def invalid_token(request, exc):
    return api.create_response(
        request,
        {'detail': 'could not validate credentials.'},
        status=401,
    )


@api.exception_handler(Http404)
def object_does_not_exists(request, exc):
    return api.create_response(request, {'detail': exc.args[0]}, status=404)
