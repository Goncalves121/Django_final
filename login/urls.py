from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.LoginPersonalizado.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("cadastro/", views.cadastro, name="cadastro"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("perfil/", views.perfil, name="perfil"),
    path("alterar-senha/", views.alterar_senha, name="alterar_senha"),

    # Recuperação de senha: mecanismo nativo do Django
    path("esqueceu-senha/", auth_views.PasswordResetView.as_view(
        template_name="password_reset.html",
        email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
        success_url=reverse_lazy("password_reset_done"),
    ), name="password_reset"),
    path("esqueceu-senha/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="password_reset_done.html"), name="password_reset_done"),
    path("redefinir/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="password_reset_confirm.html",
        success_url=reverse_lazy("password_reset_complete"),
    ), name="password_reset_confirm"),
    path("redefinir/concluido/", auth_views.PasswordResetCompleteView.as_view(
        template_name="password_reset_complete.html"), name="password_reset_complete"),
]
