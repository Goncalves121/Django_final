"""Cliente do Supabase (banco remoto da equipe).

Fica "preguiçoso": só conecta quando alguém usa. Assim o site inteiro não
quebra se o .env estiver sem as chaves ou se o Supabase estiver fora do ar.
"""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

TABELA = "integrantes"


class SupabaseIndisponivel(Exception):
    pass


@lru_cache(maxsize=1)
def _cliente():
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    chave = os.getenv("SUPABASE_KEY")
    if not url or not chave:
        raise SupabaseIndisponivel("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env")
    return create_client(url, chave)


def tabela():
    try:
        return _cliente().table(TABELA)
    except SupabaseIndisponivel:
        raise
    except Exception as erro:  # chave inválida, sem rede etc.
        raise SupabaseIndisponivel(str(erro)) from erro


def listar_integrantes():
    return tabela().select("*").order("id").execute().data or []


def obter_integrante(id_integrante):
    dados = tabela().select("*").eq("id", id_integrante).limit(1).execute().data
    return dados[0] if dados else None


def criar_integrante(dados):
    tabela().insert(dados).execute()


def atualizar_integrante(id_integrante, dados):
    tabela().update(dados).eq("id", id_integrante).execute()


def excluir_integrante(id_integrante):
    tabela().delete().eq("id", id_integrante).execute()
