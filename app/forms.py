from django import forms
from .models import Contato, Servico


class FormServico(forms.ModelForm):
    ativo = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = Servico
        fields = ("nome", "descricao", "preco", "categoria", "imagem", "ativo")
        widgets = {"descricao": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            if nome not in ("ativo", "imagem"):
                campo.widget.attrs.setdefault("class", "input")
        self.fields["categoria"].queryset = self.fields["categoria"].queryset.filter(ativo=True)

    def clean_preco(self):
        preco = self.cleaned_data["preco"]
        if preco < 0:
            raise forms.ValidationError("O preço não pode ser negativo.")
        return preco


class FormContato(forms.ModelForm):
    class Meta:
        model = Contato
        fields = ("nome", "telefone", "email", "mensagem")
        widgets = {"mensagem": forms.Textarea(attrs={"rows": 6})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "input")
