import customtkinter as ctk
import pandas as pd
import datasketch
from datasketch import MinHash, MinHashLSHForest
import threading
import webbrowser
import math
import sys

NUM_PERMUTACIONES = 128
RESULTS_PER_PAGE = 10
CSV_FILE = 'scanned_urls_202510192249.csv'

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

def run_search_thread(query):
    print(f"Buscando en el índice: '{query}'")
    results = run_real_search(query)
    window.after(0, update_gui_results, results)

def clear_results_frame():
    for widget in results_frame.winfo_children():
        widget.destroy()

def show_page(page_index):
    global current_page
    clear_results_frame()

    start = page_index * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    current_page = page_index

    subset = results_data[start:end]
    if not subset:
        ctk.CTkLabel(results_frame, text="No hay resultados para mostrar.").pack(pady=10)
        return

    for item in subset:
        title = item.get('title', 'Sin Título')
        url = item.get('url', '')
        sim = item.get('similarity', 0)
        title_label = ctk.CTkLabel(
            results_frame,
            text=f"[{sim*100:.1f}%] {title}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#007bff", cursor="hand2"
        )
        title_label.bind("<Button-1>", lambda e, u=url: open_link(u))
        title_label.pack(anchor="w", padx=10, pady=(5, 0))
        url_label = ctk.CTkLabel(
            results_frame, text=url,
            font=ctk.CTkFont(size=12), text_color="gray60"
        )
        url_label.pack(anchor="w", padx=10, pady=(0, 10))
    update_pagination_controls()

def update_pagination_controls():
    for widget in pagination_frame.winfo_children():
        widget.destroy()
    total_pages = math.ceil(len(results_data) / RESULTS_PER_PAGE)
    if total_pages <= 1:
        return
    prev_button = ctk.CTkButton(
        pagination_frame, text="⟨ Anterior",
        state=("disabled" if current_page == 0 else "normal"),
        command=lambda: show_page(current_page - 1)
    )
    prev_button.pack(side="left", padx=5)
    page_label = ctk.CTkLabel(
        pagination_frame, text=f"Página {current_page + 1} de {total_pages}",
        font=ctk.CTkFont(size=13)
    )
    page_label.pack(side="left", padx=10)
    next_button = ctk.CTkButton(
        pagination_frame, text="Siguiente ⟩",
        state=("disabled" if current_page >= total_pages - 1 else "normal"),
        command=lambda: show_page(current_page + 1)
    )
    next_button.pack(side="left", padx=5)

def update_gui_results(results):
    global results_data, current_page
    results_data = results
    current_page = 0
    show_page(0)

def update_gui_error(error_message):
    clear_results_frame()
    ctk.CTkLabel(results_frame, text=error_message, text_color="red").pack(pady=10)

def on_search_click():
    query = search_box.get()
    if not query:
        return
        
    clear_results_frame()
    ctk.CTkLabel(results_frame, text="Buscando en el índice...").pack(pady=10)
    threading.Thread(target=run_search_thread, args=(query,), daemon=True).start()

def open_link(url):
    print(f"Abriendo: {url}")
    webbrowser.open_new_tab(url)

if __name__ == "__main__":
    
    if not build_index_on_startup():
        sys.exit()

    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    
    window = ctk.CTk()
    window.title("Mi Buscador LSH (Versión CSV Completa)")
    window.geometry("700x550")

    top_frame = ctk.CTkFrame(window, fg_color="transparent")
    top_frame.pack(pady=10, padx=10, fill="x")

    search_box = ctk.CTkEntry(
        top_frame,
        font=ctk.CTkFont(size=14),
        placeholder_text="Escribe tu búsqueda aquí..."
    )
    search_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
    search_box.bind("<Return>", lambda event: on_search_click())

    search_button = ctk.CTkButton(
        top_frame,
        text="Buscar",
        font=ctk.CTkFont(size=14, weight="bold"),
        command=on_search_click
    )
    search_button.pack(side="right")

    results_frame = ctk.CTkScrollableFrame(window)
    results_frame.pack(pady=(10, 0), padx=10, fill="both", expand=True)

    pagination_frame = ctk.CTkFrame(window, fg_color="transparent")
    pagination_frame.pack(pady=10)

    print("Iniciando interfaz de usuario...")
    window.mainloop()