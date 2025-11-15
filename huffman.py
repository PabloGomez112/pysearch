import os
import heapq
import json
import struct
from collections import Counter

class NodoHuffman:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

    def __eq__(self, other):
        if not isinstance(other, NodoHuffman):
            return False
        return self.freq == other.freq

class HuffmanCompressor:
    
    def __init__(self):
        self.codigos = {}
        self.arbol = None

    def _calcular_frecuencias(self, texto):
        return Counter(texto)

    def _construir_arbol(self, frecuencias):
        cola_prioridad = [NodoHuffman(char, freq) for char, freq in frecuencias.items()]
        heapq.heapify(cola_prioridad)

        while len(cola_prioridad) > 1:
            nodo_izq = heapq.heappop(cola_prioridad)
            nodo_der = heapq.heappop(cola_prioridad)

            freq_suma = nodo_izq.freq + nodo_der.freq
            nodo_padre = NodoHuffman(None, freq_suma)
            nodo_padre.left = nodo_izq
            nodo_padre.right = nodo_der

            heapq.heappush(cola_prioridad, nodo_padre)
        
        self.arbol = cola_prioridad[0]

    def _generar_codigos_recursivo(self, nodo_actual, codigo_actual):
        if nodo_actual is None:
            return

        if nodo_actual.char is not None:
            self.codigos[nodo_actual.char] = codigo_actual or "0"
            return

        self._generar_codigos_recursivo(nodo_actual.left, codigo_actual + "0")
        self._generar_codigos_recursivo(nodo_actual.right, codigo_actual + "1")

    def _generar_codigos_completos(self):
        self.codigos = {}
        self._generar_codigos_recursivo(self.arbol, "")

    def _get_texto_codificado(self, texto):
        return "".join([self.codigos[char] for char in texto])

    def _empaquetar_bits(self, texto_codificado):
        padding = (8 - len(texto_codificado) % 8) % 8
        texto_codificado += "0" * padding
        
        info_padding_byte = bytes([padding])
        
        bytes_comprimidos = bytearray()
        for i in range(0, len(texto_codificado), 8):
            byte = texto_codificado[i:i+8]
            bytes_comprimidos.append(int(byte, 2))
            
        return info_padding_byte + bytes_comprimidos

    def _serializar_arbol(self):
        header_json = json.dumps(self.codigos)
        header_bytes = header_json.encode('utf-8')
        
        header_len = struct.pack('I', len(header_bytes))
        return header_len + header_bytes

    def compress(self, ruta_archivo):
        ruta_salida = ruta_archivo + ".ziphuff"
        
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                texto = f.read()
            
            if not texto:
                raise ValueError("El archivo está vacío.")
                
            frecuencias = self._calcular_frecuencias(texto)
            
            self._construir_arbol(frecuencias)
            
            self._generar_codigos_completos()
            
            texto_codificado = self._get_texto_codificado(texto)
            
            ruta_debug = ruta_archivo + ".debug_bits.txt"
            try:
                with open(ruta_debug, 'w', encoding='utf-8') as f_debug:
                    f_debug.write(texto_codificado)
            except Exception as e_debug:
                print(f"No se pudo escribir el archivo debug: {e_debug}")
            
            datos_comprimidos = self._empaquetar_bits(texto_codificado)
            
            header = self._serializar_arbol()
            
            with open(ruta_salida, 'wb') as f_out:
                f_out.write(header)
                f_out.write(datos_comprimidos)
                
            return ruta_salida, self.codigos

        except Exception as e:
            print(f"Error en compresión: {e}")
            return None, None

    def decompress(self, ruta_archivo_comprimido):
        ruta_salida = ruta_archivo_comprimido.replace(".ziphuff", "_descomprimido.txt")
        
        try:
            with open(ruta_archivo_comprimido, 'rb') as f:
                header_len_bytes = f.read(4)
                header_len = struct.unpack('I', header_len_bytes)[0]
                
                header_json_bytes = f.read(header_len)
                header_json = header_json_bytes.decode('utf-8')
                codigos = json.loads(header_json)
                
                codigos_inversos = {v: k for k, v in codigos.items()}
                
                info_padding_byte = f.read(1)
                padding = info_padding_byte[0]
                
                datos_comprimidos = f.read()
                
                bit_string = ""
                for byte in datos_comprimidos:
                    bit_string += f"{byte:08b}"
                
                if padding > 0:
                    bit_string = bit_string[:-padding]
                
                texto_decodificado = ""
                codigo_actual = ""
                for bit in bit_string:
                    codigo_actual += bit
                    if codigo_actual in codigos_inversos:
                        texto_decodificado += codigos_inversos[codigo_actual]
                        codigo_actual = ""
                        
            with open(ruta_salida, 'w', encoding='utf-8') as f_out:
                f_out.write(texto_decodificado)
                
            return ruta_salida
            
        except Exception as e:
            print(f"Error en descompresión: {e}")
            return None