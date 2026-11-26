import requests
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Min, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import supabase_client as sb
from .forms import FormContato, FormServico
from .models import Categoria, Contato, Pedido, Servico

API_PRODUTOS = "https://fakestoreapi.com/products"


# ----------------------------------------------------------------------------
# Páginas públicas
# ----------------------------------------------------------------------------
def saude(request):
    """Rota leve para monitores de uptime (não acessa banco nem APIs)."""
    return HttpResponse("ok")


def index(request):
    return render(request, "index.html")


def quem_somos(request):
    """Integrantes vêm do banco remoto (Supabase)."""
    integrantes, erro = [], None
    try:
        integrantes = sb.listar_integrantes()
    except Exception:
        erro = "Não foi possível carregar a equipe agora. Tente novamente em instantes."
    return render(request, "quem-somos.html", {"integrantes": integrantes, "erro": erro})


def produtos(request):
    produtos_api = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    try:
        resp = requests.get("https://fakestoreapi.com/products", headers=headers, timeout=8)
        resp.raise_for_status()
        produtos_api = resp.json()
    except Exception:
        # Fallback usando DummyJSON (não bloqueia IPs do Render) adaptado ao formato da FakeStoreAPI
        try:
            resp_alt = requests.get("https://dummyjson.com/products?limit=8", timeout=8)
            resp_alt.raise_for_status()
            dados = resp_alt.json().get("products", [])
            produtos_api = [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "price": item["price"],
                    "description": item["description"],
                    "category": item["category"],
                    "image": item["thumbnail"],
                }
                for item in dados
            ]
        except Exception:
            produtos_api = []

    # ... mantenha aqui o restante da sua view (consulta de Servico, etc.)


def add_contato(request):
    """Formulário aberto a visitantes: não exige login."""
    form = FormContato(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Mensagem enviada! Em breve entraremos em contato.")
        return redirect("add_contato")
    return render(request, "add-contato.html", {"form": form})


# ----------------------------------------------------------------------------
# Compras (somente usuários logados)
# ----------------------------------------------------------------------------
@require_POST
def comprar(request, id_servico):
    if not request.user.is_authenticated:
        messages.info(request, "Entre na sua conta para comprar.")
        return redirect(f"{reverse('login')}?next={reverse('produtos')}")

    servico = get_object_or_404(Servico, id=id_servico, ativo=True, preco__gt=0)
    Pedido.objects.create(
        usuario=request.user,
        servico=servico,
        nome=servico.nome,
        descricao=servico.descricao,
        preco=servico.preco,
    )
    messages.success(request, f"“{servico.nome}” foi adicionado aos seus pedidos.")
    return redirect("produtos")


@login_required
def meus_pedidos(request):
    pedidos = request.user.pedidos.select_related("servico")
    total = pedidos.aggregate(total=Sum("preco"))["total"] or 0
    return render(request, "meus-pedidos.html", {"pedidos": pedidos, "total": total})


# ----------------------------------------------------------------------------
# Serviços (CRUD + filtros + estatísticas)
# ----------------------------------------------------------------------------
@login_required
def servicos(request):
    todos = Servico.objects.all()
    estatisticas = todos.aggregate(total=Count("id"), menor=Min("preco"), maior=Max("preco"))
    ativos = todos.filter(ativo=True).count()

    lista = todos.select_related("categoria")

    busca = request.GET.get("busca", "").strip()
    if busca:
        lista = lista.filter(nome__icontains=busca)

    categoria = request.GET.get("categoria")
    if categoria and categoria.isdigit():
        lista = lista.filter(categoria_id=categoria)

    preco = request.GET.get("preco")
    if preco == "baixo":
        lista = lista.filter(preco__lte=500)
    elif preco == "medio":
        lista = lista.filter(preco__gt=500, preco__lte=1500)
    elif preco == "alto":
        lista = lista.filter(preco__gt=1500)

    ordem = request.GET.get("ordem")
    ordenacoes = {"menor": "preco", "maior": "-preco", "nome": "nome"}
    lista = lista.order_by(ordenacoes.get(ordem, "nome"))

    return render(request, "servicos.html", {
        "servicos": lista,
        "total_servicos": estatisticas["total"],
        "mais_barato": estatisticas["menor"],
        "mais_caro": estatisticas["maior"],
        "ativos": ativos,
        "inativos": estatisticas["total"] - ativos,
        "categorias": Categoria.objects.filter(ativo=True),
        "busca": busca,
        "categoria": categoria,
        "preco": preco,
        "ordem": ordem,
        "filtrado": bool(busca or categoria or preco or ordem),
    })


@login_required
def addServicos(request):
    form = FormServico(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Serviço cadastrado.")
        return redirect("servicos")
    return render(request, "form-servico.html", {"form": form, "modo": "novo"})


@login_required
def editServicos(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    form = FormServico(request.POST or None, request.FILES or None, instance=servico)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Serviço atualizado.")
        return redirect("servicos")
    return render(request, "form-servico.html", {"form": form, "modo": "editar", "servico": servico})


@login_required
@require_POST
def delServicos(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    servico.delete()
    messages.success(request, "Serviço excluído.")
    return redirect("servicos")


# ----------------------------------------------------------------------------
# Contatos recebidos
# ----------------------------------------------------------------------------
@login_required
def contatos(request):
    lista = Contato.objects.order_by("-id")
    return render(request, "contatos.html", {"contatos": lista, "total": lista.count()})


@login_required
@require_POST
def del_contato(request, id_contato):
    get_object_or_404(Contato, id=id_contato).delete()
    messages.success(request, "Contato excluído.")
    return redirect("contatos")


# ----------------------------------------------------------------------------
# Equipe (Supabase)
# ----------------------------------------------------------------------------
def _dados_integrante(post):
    return {
        "nome": post.get("nome", "").strip(),
        "cargo": post.get("cargo", "").strip(),
        "biografia": post.get("biografia", "").strip(),
        "foto_url": post.get("foto", "").strip(),
    }


@login_required
def integrantes(request):
    lista, erro = [], None
    try:
        lista = sb.listar_integrantes()
    except Exception:
        erro = "Não foi possível conectar ao Supabase. Confira o arquivo .env e sua conexão."
    return render(request, "integrantes.html", {"integrantes": lista, "erro": erro})


@login_required
def addIntegrante(request):
    dados = {}
    if request.method == "POST":
        dados = _dados_integrante(request.POST)
        if not dados["nome"] or not dados["cargo"]:
            messages.error(request, "Informe pelo menos o nome e o cargo.")
        else:
            try:
                sb.criar_integrante(dados)
                messages.success(request, "Integrante cadastrado.")
                return redirect("integrantes")
            except Exception:
                messages.error(request, "Não foi possível salvar no Supabase.")
    return render(request, "form-integrante.html", {"modo": "novo", "integrante": dados})


@login_required
def editIntegrante(request, id_integrante):
    try:
        integrante = sb.obter_integrante(id_integrante)
    except Exception:
        messages.error(request, "Não foi possível conectar ao Supabase.")
        return redirect("integrantes")
    if not integrante:
        messages.error(request, "Integrante não encontrado.")
        return redirect("integrantes")

    if request.method == "POST":
        dados = _dados_integrante(request.POST)
        if not dados["nome"] or not dados["cargo"]:
            messages.error(request, "Informe pelo menos o nome e o cargo.")
            integrante = {**integrante, **dados}
        else:
            try:
                sb.atualizar_integrante(id_integrante, dados)
                messages.success(request, "Integrante atualizado.")
                return redirect("integrantes")
            except Exception:
                messages.error(request, "Não foi possível salvar no Supabase.")
                integrante = {**integrante, **dados}
    return render(request, "form-integrante.html", {"modo": "editar", "integrante": integrante})


@login_required
@require_POST
def delIntegrante(request, id_integrante):
    try:
        sb.excluir_integrante(id_integrante)
        messages.success(request, "Integrante excluído.")
    except Exception:
        messages.error(request, "Não foi possível excluir no Supabase.")
    return redirect("integrantes")


# ----------------------------------------------------------------------------
# Relatórios
# ----------------------------------------------------------------------------
@login_required
def relatorios(request):
    todos = Servico.objects.all()
    ativos = todos.filter(ativo=True).count()
    inativos = todos.filter(ativo=False).count()
    por_categoria = todos.values("categoria__nome").annotate(quantidade=Count("id")).order_by("-quantidade")

    return render(request, "relatorio.html", {
        "total": ativos + inativos,
        "servicos_ativos": ativos,
        "servicos_inativos": inativos,
        "categorias_labels": [i["categoria__nome"] or "Sem categoria" for i in por_categoria],
        "categorias_valores": [i["quantidade"] for i in por_categoria],
    })
