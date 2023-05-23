from django.urls import path, re_path

from . import views

urlpatterns = [
    re_path(r"^Users", views.ScimService.as_view()),
    path('token/', views.get_scim_token),
]
