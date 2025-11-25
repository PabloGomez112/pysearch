
import pandas as pd
import datasketch
from datasketch import MinHash, MinHashLSHForest
from six import StringIO
from huffman import HuffmanCompressor

NUM_PERMUTACIONES = 128
RESULTS_PER_PAGE = 10

COMPRESSED_FILENAME = "../urls_new.ziphuff"

#compressor = HuffmanCompressor()

#datos_descomprimidos = compressor.decompress_to_string(COMPRESSED_FILENAME)

CSV_FILE = '../scanned_urls_202510192249.csv'

forest = MinHashLSHForest(num_perm=NUM_PERMUTACIONES)
data_store = {}

results_data = []
current_page = 0
window = None


def make_shingle(text: str):
    if not text:
        return set()
    text = str(text).lower()
    return set(text.split())


def build_index_on_startup():
    global forest, data_store

    print("--- [MOTOR] Iniciando ---")
    print(f"Cargando CSV '{CSV_FILE}'...")
    try:
        df = pd.read_csv(CSV_FILE)
        df.dropna(subset=['title'], inplace=True)
    except FileNotFoundError:
        print("--- [ERROR FATAL] ---")
        print(f"No se encontró el archivo '{CSV_FILE}'.")
        print("Asegúrate de que el CSV esté en la misma carpeta.")
        print("---------------------")
        return False

    print(f"Creando MinHashes para {len(df)} documentos...")
    for index, row in df.iterrows():
        csv_id = str(row['id'])
        titulo = str(row['title'])
        url = str(row['url'])
        m = datasketch.MinHash(num_perm=NUM_PERMUTACIONES)
        shingle = make_shingle(titulo)
        if not shingle:
            continue

        for s in shingle:
            m.update(s.encode('utf-8'))

        data_store[csv_id] = {'title': titulo, 'url': url, 'minhash': m}

    print(f"Poblando el índice LSHForest con {len(data_store)} elementos...")
    for csv_id, data in data_store.items():
        forest.add(csv_id, data['minhash'])

    print("Finalizando índice (esto puede tardar un momento)...")
    forest.index()

    print("--- [MOTOR] ¡Índice listo! ---")
    return True


def run_real_search(query):
    global forest, data_store

    query_shingle = make_shingle(query)
    if not query_shingle:
        return []

    query_minhash = datasketch.MinHash(NUM_PERMUTACIONES)
    for s in query_shingle:
        query_minhash.update(s.encode('utf-8'))

    result_keys = forest.query(query_minhash, k=100)

    lista_resultados = []
    for csv_id_key in result_keys:
        item_similar = data_store.get(csv_id_key)
        if not item_similar:
            continue

        minhash_similar = item_similar['minhash']
        sim = query_minhash.jaccard(minhash_similar)

        if sim > 0.01:
            lista_resultados.append({
                'id': csv_id_key,
                'title': item_similar['title'],
                'url': item_similar['url'],
                'similarity': sim
            })

    lista_resultados.sort(key=lambda x: x['similarity'], reverse=True)

    return lista_resultados