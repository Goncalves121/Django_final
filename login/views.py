from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import CadastroForm, LoginForm, PerfilForm
from .models import Perfil, eh_administrador


class LoginPersonalizado(LoginView):
    """Admin vai direto para o painel do Django; cliente vai para a Dashboard."""
    template_name = "login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        destino = self.get_redirect_url()
        if destino:
            return destino
        if eh_administrador(self.request.user) and self.request.user.is_staff:
            return reverse("admin:index")
        return reverse("dashboard")


@login_required
def dashboard(request):
    if eh_administrador(request.user) and request.user.is_staff:
        return redirect("admin:index")
    return render(request, "dashboard.html")


@login_required
def perfil(request):
    form = PerfilForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Dados atualizados com sucesso.")
        return redirect("perfil")
    return render(request, "perfil.html", {"form": form})


@login_required
def alterar_senha(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    for campo in form.fields.values():
        campo.widget.attrs.setdefault("class", "input")
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        update_session_auth_hash(request, usuario)  # mantém a sessão ativa
        messages.success(request, "Senha alterada com sucesso.")
        return redirect("perfil")
    return render(request, "alterar_senha.html", {"form": form})


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        Perfil.objects.get_or_create(usuario=usuario, defaults={"tipo_usuario": "cliente"})
        messages.success(request, "Conta criada! Entre com seu usuário e senha.")
        return redirect("login")
    return render(request, "cadastro.html", {"form": form})
