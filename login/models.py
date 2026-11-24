from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):

    TIPOS_USUARIO = [
        ('administrador', 'Administrador'),
        ('cliente', 'Cliente'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(max_length=20, choices=TIPOS_USUARIO, default='cliente')

    def __str__(self):
        return f'{self.usuario.username} - {self.tipo_usuario}'


def eh_administrador(user):
    """Administrador = superusuário ou perfil marcado como 'administrador'."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perfil = Perfil.objects.filter(usuario=user).first()
    return bool(perfil and perfil.tipo_usuario == 'administrador')
