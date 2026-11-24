# Projeto Django — WEB III

## Atualizando seu projeto
1. Extraia este .zip **por cima** da sua pasta `django/` (ele não traz `db.sqlite3`, `.env` nem `media/`, então seus dados ficam intactos).
2. `pip install -r requirements.txt`
3. `python manage.py migrate`   ← cria a tabela de Pedidos
4. `python manage.py runserver`

## Mapa do PDF → código
| Requisito | Onde |
|---|---|
| Home, menu (Quem Somos, Produtos, Contato, Entrar) | `app/templates/index.html`, `template.html` |
| Quem Somos (Supabase) | `views.quem_somos`, `supabase_client.py` |
| Produtos (local + API) + Comprar só logado | `views.produtos`, `views.comprar` |
| Contato sem login | `views.add_contato` |
| Entrar / Novo Usuário / Esqueceu a senha | `login/` (reset nativo do Django) |
| Admin → /admin/ · Cliente → Dashboard | `login.views.LoginPersonalizado` |
| Dashboard, Editar Perfil, Alterar Senha | `login/` |
| Contatos, Serviços, Equipe, Meus Pedidos, Relatórios | `app/views.py` |

## Observações
- Recuperação de senha: em desenvolvimento o e-mail aparece **no terminal** (`EMAIL_BACKEND` = console).
- Rodar testes: `python manage.py test`
- **Nunca suba o `.env` para o GitHub** (a chave do Supabase fica nele).
