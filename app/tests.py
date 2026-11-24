from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Contato, Pedido, Servico

INTEGRANTES = [
    {"id": 4, "nome": "Mariana", "cargo": "QA", "biografia": "Qualidade", "foto_url": "https://x/y.png"},
    {"id": 5, "nome": "Felipe", "cargo": "Desenvolvedor", "biografia": "Código", "foto_url": ""},
]
API = [{"id": 1, "title": "Mochila", "price": 109.95, "description": "desc", "category": "men", "image": "https://x/i.jpg"}]


class FakeResp:
    def raise_for_status(self): pass
    def json(self): return API


class Base(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Desenvolvimento")
        self.s1 = Servico.objects.create(nome="Site", preco=Decimal("2000"), categoria=self.cat)
        self.s2 = Servico.objects.create(nome="App", preco=Decimal("1000"), categoria=self.cat)
        self.s3 = Servico.objects.create(nome="Antigo", preco=Decimal("300"), ativo=False)
        self.cliente = User.objects.create_user("ana", "ana@x.com", "SenhaForte#123")
        self.admin = User.objects.create_superuser("admin", "a@x.com", "SenhaForte#123")


@patch("app.views.requests.get", return_value=FakeResp())
@patch("app.views.sb.listar_integrantes", return_value=INTEGRANTES)
class PaginasPublicas(Base):
    def test_publicas(self, *_):
        for nome in ["index", "quem_somos", "produtos", "add_contato", "login", "cadastro", "password_reset"]:
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)

    def test_quem_somos_mostra_equipe(self, *_):
        r = self.client.get(reverse("quem_somos"))
        self.assertContains(r, "Mariana"); self.assertContains(r, "Felipe")

    def test_produtos_local_e_api(self, *_):
        r = self.client.get(reverse("produtos"))
        self.assertContains(r, "Site"); self.assertContains(r, "Mochila")
        self.assertNotContains(r, "Antigo")  # inativo não aparece

    def test_quem_somos_sem_supabase_nao_quebra(self, *_):
        with patch("app.views.sb.listar_integrantes", side_effect=Exception("fora")):
            self.assertEqual(self.client.get(reverse("quem_somos")).status_code, 200)

    def test_produtos_api_fora_do_ar_nao_quebra(self, mock_sb, mock_get):
        import requests
        mock_get.side_effect = requests.ConnectionError()
        r = self.client.get(reverse("produtos"))
        self.assertEqual(r.status_code, 200); self.assertContains(r, "Site")

    def test_contato_sem_login(self, *_):
        r = self.client.post(reverse("add_contato"), {"nome": "Fe", "email": "f@x.com", "telefone": "1", "mensagem": "Oi"})
        self.assertRedirects(r, reverse("add_contato"))
        self.assertEqual(Contato.objects.count(), 1)


class Protecao(Base):
    def test_paginas_internas_exigem_login(self):
        for nome in ["contatos", "servicos", "addServicos", "integrantes", "addIntegrante", "relatorios", "meus_pedidos", "dashboard", "perfil"]:
            r = self.client.get(reverse(nome))
            self.assertEqual(r.status_code, 302, nome)
            self.assertIn("/login/", r["Location"], nome)

    def test_comprar_anonimo_vai_para_login(self):
        r = self.client.post(reverse("comprar", args=[self.s1.id]))
        self.assertIn("/login/", r["Location"])
        self.assertEqual(Pedido.objects.count(), 0)

    def test_exclusao_exige_post(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse("delServicos", args=[self.s1.id])).status_code, 405)


class Login(Base):
    def test_admin_vai_para_painel_admin(self):
        r = self.client.post(reverse("login"), {"username": "admin", "password": "SenhaForte#123"})
        self.assertRedirects(r, reverse("admin:index"), fetch_redirect_response=False)

    def test_cliente_vai_para_dashboard(self):
        r = self.client.post(reverse("login"), {"username": "ana", "password": "SenhaForte#123"})
        self.assertRedirects(r, reverse("dashboard"))

    def test_admin_na_dashboard_e_redirecionado(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse("dashboard")), reverse("admin:index"), fetch_redirect_response=False)

    def test_cadastro_cria_cliente(self):
        r = self.client.post(reverse("cadastro"), {"username": "novo", "email": "n@x.com", "password1": "SenhaForte#987", "password2": "SenhaForte#987"})
        self.assertRedirects(r, reverse("login"))
        self.assertEqual(User.objects.get(username="novo").perfil.tipo_usuario, "cliente")

    def test_recuperacao_de_senha_envia_email(self):
        from django.core import mail
        r = self.client.post(reverse("password_reset"), {"email": "ana@x.com"})
        self.assertRedirects(r, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/login/redefinir/", mail.outbox[0].body)

    def test_perfil_edita_e_senha_muda(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("perfil"), {"first_name": "Ana", "last_name": "Silva", "email": "ana2@x.com"})
        self.cliente.refresh_from_db(); self.assertEqual(self.cliente.email, "ana2@x.com")
        r = self.client.post(reverse("alterar_senha"), {"old_password": "SenhaForte#123", "new_password1": "OutraSenha#456", "new_password2": "OutraSenha#456"})
        self.assertRedirects(r, reverse("perfil"))
        self.cliente.refresh_from_db(); self.assertTrue(self.cliente.check_password("OutraSenha#456"))


class Compras(Base):
    def test_compra_e_meus_pedidos(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("comprar", args=[self.s1.id]))
        self.client.post(reverse("comprar", args=[self.s2.id]))
        r = self.client.get(reverse("meus_pedidos"))
        self.assertContains(r, "Site"); self.assertContains(r, "3.000,00")

    def test_nao_compra_servico_inativo(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.post(reverse("comprar", args=[self.s3.id])).status_code, 404)

    def test_excluir_servico_comprado_mantem_historico(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse("comprar", args=[self.s1.id]))
        self.client.post(reverse("delServicos", args=[self.s1.id]))
        self.assertEqual(Pedido.objects.get().nome, "Site")


class ServicosCrud(Base):
    def setUp(self):
        super().setUp(); self.client.force_login(self.cliente)

    def test_filtros(self):
        r = self.client.get(reverse("servicos"), {"preco": "alto"})
        self.assertContains(r, "Site"); self.assertNotContains(r, "<b>App</b>")
        r = self.client.get(reverse("servicos"), {"busca": "app"})
        self.assertContains(r, "<b>App</b>"); self.assertNotContains(r, "<b>Site</b>")
        r = self.client.get(reverse("servicos"), {"ordem": "maior"})
        self.assertLess(r.content.decode().index("<b>Site</b>"), r.content.decode().index("<b>App</b>"))

    def test_crud(self):
        r = self.client.post(reverse("addServicos"), {"nome": "Novo", "descricao": "d", "preco": "50", "ativo": "on"})
        self.assertRedirects(r, reverse("servicos"))
        s = Servico.objects.get(nome="Novo")
        self.client.post(reverse("editServicos", args=[s.id]), {"nome": "Novo2", "descricao": "d", "preco": "60"})
        s.refresh_from_db(); self.assertEqual((s.nome, s.ativo), ("Novo2", False))
        self.client.post(reverse("delServicos", args=[s.id]))
        self.assertFalse(Servico.objects.filter(id=s.id).exists())

    def test_relatorios_e_contatos(self):
        self.assertContains(self.client.get(reverse("relatorios")), "Relatórios de Serviços")
        Contato.objects.create(nome="Z", email="z@x.com", mensagem="m")
        c = Contato.objects.get()
        self.assertContains(self.client.get(reverse("contatos")), "Nossos Contatos")
        self.client.post(reverse("del_contato", args=[c.id]))
        self.assertEqual(Contato.objects.count(), 0)


class Equipe(Base):
    def setUp(self):
        super().setUp(); self.client.force_login(self.cliente)

    @patch("app.views.sb.listar_integrantes", return_value=INTEGRANTES)
    def test_lista(self, _):
        r = self.client.get(reverse("integrantes"))
        self.assertContains(r, "Mariana"); self.assertContains(r, "Total de integrantes cadastrados: <b>2</b>")

    @patch("app.views.sb.criar_integrante")
    def test_criar(self, mock):
        r = self.client.post(reverse("addIntegrante"), {"nome": "Ju", "cargo": "Dev", "biografia": "b", "foto": ""})
        self.assertRedirects(r, reverse("integrantes"))
        mock.assert_called_once_with({"nome": "Ju", "cargo": "Dev", "biografia": "b", "foto_url": ""})

    @patch("app.views.sb.atualizar_integrante")
    @patch("app.views.sb.obter_integrante", return_value=INTEGRANTES[0])
    def test_editar(self, _, mock_upd):
        self.assertContains(self.client.get(reverse("editIntegrante", args=[4])), "Mariana")
        r = self.client.post(reverse("editIntegrante", args=[4]), {"nome": "Mari", "cargo": "QA", "biografia": "", "foto": ""})
        self.assertRedirects(r, reverse("integrantes"))
        mock_upd.assert_called_once()

    @patch("app.views.sb.excluir_integrante")
    def test_excluir(self, mock):
        self.client.post(reverse("delIntegrante", args=[4])); mock.assert_called_once_with(4)
