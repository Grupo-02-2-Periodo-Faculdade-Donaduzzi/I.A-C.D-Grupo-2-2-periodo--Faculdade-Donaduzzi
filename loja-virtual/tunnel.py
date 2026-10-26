"""Testa a conexao com o banco via Cloudflare Tunnel. Credenciais vem do .env."""
import os
import subprocess
import time

import psycopg2
from dotenv import load_dotenv

load_dotenv()

HOST_TUNNEL = os.environ["DB_TUNNEL_HOSTNAME"]
PORTA_LOCAL = int(os.environ.get("DB_TUNNEL_LOCAL_PORT", "15436"))

tunnel = subprocess.Popen(
    ["cloudflared", "access", "tcp", "--hostname", HOST_TUNNEL, "--url", f"127.0.0.1:{PORTA_LOCAL}"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(5)  # espera o tunnel abrir

try:
    conn = psycopg2.connect(
        host="127.0.0.1", port=PORTA_LOCAL,
        dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=15,
    )
    with conn, conn.cursor() as cur:
        cur.execute("select current_database()")
        print(cur.fetchone())
    conn.close()
finally:
    tunnel.terminate()
