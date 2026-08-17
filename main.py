import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
import time
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from urllib.parse import urlparse, parse_qs
import base64
import re
import os
from tkinter import filedialog
import socket
import ssl

class VPNConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VPN Конфигуратор")
        self.root.geometry("1200x750")
        self.root.configure(bg="#f0f2f5")
        
        # Настройка стилей
        self.setup_styles()
        
        self.ping_results = []
        self.is_testing = False
        self.test_thread = None
        self.current_subscription = []
        self.history = []
        self.history_file = "vpn_history.json"
        self.proxy_list = []
        self.current_proxy_index = 0
        
        # Загружаем список прокси
        self.load_proxies()
        
        self.load_history()
        self.setup_ui()
        
    def setup_styles(self):
        # Современные цвета
        self.colors = {
            'bg': '#f0f2f5',
            'bg2': '#ffffff',
            'bg3': '#e8eaed',
            'accent': '#4a6cf7',
            'accent2': '#6c5ce7',
            'success': '#00b894',
            'warning': '#fdcb6e',
            'danger': '#e17055',
            'text': '#2d3436',
            'text2': '#636e72',
            'border': '#dfe6e9',
        }
        
    def load_proxies(self):
        """Загрузка списка прокси"""
        self.proxy_list = [
            {'http': 'http://proxy1:8080', 'https': 'http://proxy1:8080'},
            {'http': 'http://proxy2:8080', 'https': 'http://proxy2:8080'},
            {'http': 'http://proxy3:8080', 'https': 'http://proxy3:8080'},
            # Добавьте свои прокси здесь
        ]
        
    def setup_ui(self):
        # Главный контейнер
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(header_frame, text="🚀 VPN Конфигуратор", 
                        font=("Segoe UI", 28, "bold"), 
                        bg=self.colors['bg'], fg=self.colors['text'])
        title.pack(side=tk.LEFT)
        
        # Карточка статуса
        status_card = tk.Frame(header_frame, bg=self.colors['bg2'], 
                              relief=tk.RAISED, bd=1)
        status_card.pack(side=tk.RIGHT)
        
        self.status_label = tk.Label(status_card, text="✅ Готов к работе", 
                                    bg=self.colors['bg2'], fg=self.colors['success'],
                                    font=("Segoe UI", 11), padx=15, pady=8)
        self.status_label.pack()
        
        # Основной контент - две колонки
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая колонка
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Правая колонка
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # --- ЛЕВАЯ КОЛОНКА ---
        # Режимы работы
        self.create_card(left_frame, "📌 Режим работы", self.create_mode_selector)
        
        # Ввод данных
        self.create_card(left_frame, "📝 Ввод данных", self.create_input_area)
        
        # --- ПРАВАЯ КОЛОНКА ---
        # Результат
        self.create_card(right_frame, "📄 Результат", self.create_output_area)
        
        # --- НИЖНЯЯ ЧАСТЬ ---
        # Таблица серверов
        self.create_card(main_frame, "📊 Сервера", self.create_table, pack_bottom=True)
        
        # Панель действий
        self.create_action_panel(main_frame)
        
    def create_card(self, parent, title, content_func, pack_bottom=False):
        """Создание карточки с содержимым"""
        card = tk.Frame(parent, bg=self.colors['bg2'], relief=tk.RAISED, bd=1)
        if pack_bottom:
            card.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        else:
            card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Заголовок карточки
        header = tk.Frame(card, bg=self.colors['bg2'])
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        tk.Label(header, text=title, font=("Segoe UI", 12, "bold"),
                bg=self.colors['bg2'], fg=self.colors['text']).pack(anchor=tk.W)
        
        # Содержимое
        content = tk.Frame(card, bg=self.colors['bg2'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        content_func(content)
        
    def create_mode_selector(self, parent):
        """Создание переключателя режимов"""
        modes_frame = tk.Frame(parent, bg=self.colors['bg2'])
        modes_frame.pack(fill=tk.X)
        
        self.mode_var = tk.StringVar(value="sub_to_servers")
        modes = [
            ("🌐 Подписка → Сервера", "sub_to_servers"),
            ("🔗 VLESS → JSON", "vless_to_json"),
            ("📄 JSON → VLESS", "json_to_vless"),
            ("📋 Подписка → VLESS", "sub_to_vless")
        ]
        
        for i, (text, value) in enumerate(modes):
            rb = tk.Radiobutton(modes_frame, text=text, variable=self.mode_var, 
                              value=value, bg=self.colors['bg2'], 
                              fg=self.colors['text'], font=("Segoe UI", 10),
                              selectcolor="#d4d4d4", activebackground=self.colors['bg2'])
            rb.grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=3)
        
        # Настройки проверки
        settings_frame = tk.Frame(parent, bg=self.colors['bg2'])
        settings_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(settings_frame, text="⏱ Интервал между проверками:", 
                bg=self.colors['bg2'], fg=self.colors['text2'],
                font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_interval_var = tk.StringVar(value="2")
        intervals = [("1 мин", "1"), ("2 мин", "2"), ("5 мин", "5"), ("10 мин", "10")]
        
        for text, value in intervals:
            rb = tk.Radiobutton(settings_frame, text=text, 
                              variable=self.test_interval_var, value=value,
                              bg=self.colors['bg2'], fg=self.colors['text'],
                              font=("Segoe UI", 9), selectcolor="#d4d4d4")
            rb.pack(side=tk.LEFT, padx=5)
        
        # Кнопки управления
        btn_frame = tk.Frame(parent, bg=self.colors['bg2'])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.create_modern_button(btn_frame, "📁 Открыть", self.open_file, "#636e72")
        self.create_modern_button(btn_frame, "💾 Сохранить", self.save_file, "#636e72")
        self.create_modern_button(btn_frame, "🗑️ Очистить", self.clear_all, "#e17055")
        
    def create_input_area(self, parent):
        """Создание области ввода"""
        self.input_text = scrolledtext.ScrolledText(parent, height=10, 
                                                     bg="#f8f9fa", fg=self.colors['text'],
                                                     insertbackground=self.colors['text'],
                                                     font=("Consolas", 10), 
                                                     wrap=tk.WORD,
                                                     relief=tk.FLAT,
                                                     borderwidth=1)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
    def create_output_area(self, parent):
        """Создание области вывода"""
        self.output_text = scrolledtext.ScrolledText(parent, height=10, 
                                                      bg="#f8f9fa", fg=self.colors['text'],
                                                      insertbackground=self.colors['text'],
                                                      font=("Consolas", 10), 
                                                      wrap=tk.WORD,
                                                      relief=tk.FLAT,
                                                      borderwidth=1)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
    def create_table(self, parent):
        """Создание таблицы серверов"""
        tree_frame = tk.Frame(parent, bg=self.colors['bg2'])
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Настройка стиля для Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background="#f8f9fa",
                       foreground=self.colors['text'],
                       rowheight=28,
                       fieldbackground="#f8f9fa")
        style.configure("Treeview.Heading", 
                       background=self.colors['bg3'],
                       foreground=self.colors['text'],
                       font=("Segoe UI", 10, "bold"))
        style.map('Treeview', 
                 background=[('selected', self.colors['accent'])])
        
        self.result_tree = ttk.Treeview(tree_frame, columns=('Server', 'Protocol', 'Ping', 'Status'), 
                                        show='headings', height=5)
        
        # Настройка колонок
        self.result_tree.heading('Server', text='Сервер')
        self.result_tree.heading('Protocol', text='Протокол')
        self.result_tree.heading('Ping', text='Пинг (мс)')
        self.result_tree.heading('Status', text='Статус')
        
        self.result_tree.column('Server', width=300)
        self.result_tree.column('Protocol', width=120)
        self.result_tree.column('Ping', width=120)
        self.result_tree.column('Status', width=120)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_action_panel(self, parent):
        """Создание панели действий"""
        panel = tk.Frame(parent, bg=self.colors['bg2'], relief=tk.RAISED, bd=1)
        panel.pack(fill=tk.X, pady=(10, 0))
        
        btn_frame = tk.Frame(panel, bg=self.colors['bg2'])
        btn_frame.pack(pady=10)
        
        self.create_modern_button(btn_frame, "▶️ Выполнить", self.process_input, self.colors['accent'])
        self.create_modern_button(btn_frame, "🔍 Проверить качество", self.check_quality, self.colors['accent2'])
        self.create_modern_button(btn_frame, "📡 Проверить сервера", self.start_ping_test, "#00b894")
        self.create_modern_button(btn_frame, "📊 Диаграмма", self.show_diagram, "#fdcb6e")
        self.create_modern_button(btn_frame, "📋 История", self.show_history, "#6c5ce7")
        
        # Прогресс-бар
        self.progress = ttk.Progressbar(panel, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=15)
        
    def create_modern_button(self, parent, text, command, color, width=None):
        """Создание современной кнопки"""
        btn = tk.Button(parent, text=text, command=command,
                       bg=color, fg='white', font=("Segoe UI", 10, "bold"),
                       padx=20, pady=8, relief=tk.FLAT, cursor="hand2",
                       width=width)
        btn.pack(side=tk.LEFT, padx=5)
        
        # Эффекты при наведении
        def on_enter(e):
            btn.config(bg=self.lighten_color(color))
        def on_leave(e):
            btn.config(bg=color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def lighten_color(self, color):
        colors = {
            '#4a6cf7': '#6b8cff',
            '#6c5ce7': '#8c7cf7',
            '#00b894': '#00d4a8',
            '#fdcb6e': '#fedb8e',
            '#e17055': '#e8907a',
            '#636e72': '#8a9499'
        }
        return colors.get(color, color)
    
    def process_input(self):
        """Обработка ввода"""
        input_data = self.input_text.get("1.0", tk.END).strip()
        if not input_data:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите данные")
            return
        
        mode = self.mode_var.get()
        
        try:
            if mode == "sub_to_servers":
                self.parse_subscription(input_data)
            elif mode == "vless_to_json":
                self.convert_vless_to_json(input_data)
            elif mode == "json_to_vless":
                self.convert_json_to_vless(input_data)
            elif mode == "sub_to_vless":
                self.subscription_to_vless(input_data)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка обработки: {str(e)}")
            self.status_label.config(text="❌ Ошибка обработки")
    
    def parse_subscription(self, data):
        """Парсинг подписки"""
        try:
            # Очищаем таблицу
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)
            
            self.current_subscription = []
            
            # Проверяем URL
            if data.startswith('http://') or data.startswith('https://'):
                self.status_label.config(text="📥 Загрузка подписки...")
                try:
                    response = requests.get(data, timeout=10)
                    content = response.text
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось загрузить подписку: {str(e)}")
                    return
            else:
                content = data
            
            # Декодируем base64
            try:
                cleaned = re.sub(r'\s+', '', content)
                decoded = base64.b64decode(cleaned).decode('utf-8')
                lines = decoded.split('\n')
            except:
                lines = content.split('\n')
            
            # Парсим каждую строку
            protocols = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                server_info = self.parse_server_line(line)
                if server_info:
                    self.current_subscription.append(server_info)
                    
                    protocol = server_info.get('protocol', 'other')
                    protocols[protocol] = protocols.get(protocol, 0) + 1
                    
                    self.result_tree.insert('', 'end', values=(
                        server_info.get('host', 'Неизвестно'),
                        protocol,
                        'N/A',
                        '⏳ Ожидание'
                    ))
            
            # Сохраняем в историю
            self.add_to_history("Парсинг подписки", 
                              f"Найдено {len(self.current_subscription)} серверов")
            
            # Выводим результат
            self.output_text.delete("1.0", tk.END)
            summary = f"📊 Анализ подписки:\n"
            summary += f"Всего серверов: {len(self.current_subscription)}\n"
            summary += f"Протоколы:\n"
            for proto, count in protocols.items():
                if count > 0:
                    summary += f"  • {proto}: {count}\n"
            
            self.output_text.insert("1.0", summary)
            self.status_label.config(text=f"✅ Найдено {len(self.current_subscription)} серверов")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обработать подписку: {str(e)}")
            self.status_label.config(text="❌ Ошибка парсинга")
    
    def parse_server_line(self, line):
        """Парсинг строки сервера"""
        try:
            if line.startswith('vless://'):
                parsed = urlparse(line)
                params = parse_qs(parsed.query)
                return {
                    'protocol': 'vless',
                    'host': parsed.hostname,
                    'port': parsed.port,
                    'uuid': parsed.path.lstrip('/'),
                    'raw': line,
                    'params': params
                }
            elif line.startswith('vmess://'):
                try:
                    vmess_data = base64.b64decode(line[8:]).decode('utf-8')
                    config = json.loads(vmess_data)
                    return {
                        'protocol': 'vmess',
                        'host': config.get('add', 'Неизвестно'),
                        'port': config.get('port', 'Неизвестно'),
                        'id': config.get('id', ''),
                        'raw': line
                    }
                except:
                    return None
            elif line.startswith('trojan://'):
                parsed = urlparse(line)
                return {
                    'protocol': 'trojan',
                    'host': parsed.hostname,
                    'port': parsed.port,
                    'raw': line
                }
            elif line.startswith('hysteria2://'):
                parsed = urlparse(line)
                return {
                    'protocol': 'hysteria2',
                    'host': parsed.hostname,
                    'port': parsed.port,
                    'raw': line
                }
            else:
                return None
        except:
            return None
    
    def subscription_to_vless(self, data):
        """Извлечение VLESS ссылок из подписки"""
        try:
            self.parse_subscription(data)
            
            vless_links = []
            for server in self.current_subscription:
                if server.get('protocol') == 'vless':
                    vless_links.append(server.get('raw', ''))
            
            self.output_text.delete("1.0", tk.END)
            if vless_links:
                result = f"🔗 Найдено {len(vless_links)} VLESS ссылок:\n\n"
                for i, link in enumerate(vless_links, 1):
                    result += f"{i}. {link}\n"
                self.output_text.insert("1.0", result)
                self.status_label.config(text=f"✅ Найдено {len(vless_links)} VLESS ссылок")
                self.add_to_history("Извлечение VLESS", f"Найдено {len(vless_links)} VLESS ссылок")
            else:
                self.output_text.insert("1.0", "❌ VLESS ссылки не найдены")
                self.status_label.config(text="❌ VLESS не найдены")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка извлечения VLESS: {str(e)}")
    
    def convert_vless_to_json(self, vless_url):
        try:
            parsed = urlparse(vless_url)
            params = parse_qs(parsed.query)
            
            config = {
                "protocol": "vless",
                "address": parsed.hostname,
                "port": parsed.port or 443,
                "uuid": parsed.path.lstrip('/'),
                "encryption": params.get('encryption', ['none'])[0],
                "flow": params.get('flow', [''])[0],
                "sni": params.get('sni', [''])[0],
                "fp": params.get('fp', [''])[0],
                "type": params.get('type', [''])[0],
                "security": params.get('security', [''])[0]
            }
            
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", json.dumps(config, indent=2))
            self.status_label.config(text="✅ VLESS → JSON")
            self.add_to_history("Конвертация VLESS → JSON", "Успешно")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка парсинга VLESS: {str(e)}")
    
    def convert_json_to_vless(self, json_data):
        try:
            if isinstance(json_data, str):
                config = json.loads(json_data)
            else:
                config = json_data
            
            if 'outbounds' in config:
                # Формат Xray/V2Ray
                for outbound in config.get('outbounds', []):
                    if outbound.get('protocol') == 'vless':
                        settings = outbound.get('settings', {})
                        vnext = settings.get('vnext', [{}])[0]
                        user = vnext.get('users', [{}])[0]
                        stream = outbound.get('streamSettings', {})
                        reality = stream.get('realitySettings', {})
                        
                        base = f"vless://{user.get('id')}@{vnext.get('address')}:{vnext.get('port')}"
                        params = []
                        params.append(f"encryption={user.get('encryption', 'none')}")
                        if user.get('flow'):
                            params.append(f"flow={user.get('flow')}")
                        if reality.get('serverName'):
                            params.append(f"sni={reality.get('serverName')}")
                        if reality.get('fingerprint'):
                            params.append(f"fp={reality.get('fingerprint')}")
                        if reality.get('publicKey'):
                            params.append(f"pbk={reality.get('publicKey')}")
                        if reality.get('shortId'):
                            params.append(f"sid={reality.get('shortId')}")
                        
                        vless_url = base + "?" + "&".join(params)
                        
                        self.output_text.delete("1.0", tk.END)
                        self.output_text.insert("1.0", vless_url)
                        self.status_label.config(text="✅ JSON → VLESS")
                        self.add_to_history("Конвертация JSON → VLESS", "Успешно")
                        return
                
                messagebox.showerror("Ошибка", "VLESS конфигурация не найдена в JSON")
            else:
                base = f"vless://{config['uuid']}@{config['address']}:{config['port']}"
                params = []
                
                for key in ['encryption', 'flow', 'sni', 'fp', 'type', 'security']:
                    if config.get(key):
                        params.append(f"{key}={config[key]}")
                
                vless_url = base + "?" + "&".join(params) if params else base
                
                self.output_text.delete("1.0", tk.END)
                self.output_text.insert("1.0", vless_url)
                self.status_label.config(text="✅ JSON → VLESS")
                self.add_to_history("Конвертация JSON → VLESS", "Успешно")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка конвертации JSON: {str(e)}")
    
    def start_ping_test(self):
        """Запуск проверки пинга через прокси"""
        if not self.current_subscription:
            messagebox.showwarning("Предупреждение", "Сначала распарсите подписку")
            return
        
        if self.is_testing:
            messagebox.showinfo("Информация", "Проверка уже запущена")
            return
        
        self.is_testing = True
        self.ping_results = []
        self.progress.start()
        self.status_label.config(text="📡 Проверка серверов...")
        
        # Обновляем статус в таблице
        for item in self.result_tree.get_children():
            self.result_tree.set(item, 'Ping', '⏳ Проверка...')
            self.result_tree.set(item, 'Status', '⏳')
        
        self.test_thread = threading.Thread(target=self.run_ping_test)
        self.test_thread.start()
    
    def check_via_proxy_get(self, host, port=443, timeout=5):
        """
        Проверка доступности через прокси с GET запросом
        Как в HAPP - реальный пинг через прокси
        """
        try:
            # Пробуем разные прокси
            for proxy in self.proxy_list:
                try:
                    start_time = time.time()
                    
                    # Формируем URL для проверки
                    url = f"https://{host}/"
                    
                    # Настраиваем прокси
                    proxies = {
                        'http': proxy.get('http'),
                        'https': proxy.get('https')
                    }
                    
                    # Выполняем GET запрос через прокси
                    response = requests.get(
                        url,
                        proxies=proxies,
                        timeout=timeout,
                        verify=False,  # Отключаем проверку SSL для скорости
                        allow_redirects=True,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                    )
                    
                    end_time = time.time()
                    ping_ms = (end_time - start_time) * 1000
                    
                    # Если получили ответ, возвращаем пинг
                    if response.status_code < 500:
                        return ping_ms
                        
                except requests.exceptions.Timeout:
                    continue
                except requests.exceptions.ConnectionError:
                    continue
                except requests.exceptions.ProxyError:
                    continue
                except Exception:
                    continue
            
            # Если все прокси не сработали, пробуем прямой запрос
            try:
                start_time = time.time()
                response = requests.get(
                    f"https://{host}/",
                    timeout=timeout,
                    verify=False,
                    allow_redirects=True,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                end_time = time.time()
                ping_ms = (end_time - start_time) * 1000
                
                if response.status_code < 500:
                    return ping_ms
            except:
                pass
            
            return None
            
        except Exception as e:
            return None
    
    def run_ping_test(self):
        """Запуск проверки пинга с интервалами"""
        try:
            interval_minutes = int(self.test_interval_var.get())
            total_checks = 5  # Количество проверок
            
            test_count = 0
            
            while test_count < total_checks and self.is_testing:
                # Выполняем пинг всех серверов
                batch_results = []
                
                for i, server in enumerate(self.current_subscription):
                    if not self.is_testing:
                        break
                    
                    host = server.get('host')
                    port = server.get('port', 443)
                    
                    if host:
                        # Реальный пинг через прокси
                        ping_ms = self.check_via_proxy_get(host, port)
                        
                        if ping_ms is not None:
                            batch_results.append({
                                'index': i,
                                'server': server,
                                'ping': ping_ms,
                                'time': datetime.now()
                            })
                            
                            self.root.after(0, lambda idx=i, ping=ping_ms: 
                                self.update_tree_ping(idx, ping))
                        else:
                            # Сервер недоступен
                            self.root.after(0, lambda idx=i: 
                                self.update_tree_ping_failed(idx))
                
                # Сортируем результаты по пингу (от меньшего к большему)
                if batch_results:
                    batch_results.sort(key=lambda x: x['ping'])
                    
                    # Обновляем порядок в таблице
                    self.root.after(0, self.sort_table_by_ping, batch_results)
                
                if batch_results:
                    self.ping_results.append({
                        'timestamp': datetime.now(),
                        'results': batch_results
                    })
                    
                    test_count += 1
                    avg_ping = sum(r['ping'] for r in batch_results) / len(batch_results)
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"📡 Проверка #{test_count}/{total_checks}: {len(batch_results)} серверов доступно, средний пинг: {avg_ping:.1f}мс"
                    ))
                    
                    # Сохраняем в историю
                    self.root.after(0, lambda: self.add_to_history(
                        f"Пинг проверка #{test_count}", 
                        f"{len(batch_results)} серверов, средний пинг: {avg_ping:.1f}мс"
                    ))
                else:
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"📡 Проверка #{test_count+1}/{total_checks}: Нет доступных серверов"
                    ))
                
                # Ждем интервал перед следующей проверкой
                if test_count < total_checks and self.is_testing:
                    time.sleep(interval_minutes * 60)  # Конвертируем минуты в секунды
            
            self.root.after(0, self.finish_test)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Проверка прервана: {str(e)}"))
            self.root.after(0, self.finish_test)
    
    def update_tree_ping_failed(self, index):
        """Обновление статуса для недоступного сервера"""
        items = self.result_tree.get_children()
        if index < len(items):
            self.result_tree.set(items[index], 'Ping', '❌')
            self.result_tree.set(items[index], 'Status', '🔴 Недоступен')
    
    def sort_table_by_ping(self, sorted_results):
        """Сортировка таблицы по пингу"""
        # Получаем все элементы
        items = self.result_tree.get_children()
        
        # Удаляем все элементы
        for item in items:
            self.result_tree.delete(item)
        
        # Добавляем отсортированные серверы
        for result in sorted_results:
            server = result['server']
            ping = result['ping']
            
            if ping < 100:
                status = '🟢 Отлично'
            elif ping < 200:
                status = '🟡 Хорошо'
            elif ping < 300:
                status = '🟠 Средне'
            else:
                status = '🔴 Плохо'
            
            self.result_tree.insert('', 'end', values=(
                server.get('host', 'Неизвестно'),
                server.get('protocol', 'unknown'),
                f'{ping:.1f}',
                status
            ))
    
    def update_tree_ping(self, index, ping):
        """Обновление пинга в таблице"""
        items = self.result_tree.get_children()
        if index < len(items):
            if ping < 100:
                status = '🟢 Отлично'
            elif ping < 200:
                status = '🟡 Хорошо'
            elif ping < 300:
                status = '🟠 Средне'
            else:
                status = '🔴 Плохо'
            
            self.result_tree.set(items[index], 'Ping', f'{ping:.1f}')
            self.result_tree.set(items[index], 'Status', status)
    
    def finish_test(self):
        """Завершение проверки"""
        self.is_testing = False
        self.progress.stop()
        
        if self.ping_results:
            self.status_label.config(text=f"✅ Проверка завершена! Выполнено {len(self.ping_results)} замеров")
        else:
            self.status_label.config(text="❌ Данные не получены")
    
    def check_quality(self):
        """Проверка качества подписки"""
        if not self.current_subscription:
            messagebox.showwarning("Предупреждение", "Сначала распарсите подписку")
            return
        
        # Анализ качества
        self.output_text.insert("1.0", "\n🔍 Анализ качества подписки:\n")
        
        if self.ping_results:
            all_pings = []
            for batch in self.ping_results:
                for result in batch['results']:
                    all_pings.append(result['ping'])
            
            if all_pings:
                avg_ping = sum(all_pings) / len(all_pings)
                min_ping = min(all_pings)
                max_ping = max(all_pings)
                median_ping = sorted(all_pings)[len(all_pings)//2]
                
                # Считаем количество доступных серверов
                online_servers = len(all_pings)
                total_servers = len(self.current_subscription)
                availability = (online_servers / total_servers) * 100 if total_servers > 0 else 0
                
                quality_text = f"""
📊 Результаты анализа:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Статистика:
   • Доступно серверов: {online_servers} из {total_servers} ({availability:.1f}%)
   • Средний пинг: {avg_ping:.1f} мс
   • Медианный пинг: {median_ping:.1f} мс
   • Минимальный пинг: {min_ping:.1f} мс
   • Максимальный пинг: {max_ping:.1f} мс

🏆 Оценка качества:
   """
                
                # Оценка на основе пинга и доступности
                if avg_ping < 100 and availability > 80:
                    quality_text += "   ⭐⭐⭐⭐⭐ Отличное качество!"
                elif avg_ping < 200 and availability > 60:
                    quality_text += "   ⭐⭐⭐⭐ Хорошее качество"
                elif avg_ping < 300 and availability > 40:
                    quality_text += "   ⭐⭐⭐ Среднее качество"
                else:
                    quality_text += "   ⭐⭐ Низкое качество"
                
                # Добавляем рекомендации
                quality_text += f"\n\n💡 Рекомендации:\n"
                if avg_ping < 100 and availability > 80:
                    quality_text += "   ✓ Подписка отличного качества, рекомендуется к использованию"
                elif avg_ping < 200 and availability > 60:
                    quality_text += "   ✓ Подписка хорошего качества, подходит для большинства задач"
                elif avg_ping < 300 and availability > 40:
                    quality_text += "   ⚠️ Подписка среднего качества, возможны задержки"
                else:
                    quality_text += "   ❌ Подписка низкого качества, рекомендуется найти альтернативу"
                
                # Добавляем лучшие серверы
                if len(all_pings) > 0:
                    sorted_pings = sorted([(r['server']['host'], r['ping']) for r in self.ping_results[-1]['results']], key=lambda x: x[1])
                    quality_text += f"\n\n🏆 Лучшие серверы:\n"
                    for i, (host, ping) in enumerate(sorted_pings[:5], 1):
                        quality_text += f"   {i}. {host} - {ping:.1f} мс\n"
                
                self.output_text.insert("1.0", quality_text + "\n")
                self.add_to_history("Анализ качества", f"Средний пинг: {avg_ping:.1f}мс, {online_servers} серверов")
            else:
                self.output_text.insert("1.0", "❌ Нет данных для анализа")
        else:
            self.output_text.insert("1.0", "❌ Сначала выполните проверку серверов")
        
        self.status_label.config(text="✅ Анализ завершен")
    
    def show_diagram(self):
        """Отображение диаграммы"""
        if not self.ping_results:
            messagebox.showinfo("Информация", "Нет данных для диаграммы. Запустите проверку.")
            return
        
        diagram_window = tk.Toplevel(self.root)
        diagram_window.title("📊 Диаграмма производительности")
        diagram_window.geometry("1000x700")
        diagram_window.configure(bg="#f0f2f5")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        fig.patch.set_facecolor('#f0f2f5')
        
        # 1. График пинга по времени
        timestamps = [p['timestamp'] for p in self.ping_results]
        avg_pings = [sum(r['ping'] for r in p['results']) / len(p['results']) 
                     for p in self.ping_results]
        
        ax1.plot(timestamps, avg_pings, marker='o', color='#4a6cf7', linewidth=2)
        ax1.set_title('Средний пинг по времени', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Время')
        ax1.set_ylabel('Пинг (мс)')
        ax1.grid(True, alpha=0.3)
        ax1.set_facecolor('#f8f9fa')
        
        # 2. Последние результаты серверов (отсортированные)
        if self.ping_results:
            latest = self.ping_results[-1]
            sorted_results = sorted(latest['results'], key=lambda x: x['ping'])
            servers = [r['server']['host'] for r in sorted_results][:10]
            pings = [r['ping'] for r in sorted_results][:10]
            
            colors = ['#00b894' if p < 100 else '#fdcb6e' if p < 200 else '#e17055' for p in pings]
            ax2.barh(servers, pings, color=colors)
            ax2.set_title('Производительность серверов (от лучшего к худшему)', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Пинг (мс)')
            ax2.set_facecolor('#f8f9fa')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=diagram_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Кнопка закрытия
        tk.Button(diagram_window, text="❌ Закрыть", 
                 command=diagram_window.destroy,
                 bg='#e17055', fg='white', font=("Segoe UI", 10, "bold"),
                 padx=20, pady=8, relief=tk.FLAT).pack(pady=10)
    
    def show_history(self):
        """Показ истории"""
        if not self.history:
            messagebox.showinfo("Информация", "История операций пуста")
            return
        
        history_window = tk.Toplevel(self.root)
        history_window.title("📜 История операций")
        history_window.geometry("600x400")
        history_window.configure(bg="#f0f2f5")
        
        # Список истории
        history_list = tk.Listbox(history_window, bg='#ffffff', 
                                 fg=self.colors['text'], font=("Segoe UI", 10),
                                 selectmode=tk.SINGLE)
        history_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for entry in reversed(self.history):
            time_str = datetime.fromisoformat(entry['timestamp']).strftime('%d.%m.%Y %H:%M')
            display = f"[{time_str}] {entry['action']}: {entry['details']}"
            history_list.insert(tk.END, display)
        
        # Кнопки
        btn_frame = tk.Frame(history_window, bg="#f0f2f5")
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(btn_frame, text="🗑️ Очистить", command=self.clear_history,
                 bg='#e17055', fg='white', font=("Segoe UI", 10),
                 padx=15, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📤 Экспорт", command=self.export_history,
                 bg='#4a6cf7', fg='white', font=("Segoe UI", 10),
                 padx=15, pady=5, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Закрыть", command=history_window.destroy,
                 bg='#636e72', fg='white', font=("Segoe UI", 10),
                 padx=15, pady=5, relief=tk.FLAT).pack(side=tk.RIGHT, padx=5)
    
    def add_to_history(self, action, details):
        """Добавление в историю"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        self.history.append(entry)
        self.save_history()
    
    def save_history(self):
        """Сохранение истории"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def load_history(self):
        """Загрузка истории"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except:
            self.history = []
    
    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Очистить всю историю?"):
            self.history = []
            self.save_history()
            messagebox.showinfo("Успех", "История очищена")
    
    def export_history(self):
        """Экспорт истории"""
        try:
            filename = f"история_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", f"История экспортирована в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {str(e)}")
    
    def open_file(self):
        """Открытие файла"""
        try:
            filename = filedialog.askopenfilename(
                title="Открыть файл",
                filetypes=[("JSON файлы", "*.json"), ("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
            )
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", content)
                self.status_label.config(text=f"📂 Загружен файл: {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")
    
    def save_file(self):
        """Сохранение файла"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Сохранить результат",
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
            )
            if filename:
                content = self.output_text.get("1.0", tk.END).strip()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_label.config(text=f"💾 Сохранено: {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {str(e)}")
    
    def clear_all(self):
        """Очистка всех данных"""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.ping_results = []
        self.current_subscription = []
        
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.status_label.config(text="✅ Готов к работе")

if __name__ == "__main__":
    root = tk.Tk()
    app = VPNConfigApp(root)
    root.mainloop()