import sys
from functions.ui import COLOR_INFO, COLOR_ERROR, COLOR_SUCCESS, COLOR_RESET

try:
    import psycopg2
except ImportError:
    print(f"{COLOR_ERROR}[!] Error: Librería psycopg2 no encontrada. Ejecuta: pip install psycopg2-binary{COLOR_RESET}")
    sys.exit(1)

def check_postgres_connection(config_data, silent=False):
    db_conf = config_data.get("database", {})
    if not silent: print(f"[*] Verificando conexión con PostgreSQL ({db_conf.get('host')}:{db_conf.get('port')})...", end=" ")
    try:
        conn = psycopg2.connect(
            host=db_conf.get("host"), port=db_conf.get("port"),
            user=db_conf.get("user"), password=db_conf.get("password"),
            dbname=db_conf.get("dbname"), connect_timeout=5
        )
        conn.close()
        if not silent: print(f"{COLOR_SUCCESS}[ OK ]{COLOR_RESET}")
        return True
    except psycopg2.OperationalError as e:
        error_msg = str(e).split('\n')[0]
        if not silent: print(f"{COLOR_ERROR}[ ERROR ] {error_msg}{COLOR_RESET}")
        return False

def setup_vector_database(config_data):
    db_conf = config_data.get("database", {})
    try:
        conn = psycopg2.connect(
            host=db_conf.get("host"), port=db_conf.get("port"),
            user=db_conf.get("user"), password=db_conf.get("password"), dbname=db_conf.get("dbname")
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id bigserial PRIMARY KEY,
                    task_id varchar(255),
                    content text,
                    embedding vector(4096)
                );
            """)
        return conn
    except psycopg2.Error as e:
        print(f"\n{COLOR_ERROR}[!] Error inicializando la base de datos vectorial: {e}{COLOR_RESET}")
        return None
