from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def qs(context, **novos):
    """Monta a query string atual trocando/removendo os parâmetros informados.

    {% qs categoria=c.id %}  -> ?busca=x&categoria=3
    {% qs categoria='' %}    -> remove o filtro de categoria
    """
    params = context["request"].GET.copy()
    for chave, valor in novos.items():
        if valor in (None, ""):
            params.pop(chave, None)
        else:
            params[chave] = valor
    texto = params.urlencode()
    return f"?{texto}" if texto else "?"
