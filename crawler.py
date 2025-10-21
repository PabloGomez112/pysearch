import requests
import time
from collections import deque
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import psycopg2

POSTGRES_CREDENTIAL = {"ip": "myip", "database": "urls", "port": 5432, "username": "postgres",
                       "password": "mypass"}

try:
    database_connection = psycopg2.connect(host=POSTGRES_CREDENTIAL["ip"],
                                           database=POSTGRES_CREDENTIAL["database"],
                                           user=POSTGRES_CREDENTIAL["username"],
                                           password=POSTGRES_CREDENTIAL["password"],
                                           client_encoding='utf8'
                                           )
    print(database_connection.encoding)
    print("Conectado a la base de datos!")
except psycopg2.Error as e:
    database_connection = None
    print(f"Error fatal al conectar a la DB: {e}")


def insert_url(url: str, title: str):
    if not database_connection:
        print("[Error DB] No hay conexión a la base de datos.")
        return

    database_cursor = None
    try:
        database_cursor = database_connection.cursor()

        insert_sql = "INSERT INTO scanned_urls (url, title) VALUES (%s, %s);"

        database_cursor.execute(insert_sql, (url, title))

        database_connection.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error al insertar en la base de datos: {error}")
        if database_connection:
            database_connection.rollback()
    finally:
        if database_cursor:
            database_cursor.close()

def crawl_sites(seed_urls, max_pages=100, user_agent="MySimpleCrawler/1.0"):

    queue = deque()
    visited_or_queued = set()
    robot_parsers = {}
    pages_crawled = 0

    try:
        seed_domains = {urlparse(seed).netloc for seed in seed_urls}
    except Exception as e:
        print(f"Error en las URLs semilla: {e}")
        return

    for url in seed_urls:
        clean_url = normalize_url(url)
        if clean_url:
            queue.append(clean_url)
            visited_or_queued.add(clean_url)

    print(f"--- Iniciando rastreo con {len(queue)} URLs semilla ---")
    print(f"--- Dominios permitidos: {seed_domains} ---")
    print(f"--- Límite de {max_pages} páginas ---")

    try:
        while queue and pages_crawled < max_pages:
            current_url = queue.popleft()

            parsed_url = urlparse(current_url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            robots_url = f"{domain}/robots.txt"

            if domain not in robot_parsers:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                    robot_parsers[domain] = rp
                except Exception as e:
                    print(f"[Error] No se pudo leer {robots_url}: {e}")
                    robot_parsers[domain] = None

            parser = robot_parsers[domain]

            if parser and not parser.can_fetch(user_agent, current_url):
                print(f"[Robots] Acceso denegado: {current_url}")
                continue

            try:
                time.sleep(0.6)
                response = requests.get(
                    current_url,
                    headers={"User-Agent": user_agent},
                    timeout=5
                )

                if response.status_code != 200:
                    print(f"[Error {response.status_code}] Falló la descarga de {current_url}")
                    continue

                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type:
                    print(f"[Info] Omitiendo (no es HTML): {current_url}")
                    continue

            except requests.exceptions.RequestException as e:
                print(f"[Error] Excepción en petición: {e}")
                continue

            pages_crawled += 1
            soup = BeautifulSoup(response.text, 'html.parser')

            h1_tag = soup.find('h1')
            if h1_tag:
                h1_text = h1_tag.get_text().strip()
                insert_url(current_url, h1_text)
            else:
                print(f"    [Info] No se encontró H1 en: {current_url}")

            for link_tag in soup.find_all('a', href=True):
                link = link_tag['href']
                new_url = normalize_url(current_url, link)

                if not new_url:
                    continue

                new_domain = urlparse(new_url).netloc
                if new_domain not in seed_domains:
                    continue

                if new_url not in visited_or_queued:
                    visited_or_queued.add(new_url)
                    queue.append(new_url)

    except KeyboardInterrupt:
        pass

    print(f"\n--- Rastreo finalizado ---")
    print(f"Páginas totales rastreadas: {pages_crawled}")
    print(f"URLs únicas encontradas (en cola o visitadas): {len(visited_or_queued)}")


def normalize_url(base_url, link=None):
    try:
        if link:
            full_url = urljoin(base_url, link)
        else:
            full_url = base_url

        full_url = urldefrag(full_url)[0]

        if full_url.endswith('/'):
            full_url = full_url[:-1]

        parsed = urlparse(full_url)

        if parsed.scheme not in ('http', 'https'):
            return None

        return full_url
    except Exception as e:
        return None

if __name__ == "__main__":
    URLS_SEMILLA = [
        "https://seed_example.com",
    ]

    if database_connection:
        crawl_sites(URLS_SEMILLA, max_pages=10_000)
        database_connection.close()
        print("Conexión a la base de datos cerrada.")
    else:
        print("No se pudo iniciar el crawler, la conexión a la base de datos falló.")
