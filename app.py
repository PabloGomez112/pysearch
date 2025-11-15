import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
from huffman import HuffmanCompressor

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Compresor Huffman - Proyecto")
        self.root.geometry("600x450")
        
        self.ruta_archivo = ""
        self.compresor = HuffmanCompressor()
        
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        frame_carga = tk.LabelFrame(main_frame, text="1. Archivo Original (.txt)", padx=10, pady=10)
        frame_carga.pack(fill=tk.X, pady=5)

        self.btn_cargar = tk.Button(frame_carga, text="Cargar Archivo", command=self.cargar_archivo)
        self.btn_cargar.pack(side=tk.LEFT, padx=5)

        self.lbl_ruta_original = tk.Label(frame_carga, text="No se ha cargado ningún archivo", fg="gray")
        self.lbl_ruta_original.pack(side=tk.LEFT, padx=5)

        frame_resultados = tk.LabelFrame(main_frame, text="2. Resultados y Comparación", padx=10, pady=10)
        frame_resultados.pack(fill=tk.X, pady=5)
        
        self.lbl_tamano_original = tk.Label(frame_resultados, text="Tamaño Original: -")
        self.lbl_tamano_original.pack(anchor="w")
        
        self.lbl_tamano_comprimido = tk.Label(frame_resultados, text="Tamaño Comprimido: -")
        self.lbl_tamano_comprimido.pack(anchor="w")
        
        self.lbl_ratio = tk.Label(frame_resultados, text="Ratio de Compresión: -", font=("Helvetica", 10, "bold"))
        self.lbl_ratio.pack(anchor="w", pady=5)

        frame_compresion = tk.LabelFrame(main_frame, text="3. Compresión", padx=10, pady=10)
        frame_compresion.pack(fill=tk.X, pady=5)

        self.btn_comprimir = tk.Button(frame_compresion, text="Comprimir Archivo", command=self.comprimir_archivo, state=tk.DISABLED)
        self.btn_comprimir.pack(pady=5)
        
        self.btn_ver_codigos = tk.Button(frame_compresion, text="Ver Códigos Generados", command=self.ver_codigos, state=tk.DISABLED)
        self.btn_ver_codigos.pack(pady=5)

        frame_descompresion = tk.LabelFrame(main_frame, text="4. Descompresión (Verificación)", padx=10, pady=10)
        frame_descompresion.pack(fill=tk.X, pady=5)

        self.btn_descomprimir = tk.Button(frame_descompresion, text="Descomprimir Archivo", command=self.descomprimir_archivo)
        self.btn_descomprimir.pack(pady=5)

    def cargar_archivo(self):
        self.ruta_archivo = filedialog.askopenfilename(
            title="Selecciona un archivo de texto",
            filetypes=[("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if not self.ruta_archivo:
            return
            
        try:
            tamano_original = os.path.getsize(self.ruta_archivo)
            self.lbl_ruta_original.config(text=os.path.basename(self.ruta_archivo), fg="black")
            self.lbl_tamano_original.config(text=f"Tamaño Original: {tamano_original:,} bytes")
            self.btn_comprimir.config(state=tk.NORMAL)
            
            self.lbl_tamano_comprimido.config(text="Tamaño Comprimido: -", fg="black")
            self.lbl_ratio.config(text="Ratio de Compresión: -", fg="black")
            self.btn_ver_codigos.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo: {e}")

    def comprimir_archivo(self):
        if not self.ruta_archivo:
            messagebox.showwarning("Advertencia", "Por favor, carga un archivo primero.")
            return

        try:
            self.compresor = HuffmanCompressor() 
            ruta_comprimido, codigos = self.compresor.compress(self.ruta_archivo)
            
            if ruta_comprimido:
                tamano_comprimido = os.path.getsize(ruta_comprimido)
                tamano_original = os.path.getsize(self.ruta_archivo)
                
                if tamano_original > 0:
                    ratio = (1 - (tamano_comprimido / tamano_original)) * 100
                    self.lbl_ratio.config(text=f"Ratio de Compresión: {ratio:.2f}% (Ahorro)", fg="green")
                else:
                    self.lbl_ratio.config(text="Ratio de Compresión: N/A", fg="gray")

                self.lbl_tamano_comprimido.config(text=f"Tamaño Comprimido: {tamano_comprimido:,} bytes", fg="green")
                self.btn_ver_codigos.config(state=tk.NORMAL)
                
                messagebox.showinfo("Éxito", f"Archivo comprimido y guardado como:\n{ruta_comprimido}")
            else:
                messagebox.showerror("Error", "La compresión falló. Revisa la consola.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al comprimir: {e}")
            
    def ver_codigos(self):
        if not self.compresor.codigos:
            messagebox.showwarning("Advertencia", "No hay códigos para mostrar. Comprime un archivo primero.")
            return

        win_codigos = tk.Toplevel(self.root)
        win_codigos.title("Códigos de Huffman Generados")
        win_codigos.geometry("400x500")
        
        txt_area = scrolledtext.ScrolledText(win_codigos, wrap=tk.WORD, width=50, height=30)
        txt_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        txt_area.insert(tk.INSERT, "Caracter\t| Código Binario\n")
        txt_area.insert(tk.INSERT, "-------------------------------------------\n")
        
        # --- CAMBIO AQUÍ ---
        # Ordena por la longitud del código (item[1])
        codigos_ordenados = sorted(self.compresor.codigos.items(), key=lambda item: len(item[1]))
        
        for char, code in codigos_ordenados:
            if char == '\n':
                char_repr = "'\\n'"
            elif char == '\t':
                char_repr = "'\\t'"
            elif char == ' ':
                char_repr = "' '"
            else:
                char_repr = f"'{char}'"
                
            txt_area.insert(tk.INSERT, f"{char_repr:<10}\t| {code}\n")
            
        txt_area.config(state=tk.DISABLED)


    def descomprimir_archivo(self):
        ruta_huff = filedialog.askopenfilename(
            title="Selecciona un archivo .ziphuff para descomprimir",
            filetypes=[("Archivos Huffman", "*.ziphuff"), ("Todos los archivos", "*.*")]
        )
        
        if not ruta_huff:
            return
            
        try:
            descompresor = HuffmanCompressor()
            ruta_salida = descompresor.decompress(ruta_huff)
            
            if ruta_salida:
                messagebox.showinfo("Éxito", f"Archivo descomprimido y guardado como:\n{ruta_salida}")
            else:
                messagebox.showerror("Error", "La descompresión falló. Revisa la consola.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al descomprimir: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()