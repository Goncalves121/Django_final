from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class _EstiloMixin:
    """Aplica a classe CSS do tema em todos os campos."""

    def _estilizar(self):
        for campo in self.fields.values():
            campo.widget.attrs.setdefault('class', 'input')


class LoginForm(_EstiloMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuário'
        self.fields['username'].widget.attrs.update({'autofocus': True, 'placeholder': 'Seu usuário'})
        self.fields['password'].widget.attrs.update({'placeholder': 'Sua senha'})
        self._estilizar()


class CadastroForm(_EstiloMixin, UserCreationForm):
    email = forms.EmailField(label="E-mail", required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {'username': 'Nome de usuário'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estilizar()

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')
        return email


class PerfilForm(_EstiloMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {'first_name': 'Nome', 'last_name': 'Sobrenome', 'email': 'E-mail'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].widget.attrs['placeholder'] = 'Digite seu nome'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Digite seu sobrenome'
        self._estilizar()

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este e-mail já está em uso.')
        return email
