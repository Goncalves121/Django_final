from django.db import migrations, models


def criar_tabela_se_nao_existir(apps, schema_editor):
    """A tabela `contato_contato` veio de um app antigo ('contato').

    Em bancos que já a possuem, nada é feito (os dados são preservados).
    Em um banco novo, ela é criada aqui; sem isso o formulário de contato
    quebraria depois de um `migrate` do zero.
    """
    from app.models import Contato

    if Contato._meta.db_table not in schema_editor.connection.introspection.table_names():
        schema_editor.create_model(Contato)


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0002_servico_imagem"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Contato",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("nome", models.CharField(max_length=100)),
                        ("email", models.EmailField(max_length=254)),
                        ("telefone", models.CharField(blank=True, max_length=20)),
                        ("mensagem", models.TextField()),
                    ],
                    options={"db_table": "contato_contato"},
                ),
            ],
            database_operations=[
                migrations.RunPython(criar_tabela_se_nao_existir, migrations.RunPython.noop),
            ],
        ),
    ]
