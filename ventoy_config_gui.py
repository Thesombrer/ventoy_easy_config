import glob
import os
import json
import re
import shutil
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk

class VentoyConfigGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Ocultar ventana principal
        
    def cargar_base_datos(self):
        """Cargar base de datos desde archivo externo"""
        try:
            with open("base_datos.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def guardar_base_datos(self, base):
        """Guardar cambios a la base de datos"""
        with open("base_datos.json", "w", encoding="utf-8") as f:
            json.dump(base, f, indent=4)

    def cargar_ventoy_json(self):
        """Leer Ventoy.Json"""
        ruta = "Ventoy.Json"
        if not os.path.isfile(ruta):
            messagebox.showerror("Error", "No se encontró Ventoy.Json")
            return None, ruta
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f), ruta

    def obtener_tema(self, config):
        """Obtener tema actual desde el JSON"""
        ruta = config.get("theme", {}).get("file", "")
        match = re.search(r"/Ventoy/Themes/([^/]+)/", ruta)
        return match.group(1) if match else None

    def listar_isos(self):
        """Listar isos en la carpeta padre (raíz del USB)"""
        parent_dir = os.path.dirname(os.getcwd())
        return [f for f in os.listdir(parent_dir) if f.lower().endswith(".iso")]

    def listar_temas_disponibles(self):
        """Listar temas disponibles en la carpeta Themes"""
        themes_path = os.path.join("Themes")
        if not os.path.isdir(themes_path):
            return []
        
        temas = []
        for item in os.listdir(themes_path):
            theme_path = os.path.join(themes_path, item)
            if os.path.isdir(theme_path):
                theme_txt = os.path.join(theme_path, "theme.txt")
                if os.path.isfile(theme_txt):
                    temas.append(item)
        return temas

    def detectar_sistema_automatico(self, nombre_iso, base):
        """Detecta automáticamente el sistema operativo basándose en el nombre del archivo ISO"""
        nombre_lower = nombre_iso.lower()
        
        # Dividir el nombre en partes
        partes = re.split(r"[-_.]+", nombre_lower)
        
        # Buscar coincidencias exactas primero
        for parte in partes:
            if parte in base:
                return parte, base[parte][0]
        
        # Buscar coincidencias parciales
        for clave, valores in base.items():
            if clave in nombre_lower:
                return clave, valores[0]
            # También verificar si algún valor de la base está en el nombre
            for valor in valores:
                if valor in nombre_lower:
                    return clave, valor
        
        # Si no encuentra nada, devolver None
        return None, None

    def buscar_icono_por_partes(self, tema, nombre_iso, equivalentes):
        """Busca iconos disponibles y maneja múltiples coincidencias"""
        partes = re.split(r"[-_.]+", nombre_iso.lower())
        iconos_path = os.path.join("Themes", tema, "icons")
        
        if not os.path.isdir(iconos_path):
            return None

        disponibles = [f for f in os.listdir(iconos_path) if f.endswith(".png")]

        # 1. Buscar coincidencias directas con partes del nombre
        coincidencias = []
        for archivo in disponibles:
            nombre_archivo = os.path.splitext(archivo)[0].lower()
            for parte in partes:
                if parte in nombre_archivo or nombre_archivo in parte:
                    coincidencias.append(os.path.splitext(archivo)[0])
                    break
        
        # Eliminar duplicados manteniendo el orden
        coincidencias = list(dict.fromkeys(coincidencias))
        
        # 2. Buscar por equivalencias desde la base
        for equivalente in equivalentes:
            for archivo in disponibles:
                nombre_archivo = os.path.splitext(archivo)[0].lower()
                if equivalente in nombre_archivo:
                    icono_equiv = os.path.splitext(archivo)[0]
                    if icono_equiv not in coincidencias:
                        coincidencias.append(icono_equiv)

        # Manejar resultados
        if len(coincidencias) == 1:
            return coincidencias[0]
        elif len(coincidencias) > 1:
            return self.elegir_icono_usuario(coincidencias, nombre_iso)
        
        return None

    def elegir_icono_usuario(self, opciones, nombre_iso):
        """Ventana para elegir entre múltiples iconos disponibles"""
        print(f"    - Mostrando ventana de selección de icono...")
        
        # Asegurar que la ventana root esté visible
        self.root.deiconify()
        self.root.update()
        
        resultado = [None]  # Usar lista para poder modificar desde funciones internas
        
        def seleccionar(opcion):
            print(f"    - Usuario seleccionó icono: {opcion}")
            resultado[0] = opcion
            ventana.destroy()

        def cancelar():
            print("    - Usuario canceló selección")
            resultado[0] = None
            ventana.destroy()

        ventana = tk.Toplevel(self.root)
        ventana.title(f"Elegir icono para {nombre_iso}")
        ventana.geometry("400x300")
        ventana.resizable(False, False)
        
        # Forzar que aparezca la ventana
        ventana.lift()
        ventana.attributes('-topmost', True)
        
        # Centrar la ventana
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (400 // 2)
        y = (ventana.winfo_screenheight() // 2) - (300 // 2)
        ventana.geometry(f"400x300+{x}+{y}")
        
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.focus_set()
        
        # Configurar cierre de ventana
        ventana.protocol("WM_DELETE_WINDOW", cancelar)
        
        # Después de configurar todo, quitar topmost
        ventana.after(100, lambda: ventana.attributes('-topmost', False))
        
        tk.Label(ventana, text=f"Se encontraron varios iconos compatibles con:\n'{nombre_iso}'\n\nElige el más apropiado:", 
                 justify=tk.CENTER, wraplength=350).pack(pady=10)

        # Frame para los botones
        frame_botones = tk.Frame(ventana)
        frame_botones.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Scrollbar si hay muchas opciones
        if len(opciones) > 8:
            canvas = tk.Canvas(frame_botones)
            scrollbar = tk.Scrollbar(frame_botones, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            for opcion in opciones:
                tk.Button(scrollable_frame, text=opcion, width=30, 
                         command=lambda o=opcion: seleccionar(o)).pack(pady=2)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        else:
            for opcion in opciones:
                tk.Button(frame_botones, text=opcion, width=30, 
                         command=lambda o=opcion: seleccionar(o)).pack(pady=2)

        # Botón cancelar
        tk.Button(ventana, text="Cancelar (usar unknown)", width=20, 
                 command=cancelar).pack(pady=10)

        print("    - Esperando respuesta del usuario...")
        # Esperar a que se cierre la ventana
        ventana.wait_window()
        print(f"    - Usuario respondió: {resultado[0]}")
        return resultado[0]

    def gestionar_icono_faltante(self, tema, nombre_iso, clase_detectada=None):
        """Maneja cuando no se encuentra un icono apropiado"""
        print(f"    - Mostrando ventana de gestión de icono faltante...")
        
        # Asegurar que la ventana root esté visible
        self.root.deiconify()
        self.root.update()
        
        mensaje = f"No se encontró icono apropiado para '{nombre_iso}'"
        if clase_detectada:
            mensaje += f"\n(Detectado como: {clase_detectada})"
        mensaje += "\n\n¿Qué deseas hacer?"
        
        resultado = [None]  # Usar lista para poder modificar desde funciones internas
        
        def seleccionar_manual():
            print("    - Usuario seleccionó: manual")
            resultado[0] = "manual"
            ventana.destroy()
        
        def usar_unknown():
            print("    - Usuario seleccionó: unknown")
            resultado[0] = "unknown"
            ventana.destroy()
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Icono no encontrado")
        ventana.geometry("400x200")
        ventana.resizable(False, False)
        
        # Forzar que aparezca la ventana
        ventana.lift()
        ventana.attributes('-topmost', True)
        
        # Centrar ventana
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (400 // 2)
        y = (ventana.winfo_screenheight() // 2) - (200 // 2)
        ventana.geometry(f"400x200+{x}+{y}")
        
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.focus_set()
        ventana.protocol("WM_DELETE_WINDOW", usar_unknown)
        
        # Después de configurar todo, quitar topmost
        ventana.after(100, lambda: ventana.attributes('-topmost', False))
        
        tk.Label(ventana, text=mensaje, justify=tk.CENTER, wraplength=350).pack(pady=20)
        
        frame_botones = tk.Frame(ventana)
        frame_botones.pack(pady=10)
        
        tk.Button(frame_botones, text="Seleccionar icono manualmente", 
                 command=seleccionar_manual).pack(pady=5)
        tk.Button(frame_botones, text="Usar icono 'unknown'", 
                 command=usar_unknown).pack(pady=5)
        
        print("    - Esperando respuesta del usuario...")
        ventana.wait_window()
        print(f"    - Usuario respondió: {resultado[0]}")
        
        if resultado[0] == "manual":
            if self.copiar_icono_manual(tema, nombre_iso):
                return nombre_iso
            else:
                messagebox.showinfo("Aviso", "No se seleccionó ningún icono. Se usará 'unknown'.")
        
        # Verificar si existe unknown.png
        ruta_unknown = os.path.join("Themes", tema, "icons", "unknown.png")
        if os.path.isfile(ruta_unknown):
            return "unknown"
        else:
            messagebox.showwarning("Falta unknown.png", 
                                 "No se encontró 'unknown.png'. Considera agregarlo al tema.")
            return ""

    def copiar_icono_manual(self, tema, nombre_clase):
        """Copia un icono seleccionado manualmente"""
        ruta_destino = os.path.join("Themes", tema, "icons", f"{nombre_clase}.png")
        origen = filedialog.askopenfilename(
            title="Selecciona un icono (.png)", 
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if origen:
            try:
                shutil.copy(origen, ruta_destino)
                messagebox.showinfo("Éxito", f"Icono copiado como '{nombre_clase}.png'")
                return True
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo copiar el icono: {e}")
                return False
        return False

    def preguntar_sistema_operativo(self, nombre_iso, base):
        """Pregunta al usuario qué sistema operativo es"""
        print(f"    - Mostrando ventana de selección de sistema operativo...")
        
        # Asegurar que la ventana root esté visible
        self.root.deiconify()
        self.root.update()
        
        sistemas_comunes = [
            "ubuntu", "debian", "fedora", "archlinux", "windows", 
            "linuxmint", "manjaro", "opensuse", "centos", "unknown"
        ]
        
        resultado = [None]  # Usar lista para poder modificar desde funciones internas
        
        def seleccionar_sistema(sistema):
            print(f"    - Usuario seleccionó sistema: {sistema}")
            resultado[0] = sistema
            ventana.destroy()
        
        def entrada_personalizada():
            print("    - Usuario eligió entrada personalizada")
            ventana.withdraw()  # Ocultar ventana temporalmente
            custom = simpledialog.askstring(
                "Sistema personalizado",
                f"¿Qué sistema operativo es '{nombre_iso}'?\n(Será agregado a la base de datos)",
                parent=self.root
            )
            if custom:
                resultado[0] = custom.lower()
                print(f"    - Usuario escribió: {resultado[0]}")
            else:
                resultado[0] = "unknown"
                print("    - Usuario canceló entrada personalizada")
            ventana.destroy()
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Sistema no reconocido")
        ventana.geometry("400x300")
        ventana.resizable(False, False)
        
        # Forzar que aparezca la ventana
        ventana.lift()
        ventana.attributes('-topmost', True)
        
        # Centrar ventana
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (400 // 2)
        y = (ventana.winfo_screenheight() // 2) - (300 // 2)
        ventana.geometry(f"400x300+{x}+{y}")
        
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.focus_set()
        ventana.protocol("WM_DELETE_WINDOW", lambda: seleccionar_sistema("unknown"))
        
        # Después de configurar todo, quitar topmost
        ventana.after(100, lambda: ventana.attributes('-topmost', False))
        
        tk.Label(ventana, text=f"No se pudo detectar automáticamente:\n'{nombre_iso}'\n\nSelecciona el sistema operativo:", 
                 justify=tk.CENTER, wraplength=350).pack(pady=10)
        
        frame_sistemas = tk.Frame(ventana)
        frame_sistemas.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Crear botones en columnas
        for i, sistema in enumerate(sistemas_comunes):
            row = i // 2
            col = i % 2
            tk.Button(frame_sistemas, text=sistema.title(), width=15,
                     command=lambda s=sistema: seleccionar_sistema(s)).grid(row=row, column=col, padx=5, pady=2)
        
        tk.Button(ventana, text="Otro (personalizado)", 
                 command=entrada_personalizada).pack(pady=5)
        tk.Button(ventana, text="Saltar (usar unknown)", 
                 command=lambda: seleccionar_sistema("unknown")).pack(pady=5)
        
        print("    - Esperando respuesta del usuario...")
        ventana.wait_window()
        print(f"    - Usuario respondió: {resultado[0]}")
        
        if resultado[0] and resultado[0] != "unknown":
            # Agregar a la base de datos
            clave = re.sub(r"[^a-z0-9]", "", nombre_iso.lower())
            base[clave] = [resultado[0]]
            self.guardar_base_datos(base)
            messagebox.showinfo("Base actualizada", f"Se agregó '{nombre_iso}' -> '{resultado[0]}' a la base de datos")
            return clave, resultado[0]
        
        return None, "unknown"

    def seleccionar_tema(self, temas_disponibles, tema_actual):
        """Ventana para seleccionar un tema"""
        print(f"    - Mostrando ventana de selección de tema...")
        
        # Asegurar que la ventana root esté visible
        self.root.deiconify()
        self.root.update()
        
        resultado = [None]
        
        def seleccionar(tema):
            print(f"    - Usuario seleccionó tema: {tema}")
            resultado[0] = tema
            ventana.destroy()
        
        def cancelar():
            print("    - Usuario canceló selección de tema")
            resultado[0] = None
            ventana.destroy()
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Seleccionar Tema")
        ventana.geometry("400x350")
        ventana.resizable(False, False)
        
        # Forzar que aparezca la ventana
        ventana.lift()
        ventana.attributes('-topmost', True)
        
        # Centrar ventana
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (400 // 2)
        y = (ventana.winfo_screenheight() // 2) - (350 // 2)
        ventana.geometry(f"400x350+{x}+{y}")
        
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.focus_set()
        ventana.protocol("WM_DELETE_WINDOW", cancelar)
        
        # Después de configurar todo, quitar topmost
        ventana.after(100, lambda: ventana.attributes('-topmost', False))
        
        tk.Label(ventana, text=f"Tema actual: {tema_actual}\n\nSelecciona el nuevo tema:", 
                 justify=tk.CENTER, wraplength=350).pack(pady=10)
        
        frame_temas = tk.Frame(ventana)
        frame_temas.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Crear lista con scroll
        canvas = tk.Canvas(frame_temas)
        scrollbar = tk.Scrollbar(frame_temas, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for tema in temas_disponibles:
            color = "lightblue" if tema == tema_actual else "white"
            text = f"{tema} (actual)" if tema == tema_actual else tema
            tk.Button(scrollable_frame, text=text, width=30, bg=color,
                     command=lambda t=tema: seleccionar(t)).pack(pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        tk.Button(ventana, text="Cancelar", width=20, 
                 command=cancelar).pack(pady=10)
        
        print("    - Esperando respuesta del usuario...")
        ventana.wait_window()
        print(f"    - Usuario respondió: {resultado[0]}")
        return resultado[0]

    def cambiar_tema(self, config, nuevo_tema, ruta_json):
        """Cambia el tema en la configuración"""
        config["theme"]["file"] = f"/Ventoy/Themes/{nuevo_tema}/theme.txt"
        
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        
        print(f"Tema cambiado a: {nuevo_tema}")
        return True

    def mostrar_menu_principal(self, isos_info, temas_disponibles, tema_actual):
        """Muestra el menú principal con opciones"""
        print(f"    - Mostrando menú principal...")
        
        # Asegurar que la ventana root esté visible
        self.root.deiconify()
        self.root.update()
        
        resultado = [None]
        
        def agregar_isos():
            print("    - Usuario seleccionó: Agregar ISOs")
            resultado[0] = "agregar_isos"
            ventana.destroy()
        
        def cambiar_tema():
            print("    - Usuario seleccionó: Cambiar tema")
            resultado[0] = "cambiar_tema"
            ventana.destroy()
        
        def salir():
            print("    - Usuario seleccionó: Salir")
            resultado[0] = "salir"
            ventana.destroy()
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Ventoy Config GUI")
        ventana.geometry("500x400")
        ventana.resizable(False, False)
        
        # Forzar que aparezca la ventana
        ventana.lift()
        ventana.attributes('-topmost', True)
        
        # Centrar ventana
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (500 // 2)
        y = (ventana.winfo_screenheight() // 2) - (400 // 2)
        ventana.geometry(f"500x400+{x}+{y}")
        
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.focus_set()
        ventana.protocol("WM_DELETE_WINDOW", salir)
        
        # Después de configurar todo, quitar topmost
        ventana.after(100, lambda: ventana.attributes('-topmost', False))
        
        # Título
        tk.Label(ventana, text="Ventoy Config GUI", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Información actual
        info_frame = tk.Frame(ventana, relief=tk.SUNKEN, borderwidth=2)
        info_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(info_frame, text="Estado actual:", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(info_frame, text=f"Tema activo: {tema_actual}").pack()
        tk.Label(info_frame, text=f"Temas disponibles: {len(temas_disponibles)}").pack()
        tk.Label(info_frame, text=f"ISOs totales: {isos_info['total']}").pack()
        
        if isos_info['nuevas'] > 0:
            tk.Label(info_frame, text=f"ISOs nuevas: {isos_info['nuevas']}", 
                    fg="green", font=("Arial", 10, "bold")).pack()
        else:
            tk.Label(info_frame, text="No hay ISOs nuevas", fg="blue").pack()
        
        # Botones de acción
        button_frame = tk.Frame(ventana)
        button_frame.pack(pady=20)
        
        if isos_info['nuevas'] > 0:
            tk.Button(button_frame, text="Agregar ISOs nuevas", width=20, height=2,
                     command=agregar_isos, bg="lightgreen").pack(pady=5)
        else:
            tk.Button(button_frame, text="Agregar ISOs nuevas", width=20, height=2,
                     command=agregar_isos, state=tk.DISABLED).pack(pady=5)
        
        tk.Button(button_frame, text="Cambiar tema", width=20, height=2,
                 command=cambiar_tema, bg="lightblue").pack(pady=5)
        
        tk.Button(button_frame, text="Salir", width=20, height=2,
                 command=salir).pack(pady=5)
        
        print("    - Esperando respuesta del usuario...")
        ventana.wait_window()
        print(f"    - Usuario respondió: {resultado[0]}")
        return resultado[0]

    def actualizar_json(self, config, nuevas_isos, tema, base, ruta_json):
        """Actualiza el JSON con las nuevas ISOs detectadas"""
        existentes = {c["key"]: c["class"] for c in config.get("menu_class", [])}
        parent_dir = os.path.dirname(os.getcwd())
        isos_actuales = [os.path.splitext(f)[0] for f in os.listdir(parent_dir) if f.lower().endswith(".iso")]
        
        print(f"Procesando {len(nuevas_isos)} nuevas ISOs...")
        
        for iso_archivo in nuevas_isos:
            nombre_iso = os.path.splitext(iso_archivo)[0]
            print(f"Procesando: {nombre_iso}")
            
            # 1. Detectar sistema automáticamente
            clave_detectada, sistema_detectado = self.detectar_sistema_automatico(nombre_iso, base)
            
            if clave_detectada:
                print(f"  - Detectado automáticamente: {sistema_detectado}")
                equivalentes = base[clave_detectada]
            else:
                print(f"  - No detectado automáticamente, preguntando al usuario...")
                clave_detectada, sistema_detectado = self.preguntar_sistema_operativo(nombre_iso, base)
                equivalentes = [sistema_detectado] if sistema_detectado != "unknown" else []
            
            # 2. Buscar icono apropiado
            icono_usado = self.buscar_icono_por_partes(tema, nombre_iso, equivalentes)
            
            if not icono_usado:
                print(f"  - No se encontró icono, gestionando...")
                icono_usado = self.gestionar_icono_faltante(tema, nombre_iso, sistema_detectado)
            
            if not icono_usado:
                icono_usado = "unknown"
            
            print(f"  - Icono asignado: {icono_usado}")
            existentes[nombre_iso] = icono_usado
        
        # Limpiar entradas que ya no existen
        for key in list(existentes.keys()):
            if key not in isos_actuales:
                del existentes[key]
        
        # Actualizar configuración
        config["menu_class"] = [{"key": k, "class": v} for k, v in sorted(existentes.items())]
        
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        
        messagebox.showinfo("Éxito", f"Ventoy.Json actualizado correctamente.\nProcesadas {len(nuevas_isos)} ISOs nuevas.")

    def rescanear_iconos_tema(self, config, tema, base, ruta_json):
        """Rescanea todos los iconos para el nuevo tema"""
        print(f"Rescaneando iconos para tema: {tema}")
        
        # Obtener todas las ISOs existentes
        parent_dir = os.path.dirname(os.getcwd())
        isos_existentes = [os.path.splitext(f)[0] for f in os.listdir(parent_dir) if f.lower().endswith(".iso")]
        
        # Actualizar iconos para todas las ISOs
        nuevos_iconos = {}
        
        for nombre_iso in isos_existentes:
            print(f"Rescaneando: {nombre_iso}")
            
            # Detectar sistema (usar lo que ya está en la base o detectar)
            clave_detectada, sistema_detectado = self.detectar_sistema_automatico(nombre_iso, base)
            
            if clave_detectada:
                equivalentes = base[clave_detectada]
            else:
                # Buscar en configuración actual
                iso_config = next((item for item in config.get("menu_class", []) if item["key"] == nombre_iso), None)
                if iso_config:
                    equivalentes = [iso_config["class"]]
                else:
                    equivalentes = []
            
            # Buscar icono apropiado para el nuevo tema
            icono_usado = self.buscar_icono_por_partes(tema, nombre_iso, equivalentes)
            
            if not icono_usado:
                icono_usado = self.gestionar_icono_faltante(tema, nombre_iso, sistema_detectado)
            
            if not icono_usado:
                icono_usado = "unknown"
            
            print(f"  - Icono asignado: {icono_usado}")
            nuevos_iconos[nombre_iso] = icono_usado
        
        # Actualizar configuración
        config["menu_class"] = [{"key": k, "class": v} for k, v in sorted(nuevos_iconos.items())]
        
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        
        messagebox.showinfo("Éxito", f"Iconos rescaneados para tema '{tema}'.\nActualizadas {len(nuevos_iconos)} ISOs.")

    def run(self):
        """Función principal"""
        print("Iniciando Ventoy Config GUI...")
        
        try:
            # Cargar configuración
            base = self.cargar_base_datos()
            config, ruta_json = self.cargar_ventoy_json()
            if not config:
                return

            # Detectar tema actual
            tema_actual = self.obtener_tema(config)
            if not tema_actual:
                messagebox.showerror("Error", "No se pudo detectar el tema actual")
                return

            # Listar temas disponibles
            temas_disponibles = self.listar_temas_disponibles()
            if not temas_disponibles:
                messagebox.showerror("Error", "No se encontraron temas disponibles")
                return

            print(f"Tema actual: {tema_actual}")
            print(f"Temas disponibles: {temas_disponibles}")
            
            # Verificar ISOs
            clases_actuales = [item["key"] for item in config.get("menu_class", [])]
            isos_en_raiz = self.listar_isos()
            nuevas_isos = [f for f in isos_en_raiz if os.path.splitext(f)[0] not in clases_actuales]

            isos_info = {
                'total': len(isos_en_raiz),
                'nuevas': len(nuevas_isos),
                'lista_nuevas': nuevas_isos
            }

            print(f"ISOs totales: {isos_info['total']}")
            print(f"ISOs nuevas: {isos_info['nuevas']}")
            
            # Mostrar menú principal
            accion = self.mostrar_menu_principal(isos_info, temas_disponibles, tema_actual)
            
            if accion == "agregar_isos":
                if nuevas_isos:
                    # Mostrar resumen y confirmar
                    if messagebox.askyesno("Confirmar procesamiento", 
                                          f"Se encontraron {len(nuevas_isos)} ISOs nuevas:\n\n" + 
                                          "\n".join(f"• {iso}" for iso in nuevas_isos[:10]) + 
                                          (f"\n... y {len(nuevas_isos)-10} más" if len(nuevas_isos) > 10 else "") +
                                          "\n\n¿Proceder con la configuración?"):
                        self.actualizar_json(config, nuevas_isos, tema_actual, base, ruta_json)
                else:
                    messagebox.showinfo("Sin cambios", "No hay nuevas ISOs para agregar.")
            
            elif accion == "cambiar_tema":
                nuevo_tema = self.seleccionar_tema(temas_disponibles, tema_actual)
                if nuevo_tema and nuevo_tema != tema_actual:
                    # Cambiar tema
                    if self.cambiar_tema(config, nuevo_tema, ruta_json):
                        messagebox.showinfo("Tema cambiado", f"Tema cambiado a: {nuevo_tema}")
                        
                        # Preguntar si quiere rescanear iconos
                        if messagebox.askyesno("Rescanear iconos", 
                                              f"¿Deseas rescanear los iconos para el nuevo tema '{nuevo_tema}'?\n\n" +
                                              "Esto actualizará los iconos de todas las ISOs existentes."):
                            # Recargar configuración con el nuevo tema
                            config, _ = self.cargar_ventoy_json()
                            self.rescanear_iconos_tema(config, nuevo_tema, base, ruta_json)
                elif nuevo_tema == tema_actual:
                    messagebox.showinfo("Sin cambios", "El tema seleccionado ya está activo.")
            
            elif accion == "salir":
                print("Saliendo...")
            
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
        finally:
            self.root.quit()

def main():
    app = VentoyConfigGUI()
    app.run()

if __name__ == "__main__":
    main()