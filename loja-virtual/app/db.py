import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()  # le o .env da pasta atual (ou de cima) para os.environ


def _env(*nomes, padrao=None):
    """Retorna a primeira variavel definida. Aceita DB_* ou POSTGRES_* (as do container)."""
    for n in nomes:
        if os.getenv(n):
            return os.getenv(n)
    return padrao


def conectar():
    return psycopg2.connect(
        host=_env("DB_HOST", padrao="localhost"),
        port=_env("DB_PORT", padrao="5432"),
        dbname=_env("DB_NAME", "POSTGRES_DB"),
        user=_env("DB_USER", "POSTGRES_USER"),
        password=_env("DB_PASSWORD", "POSTGRES_PASSWORD"),
        cursor_factory=RealDictCursor,  # linhas como dict: row["nome"]
        connect_timeout=5,
    )


@contextmanager
def transacao(conn):
    """Tudo dentro do with vira UMA transacao: commit se deu certo, rollback se falhou."""
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
