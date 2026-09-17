import sys
import os
import io
import threading
import zipfile
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.dom.minidom as minidom

# ---- ANDROGUARD 4.x API ----
from androguard.core.apk import APK
from androguard.core.dex import DEX

# ---- LIBRERÍAS OPCIONALES ----
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    import xml.etree.ElementTree as ET
    HAS_LXML = False

try:
    from PIL import Image, ImageTk, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ==========================================
# CONFIGURACIÓN GLOBAL Y CONSTANTES
# ==========================================
ICON_SIZE = (96, 96)
MIN_LIST_LINES = 3

# Fuentes
FONT_TITLE = ("Helvetica", 20, "bold")
FONT_SUBTITLE = ("Helvetica", 12)
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)

# Colores
COLOR_PLACEHOLDER_BG = '#e0e0e0'
COLOR_PLACEHOLDER_BORDER = '#cccccc'
COLOR_TEXT_BG = '#fcfcfc'
COLOR_MARK_BG = '#cfe3fc'
COLOR_FOLDER_BG = '#eef3f8'

# Android XML Namespace
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

# Lista ampliada de rastreadores
KNOWN_TRACKERS = {
    'google.android.gms.measurement': 'Google Analytics / Firebase',
    'facebook.appevents': 'Facebook Analytics',
    'appsflyer': 'AppsFlyer',
    'mixpanel': 'Mixpanel',
    'flurry': 'Flurry',
    'adjust': 'Adjust',
    'amplitude': 'Amplitude',
    'kochava': 'Kochava',
    'branch.io': 'Branch',
    'segment.analytics': 'Segment',
    'yandex.metrica': 'Yandex Metrica',
    'clevertap': 'CleverTap',
    'moengage': 'MoEngage',
    'localytics': 'Localytics',
    'tenjin': 'Tenjin',
    'snowplow': 'Snowplow Analytics',
    'crashlytics': 'Crashlytics (Google)',
    'bugsnag': 'Bugsnag',
    'sentry': 'Sentry',
    'newrelic': 'New Relic',
    'datadog': 'Datadog',
    'instabug': 'Instabug',
    'appdynamics': 'AppDynamics',
    'google.android.gms.ads': 'Google AdMob',
    'facebook.ads': 'Facebook Audience Network',
    'unity3d.ads': 'Unity Ads',
    'applovin': 'AppLovin',
    'vungle': 'Vungle',
    'ironsource': 'ironSource',
    'chartboost': 'Chartboost',
    'inmobi': 'InMobi',
    'bytedance': 'TikTok / Pangle Ads',
    'amazon.device.ads': 'Amazon Ads',
    'mopub': 'MoPub (Twitter)',
    'tapjoy': 'Tapjoy',
    'adcolony': 'AdColony',
    'onesignal': 'OneSignal',
    'urbanairship': 'Airship',
    'braze': 'Braze',
    'pushwoosh': 'Pushwoosh',
    'batch': 'Batch',
    'leanplum': 'Leanplum'
}

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner_frame = ttk.Frame(self.canvas)

        self.inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")


class ApkAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("APKViewer")
        self.root.geometry("1000x750")

        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar padding global y forzarlo explícitamente en el mapa de estados para la pestaña seleccionada
        style.configure('TNotebook.Tab', padding=(20, 2))
        style.map('TNotebook.Tab', padding=[('selected', (20, 3))])
        
        self.placeholder_icon = self._create_placeholder()
        self.current_icon = None
        self.current_files_tree = {}
        
        # --- Menú Contextual (Copiar) ---
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy Text", command=self._copy_text)
        self.active_text_widget = None

        self.create_widgets()

    def _create_placeholder(self):
        if HAS_PIL:
            img = Image.new('RGB', ICON_SIZE, color=COLOR_PLACEHOLDER_BG)
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, ICON_SIZE[0]-1, ICON_SIZE[1]-1], outline=COLOR_PLACEHOLDER_BORDER, width=2)
            return ImageTk.PhotoImage(img)
        return tk.PhotoImage(width=ICON_SIZE[0], height=ICON_SIZE[1])

    def create_widgets(self):
        # --- Cabecera Principal ---
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)
        
        left_header = ttk.Frame(top_frame)
        left_header.pack(side=tk.LEFT, fill=tk.Y)
        
        self.lbl_icon = ttk.Label(left_header, image=self.placeholder_icon)
        self.lbl_icon.pack(side=tk.LEFT, padx=(0, 15))
        
        text_header = ttk.Frame(left_header)
        text_header.pack(side=tk.LEFT, expand=True, fill=tk.Y)
        
        self.lbl_app_name = ttk.Label(text_header, text="No APK Loaded", font=FONT_TITLE)
        self.lbl_app_name.pack(side=tk.TOP, anchor="sw", expand=True)
        
        self.lbl_app_package = ttk.Label(text_header, text="Select an application file to begin analysis.", font=FONT_SUBTITLE, foreground="#666666")
        self.lbl_app_package.pack(side=tk.TOP, anchor="nw", expand=True)
        
        self.btn_load = ttk.Button(top_frame, text="Load APK", command=self.load_apk)
        self.btn_load.pack(side=tk.RIGHT)

        # --- Barra de Estado (Footer) ---
        footer_frame = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.lbl_status = ttk.Label(footer_frame, text="Ready.", foreground="gray")
        self.lbl_status.pack(side=tk.LEFT, padx=10, pady=2)

        # --- Pestañas ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        self.tab_info = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_info, text="Information")
        self.scroll_frame = ScrollableFrame(self.tab_info)
        self.scroll_frame.pack(expand=True, fill=tk.BOTH)
        
        self.tab_manifest = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_manifest, text="Manifest.xml")
        
        self.tab_manifest.rowconfigure(0, weight=1)
        self.tab_manifest.columnconfigure(0, weight=1)
        
        self.txt_manifest = tk.Text(self.tab_manifest, wrap=tk.NONE, font=FONT_MONO, borderwidth=0, bg=COLOR_TEXT_BG)
        v_scroll_man = ttk.Scrollbar(self.tab_manifest, orient="vertical", command=self.txt_manifest.yview)
        h_scroll_man = ttk.Scrollbar(self.tab_manifest, orient="horizontal", command=self.txt_manifest.xview)
        
        self.txt_manifest.configure(yscrollcommand=v_scroll_man.set, xscrollcommand=h_scroll_man.set)
        
        self.txt_manifest.grid(row=0, column=0, sticky="nsew")
        v_scroll_man.grid(row=0, column=1, sticky="ns")
        h_scroll_man.grid(row=1, column=0, sticky="ew")
        
        # Enlazar menú contextual al Manifest
        self.txt_manifest.bind("<Button-3>", self._show_context_menu)

        # --- Pestaña Files (listado jerárquico del APK) ---
        self.tab_files = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_files, text="Files")

        # Configurar pesos de fila para que la tabla ocupe todo el espacio y el buscador se quede abajo
        self.tab_files.rowconfigure(0, weight=1)
        self.tab_files.rowconfigure(1, weight=0)
        self.tab_files.rowconfigure(2, weight=0)
        self.tab_files.columnconfigure(0, weight=1)

        files_columns = ("type", "size", "compressed", "modified")
        self.tree_files = ttk.Treeview(self.tab_files, columns=files_columns, show="tree headings")

        # Alineación a la izquierda generalizada
        self.tree_files.heading("#0", text="Name", anchor="w")
        self.tree_files.column("#0", width=380, minwidth=200, stretch=True, anchor="w")

        self.tree_files.heading("type", text="Type", anchor="w")
        self.tree_files.column("type", width=120, minwidth=80, stretch=False, anchor="w")

        self.tree_files.heading("size", text="Size", anchor="w")
        self.tree_files.column("size", width=100, minwidth=70, stretch=False, anchor="w")

        self.tree_files.heading("compressed", text="Compressed", anchor="w")
        self.tree_files.column("compressed", width=100, minwidth=70, stretch=False, anchor="w")

        self.tree_files.heading("modified", text="Modified", anchor="w")
        self.tree_files.column("modified", width=150, minwidth=130, stretch=False, anchor="w")

        v_scroll_files = ttk.Scrollbar(self.tab_files, orient="vertical", command=self.tree_files.yview)
        h_scroll_files = ttk.Scrollbar(self.tab_files, orient="horizontal", command=self.tree_files.xview)
        
        # Función para ocultar el scroll horizontal automáticamente
        def auto_hide_files_h_scroll(first, last):
            if float(first) <= 0.0 and float(last) >= 1.0:
                h_scroll_files.grid_remove()
            else:
                h_scroll_files.grid(row=1, column=0, sticky="ew")
            h_scroll_files.set(first, last)

        self.tree_files.configure(yscrollcommand=v_scroll_files.set, xscrollcommand=auto_hide_files_h_scroll)

        self.tree_files.grid(row=0, column=0, sticky="nsew")
        v_scroll_files.grid(row=0, column=1, sticky="ns")

        # Se quita la fuente bold en carpetas
        self.tree_files.tag_configure("folder", background=COLOR_FOLDER_BG, font=FONT_MONO_SMALL)
        self.tree_files.tag_configure("file", font=FONT_MONO_SMALL)

        # Buscador / Filtro movido a la parte inferior (fila 2)
        filter_frame = ttk.Frame(self.tab_files)
        filter_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.entry_filter = ttk.Entry(filter_frame)
        self.entry_filter.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_filter.bind("<KeyRelease>", self._apply_file_filter)

    def load_apk(self):
        apk_path = filedialog.askopenfilename(
            title="Select APK file",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")]
        )
        if apk_path:
            self.start_analysis(apk_path)

    def start_analysis(self, apk_path):
        if not os.path.exists(apk_path):
            messagebox.showerror("Error", f"File not found:\n{apk_path}")
            return

        self._set_status(f"Analyzing: {os.path.basename(apk_path)}... (Please wait)", "blue")
        self.btn_load.config(state=tk.DISABLED)
        self.lbl_icon.config(image=self.placeholder_icon)
        self.lbl_app_name.config(text="Analyzing APK...")
        self.lbl_app_package.config(text=os.path.basename(apk_path))
        self.current_icon = None
        self.entry_filter.delete(0, tk.END)
        
        for widget in self.scroll_frame.inner_frame.winfo_children():
            widget.destroy()
        self.txt_manifest.configure(state="normal")
        self.txt_manifest.delete(1.0, tk.END)
        self.tree_files.delete(*self.tree_files.get_children())

        threading.Thread(target=self.analyze_apk_thread, args=(apk_path,), daemon=True).start()

    def _set_status(self, message, color="gray"):
        self.root.after(0, lambda: self.lbl_status.config(text=message, foreground=color))

    # ==========================================
    # LÓGICA DE EXTRACCIÓN (ANDROGUARD CORE)
    # ==========================================
    def analyze_apk_thread(self, apk_path):
        try:
            a = APK(apk_path)
            
            pil_image = self._extract_icon(a)
            data = {
                'App Information': self._get_app_info(a),
                'Security & Operations': self._get_security(a),
                'Components & Intents': self._get_components(a),
                'Extras & Libraries': self._get_trackers_and_libs(a)
            }
            manifest_xml = self._format_manifest(a)
            self.current_files_tree = self._build_files_tree(apk_path)
            
            self.root.after(0, lambda: self.render_gui(data, manifest_xml, pil_image))
            self._set_status("Analysis completed successfully.", "green")
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred while analyzing the APK:\n{str(e)}"))
            self._set_status("Analysis failed.", "red")
            self.root.after(0, lambda: self.lbl_app_name.config(text="Error loading APK"))
        finally:
            self.root.after(0, lambda: self.btn_load.config(state=tk.NORMAL))

    def _extract_icon(self, a):
        if not HAS_PIL:
            return None
        try:
            icon_path = a.get_app_icon(max_dpi=True)
            base_name = "ic_launcher"
            
            if icon_path:
                if icon_path.lower().endswith(('.png', '.webp', '.jpg')):
                    icon_data = a.get_file(icon_path)
                    if icon_data:
                        img = Image.open(io.BytesIO(icon_data))
                        return img.resize(ICON_SIZE, Image.Resampling.LANCZOS)
                base_name = os.path.splitext(os.path.basename(icon_path))[0]
            else:
                xml_elem = a.get_android_manifest_xml()
                if xml_elem is not None:
                    app_tag = xml_elem.find(".//application")
                    if app_tag is not None:
                        icon_ref = app_tag.get(f"{ANDROID_NS}icon") or app_tag.get(f"{ANDROID_NS}roundIcon")
                        if icon_ref and "/" in icon_ref:
                            base_name = icon_ref.split("/")[-1]

            matches = [f for f in a.get_files() if os.path.splitext(os.path.basename(f))[0] == base_name and f.lower().endswith(('.png', '.webp', '.jpg'))]

            dpi_scores = {'xxxhdpi': 5, 'xxhdpi': 4, 'xhdpi': 3, 'hdpi': 2, 'mdpi': 1}
            matches.sort(key=lambda p: next((v for k, v in dpi_scores.items() if k in p.lower()), 0), reverse=True)

            for match in matches:
                try:
                    img = Image.open(io.BytesIO(a.get_file(match)))
                    return img.resize(ICON_SIZE, Image.Resampling.LANCZOS)
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _get_app_info(self, a):
        archs = {f.split("/")[1] for f in a.get_files() if f.startswith("lib/") and len(f.split("/")) > 1}
        return {
            'App name': a.get_app_name(),
            'Package name': a.get_package(),
            'Version': a.get_androidversion_name(),
            'Version code': a.get_androidversion_code(),
            'Split / Multidex': "Yes" if a.is_multidex() else "No",
            'Architectures': ", ".join(archs) if archs else "None / Unknown",
            'Min SDK': a.get_min_sdk_version(),
            'Target SDK': a.get_target_sdk_version(),
            'Max SDK': a.get_max_sdk_version(),
            'Effective SDK': a.get_effective_target_sdk_version()
        }

    def _get_security(self, a):
        perms, appops = [], []
        for p in a.get_permissions():
            (perms if p.startswith("android.permission.") else appops).append(p)
            
        certs = []
        for cert in a.get_certificates():
            try:
                certs.append(f"Issuer: {cert.issuer.human_friendly}\nSubject: {cert.subject.human_friendly}")
            except:
                certs.append("Unknown / Encrypted Certificate")

        return {
            'Permissions': sorted(perms),
            'AppOps / Custom Perms': sorted(appops),
            'Certificates': certs
        }

    def _get_components(self, a):
        pkg_name = a.get_package()
        intent_actions = set()
        
        try:
            xml = a.get_android_manifest_xml()
            if xml is not None:
                for tag in ['activity', 'activity-alias', 'service', 'receiver', 'provider']:
                    for comp in xml.iter(tag):
                        exported = comp.get(f"{ANDROID_NS}exported", "").lower()
                        has_filters = comp.find('intent-filter') is not None
                        
                        if exported == 'true' or (not exported and has_filters):
                            comp_name = comp.get(f"{ANDROID_NS}name", "Unknown")
                            
                            if comp_name.startswith("."):
                                comp_name = pkg_name + comp_name
                            elif "." not in comp_name and comp_name != "Unknown":
                                comp_name = f"{pkg_name}.{comp_name}"
                                
                            comp_type = tag.capitalize()
                            
                            for filter_node in comp.iter('intent-filter'):
                                actions = []
                                extras = []
                                
                                for node in filter_node:
                                    if node.tag == 'action':
                                        name = node.get(f"{ANDROID_NS}name")
                                        if name: actions.append(name)
                                        
                                    elif node.tag == 'category':
                                        cat = node.get(f"{ANDROID_NS}name")
                                        if cat:
                                            clean_cat = cat.replace("android.intent.category.", "")
                                            extras.append(f"category='{clean_cat}'")
                                            
                                    elif node.tag == 'data':
                                        mime = node.get(f"{ANDROID_NS}mimeType")
                                        scheme = node.get(f"{ANDROID_NS}scheme")
                                        host = node.get(f"{ANDROID_NS}host")
                                        path = node.get(f"{ANDROID_NS}path")
                                        path_prefix = node.get(f"{ANDROID_NS}pathPrefix")
                                        
                                        if mime: extras.append(f"mimeType='{mime}'")
                                        if scheme: extras.append(f"scheme='{scheme}'")
                                        if host: extras.append(f"host='{host}'")
                                        if path: extras.append(f"path='{path}'")
                                        if path_prefix: extras.append(f"pathPrefix='{path_prefix}'")
                                        
                                extras.append(f"{comp_type}='{comp_name}'")
                                extras_str = ", ".join(extras)
                                
                                for act in actions:
                                    intent_actions.add(f"{act} ( {extras_str} )")
        except Exception:
            pass

        return {
            'Activities': sorted(a.get_activities()),
            'Services': sorted(a.get_services()),
            'Receivers': sorted(a.get_receivers()),
            'Providers': sorted(a.get_providers()),
            'Intent Actions': sorted(list(intent_actions))
        }

    def _get_trackers_and_libs(self, a):
        packages = set()
        for dex in a.get_all_dex():
            try:
                for c in DEX(dex).get_classes():
                    name = str(getattr(c, 'name', getattr(c, 'get_name', lambda: '')())).lstrip('L')
                    parts = name.split('/')
                    if len(parts) > 1:
                        packages.add(".".join(parts[:3] if len(parts) > 3 else parts[:-1]))
            except:
                pass

        trackers = [f"{t_name} (Found in: {pkg})" for pkg in packages for t_key, t_name in KNOWN_TRACKERS.items() if t_key in pkg.lower()]
        
        return {
            'Hardware Features': a.get_features(),
            'Libraries': a.get_libraries(),
            'Trackers': sorted(list(set(trackers)))
        }

    def _format_manifest(self, a):
        try:
            xml = a.get_android_manifest_xml()
            if xml is None: return "Manifest XML is missing or corrupted."
            
            raw_xml = etree.tostring(xml, encoding="utf-8") if HAS_LXML else ET.tostring(xml, encoding="utf-8")
            pretty = minidom.parseString(raw_xml).toprettyxml(indent="    ")
            return os.linesep.join([s for s in pretty.splitlines() if s.strip()])
        except Exception as e:
            return f"Error processing Manifest:\n{str(e)}"

    def _build_files_tree(self, apk_path):
        root_node = {}
        try:
            with zipfile.ZipFile(apk_path, 'r') as zf:
                for info in zf.infolist():
                    if info.is_dir() or not info.filename:
                        continue
                    parts = [p for p in info.filename.split('/') if p]
                    if not parts:
                        continue
                    node = root_node
                    for i, part in enumerate(parts):
                        is_last = (i == len(parts) - 1)
                        if part not in node:
                            node[part] = {'__children__': {}, '__is_file__': False, '__size__': 0}
                        if is_last:
                            try:
                                mtime = datetime(*info.date_time)
                                mtime_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception:
                                mtime_str = ""
                            node[part]['__is_file__'] = True
                            node[part]['__size__'] = info.file_size
                            node[part]['__compressed__'] = info.compress_size
                            node[part]['__modified__'] = mtime_str
                        node = node[part]['__children__']
        except Exception:
            pass

        self._aggregate_folder_sizes(root_node)
        return root_node

    def _aggregate_folder_sizes(self, node_dict):
        """Suma recursivamente tamaño y tamaño compreso, y busca la última fecha modificada"""
        total_size = 0
        total_compressed = 0
        latest_modified = ""

        for meta in node_dict.values():
            if meta.get('__is_file__'):
                total_size += meta.get('__size__', 0)
                total_compressed += meta.get('__compressed__', 0)
                mtime = meta.get('__modified__', "")
                if mtime > latest_modified:
                    latest_modified = mtime
            else:
                folder_size, folder_comp, folder_mod = self._aggregate_folder_sizes(meta.get('__children__', {}))
                meta['__size__'] = folder_size
                meta['__compressed__'] = folder_comp
                meta['__modified__'] = folder_mod
                
                total_size += folder_size
                total_compressed += folder_comp
                if folder_mod > latest_modified:
                    latest_modified = folder_mod
                    
        return total_size, total_compressed, latest_modified

    @staticmethod
    def _human_size(num_bytes):
        try:
            num = float(num_bytes)
        except (TypeError, ValueError):
            return "-"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if num < 1024.0:
                return f"{num:.0f} {unit}" if unit == 'B' else f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} TB"

    def _apply_file_filter(self, event=None):
        query = self.entry_filter.get().strip().lower()
        self.tree_files.delete(*self.tree_files.get_children())
        
        if not query:
            self._populate_files_tree(self.current_files_tree)
            return
            
        filtered_tree = self._filter_tree_recursive(self.current_files_tree, query)
        self._populate_files_tree(filtered_tree)

    def _filter_tree_recursive(self, node_dict, query, force_include=False):
        filtered = {}
        for name, meta in node_dict.items():
            matches_name = query in name.lower()
            should_include = force_include or matches_name
            
            if meta.get('__is_file__'):
                if should_include:
                    filtered[name] = meta
            else:
                children = self._filter_tree_recursive(meta.get('__children__', {}), query, should_include)
                if children or should_include:
                    new_meta = meta.copy()
                    new_meta['__children__'] = children
                    filtered[name] = new_meta
        return filtered

    def _populate_files_tree(self, node_dict, parent_iid=""):
        entries = sorted(
            node_dict.items(),
            key=lambda kv: (kv[1].get('__is_file__', False), kv[0].lower())
        )
        for name, meta in entries:
            is_file = meta.get('__is_file__', False)
            size_str = self._human_size(meta.get('__size__', 0))
            compressed_str = self._human_size(meta.get('__compressed__', 0))
            modified_str = meta.get('__modified__', "")

            if is_file:
                ext = os.path.splitext(name)[1].lstrip('.').upper() + " File" or "File"
                self.tree_files.insert(
                    parent_iid, tk.END, text=f" 📄 {name}",
                    values=(ext, size_str, compressed_str, modified_str),
                    tags=('file',)
                )
            else:
                child_count = len(meta.get('__children__', {}))
                iid = self.tree_files.insert(
                    parent_iid, tk.END, text=f" 📁 {name}",
                    values=(f"Directory ({child_count})", size_str, compressed_str, modified_str),
                    open=True, tags=('folder',)
                )
                self._populate_files_tree(meta.get('__children__', {}), iid)

    # ==========================================
    # LÓGICA DE RENDERIZADO UI E INTERACTIVIDAD
    # ==========================================
    def render_gui(self, data, manifest_xml, pil_image):
        if pil_image and HAS_PIL:
            self.current_icon = ImageTk.PhotoImage(pil_image)
            self.lbl_icon.config(image=self.current_icon)
        
        app_info = data.get('App Information', {})
        self.lbl_app_name.config(text=app_info.get('App name', 'Unknown App'))
        self.lbl_app_package.config(text=app_info.get('Package name', 'Unknown Package'))
        
        parent = self.scroll_frame.inner_frame
        for row_idx, (section_title, fields) in enumerate(data.items()):
            frame = ttk.LabelFrame(parent, text=section_title)
            frame.grid(row=row_idx, column=0, sticky="ew", padx=15, pady=10)
            parent.columnconfigure(0, weight=1)
            
            for inner_row, (label, value) in enumerate(fields.items()):
                if isinstance(value, list):
                    txt_widget = self._create_text_list_field(frame, inner_row, label, value)
                    if label == 'Intent Actions':
                        txt_widget.bind("<Double-Button-1>", self._on_intent_double_click)
                else:
                    self._create_entry_field(frame, inner_row, label, value)

        self.txt_manifest.configure(state="normal")
        self.txt_manifest.insert(tk.END, manifest_xml)
        self._highlight_xml(self.txt_manifest)
        self.txt_manifest.configure(state="disabled")

        self._apply_file_filter()

    def _highlight_xml(self, txt_widget):
        """Sintaxis highlighting básico estilo VS Code para XML."""
        content = txt_widget.get("1.0", tk.END)
        
        txt_widget.tag_configure("xml_tag", foreground="#800000") # Marrón
        txt_widget.tag_configure("xml_attr", foreground="#FF0000") # Rojo
        txt_widget.tag_configure("xml_value", foreground="#0000FF") # Azul
        txt_widget.tag_configure("xml_comment", foreground="#008000", font=FONT_MONO_SMALL + ("italic",)) # Verde
        
        for match in re.finditer(r'<[^>]+>', content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            txt_widget.tag_add("xml_tag", start, end)
            
            tag_str = match.group()
            for amatch in re.finditer(r'([a-zA-Z0-9_:-]+)\s*=\s*("[^"]*"|\'[^\']*\')', tag_str):
                a_start = match.start() + amatch.start(1)
                a_end = match.start() + amatch.end(1)
                v_start = match.start() + amatch.start(2)
                v_end = match.start() + amatch.end(2)
                
                txt_widget.tag_add("xml_attr", f"1.0 + {a_start} chars", f"1.0 + {a_end} chars")
                txt_widget.tag_add("xml_value", f"1.0 + {v_start} chars", f"1.0 + {v_end} chars")
                
        for match in re.finditer(r'<!--.*?-->', content, re.DOTALL):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            txt_widget.tag_add("xml_comment", start, end)
            txt_widget.tag_raise("xml_comment")

    def _create_entry_field(self, parent, row, label_text, value):
        ttk.Label(parent, text=label_text, width=25).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        
        entry = ttk.Entry(parent)
        entry.insert(0, str(value) if value is not None else "")
        entry.configure(state="readonly")
        entry.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        parent.columnconfigure(1, weight=1)

    def _create_text_list_field(self, parent, row, label_text, items):
        ttk.Label(parent, text=f"{label_text} ({len(items)})", width=25).grid(row=row, column=0, sticky="nw", padx=10, pady=5)
        
        display_text = ("\n\n" if "Certificates" in label_text else "\n").join(items) if items else "None found"
        
        actual_lines = display_text.count('\n') + 1
        if actual_lines < MIN_LIST_LINES:
            display_text += '\n' * (MIN_LIST_LINES - actual_lines)
            actual_lines = MIN_LIST_LINES

        container = ttk.Frame(parent)
        container.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        parent.columnconfigure(1, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        
        txt = tk.Text(container, height=actual_lines, wrap=tk.NONE, borderwidth=1, relief="solid", bg=COLOR_TEXT_BG, font=FONT_MONO_SMALL)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=txt.xview)
        
        def auto_hide_scrollbar(first, last):
            if float(first) <= 0.0 and float(last) >= 1.0:
                h_scroll.grid_remove()
            else:
                h_scroll.grid(row=1, column=0, sticky="ew")
            h_scroll.set(first, last)

        txt.configure(xscrollcommand=auto_hide_scrollbar)
        txt.grid(row=0, column=0, sticky="ew")
        
        txt.insert(tk.END, display_text)
        txt.configure(state="disabled")

        txt.tag_configure("marked_line", background=COLOR_MARK_BG)
        
        # Lógica no invasiva para la selección.
        # Desmarca al pulsar (para limpiezas) y marca al soltar SÓLO si no se ha arrastrado una selección.
        txt.bind("<Button-1>", lambda e: e.widget.tag_remove("marked_line", "1.0", tk.END))
        txt.bind("<ButtonRelease-1>", self._on_line_click)
        txt.bind("<Button-3>", self._show_context_menu)

        return txt

    def _on_line_click(self, event):
        widget = event.widget
        # Si el usuario ha seleccionado texto (arrastrando), evitamos sobreescribir con el remarcado.
        if widget.tag_ranges(tk.SEL):
            return

        index = widget.index(f"@{event.x},{event.y}")
        line_num = index.split('.')[0]
        
        widget.tag_remove("marked_line", "1.0", tk.END)
        widget.tag_add("marked_line", f"{line_num}.0", f"{line_num}.end")

    def _show_context_menu(self, event):
        """Muestra el menú contextual de copiar."""
        self.active_text_widget = event.widget
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _copy_text(self):
        """Copia el texto seleccionado o la línea entera marcada."""
        if not self.active_text_widget:
            return
            
        try:
            if self.active_text_widget.tag_ranges(tk.SEL):
                text_to_copy = self.active_text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                ranges = self.active_text_widget.tag_ranges("marked_line")
                if ranges:
                    text_to_copy = self.active_text_widget.get(ranges[0], ranges[1])
                else:
                    text_to_copy = ""
                    
            if text_to_copy:
                self.root.clipboard_clear()
                self.root.clipboard_append(text_to_copy)
        except Exception:
            pass

    # --- Lógica del Pop-up de Intents ---
    def _on_intent_double_click(self, event):
        txt_widget = event.widget
        index = txt_widget.index(f"@{event.x},{event.y}")
        line_num = index.split('.')[0]
        line_text = txt_widget.get(f"{line_num}.0", f"{line_num}.end").strip()
        
        if not line_text or line_text == "None found":
            return
            
        self._open_intent_dialog(line_text)

    def _open_intent_dialog(self, line_text):
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("Intent Details")
            dialog.minsize(550, 150)
            dialog.transient(self.root)
            
            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            action = line_text
            extras_str = ""
            
            if " ( " in action and action.endswith(" )"):
                action, extras_str = action.split(" ( ", 1)
                extras_str = extras_str[:-2]
                
            fields = {"Action": action}
            
            if extras_str:
                for extra in extras_str.split(", "):
                    if "=" in extra:
                        key, value = extra.split("=", 1)
                        key = key.strip().capitalize()
                        value = value.strip().strip("'").strip('"') 
                        
                        if key in fields:
                            fields[key] += f", {value}"
                        else:
                            fields[key] = value

            row_idx = 0
            for label_text, value_text in fields.items():
                ttk.Label(main_frame, text=label_text, width=15).grid(row=row_idx, column=0, sticky="w", pady=5)
                
                entry = ttk.Entry(main_frame, font=FONT_MONO)
                entry.insert(0, str(value_text))
                entry.configure(state="readonly")
                entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=(10, 0))
                
                main_frame.columnconfigure(1, weight=1)
                row_idx += 1
                
            btn_close = ttk.Button(main_frame, text="Close", command=dialog.destroy)
            btn_close.grid(row=row_idx, column=0, columnspan=2, pady=(20, 0))
            
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
            x = max(x, 0)
            y = max(y, 0)
            dialog.geometry(f"+{x}+{y}")

            dialog.deiconify()
            dialog.lift()
            dialog.attributes('-topmost', True)
            dialog.after(150, lambda: dialog.attributes('-topmost', False))
            dialog.focus_force()
            dialog.grab_set()

        except Exception as e:
            messagebox.showerror("Parse Error", f"Could not load intent details:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ApkAnalyzerApp(root)
    
    if len(sys.argv) > 1:
        root.after(100, lambda: app.start_analysis(sys.argv[1]))
    
    root.mainloop()