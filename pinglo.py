import tkinter as tk
import subprocess
import threading
import time
import os
import csv
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import platform

class PingMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Pinglo")
        self.root.geometry("800x500")
        
        # Устанавливаем современную тему
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Используем тему clam для более современного вида
        
        # Настраиваем цвета
        bg_color = "#f5f5f5"  # Светло-серый фон
        accent_color = "#3498db"  # Голубой акцент
        
        # Настраиваем стили для элементов ttk
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TLabel', background=bg_color, font=('Segoe UI', 9))
        self.style.configure('TButton', font=('Segoe UI', 9))
        self.style.configure('TRadiobutton', background=bg_color, font=('Segoe UI', 9))
        self.style.configure('TEntry', font=('Segoe UI', 9))
        
        # Создаем стиль для кнопки Start
        self.style.configure('Start.TButton', background='#2ecc71', foreground='white')
        # Создаем стиль для кнопки Stop
        self.style.configure('Stop.TButton', background='#e74c3c', foreground='white')
        
        # Устанавливаем фон окна
        self.root.configure(bg=bg_color)
        
        # Устанавливаем минимальный размер окна
        self.root.minsize(1100, 400)
        
        # Устанавливаем начальный размер окна
        self.root.geometry("1100x500")
        
        # Создаем контекстное меню для вставки
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Paste", command=lambda: self.paste_from_clipboard(None))
        
        self.ip_addresses = []
        self.ping_interval = 2
        self.running = False
        self.ping_thread = None
        self.log_mode = tk.StringVar(value="combined")
        
        try:
            print("Creating widgets...")
            self.create_widgets()
            print("Widgets created successfully")
        except Exception as e:
            print(f"Error creating widgets: {str(e)}")
        
    def extract_response_time(self, output):
        """Извлекает время отклика из результата ping"""
        try:
            # Выводим полный вывод для отладки
            print(f"DEBUG - Full ping output:\n{output}")
            
            # Проверяем успешность пинга по коду возврата (уже проверено в ping_loop)
            # Если мы здесь, значит ping вернул код 0 (успешно)
            
            # Разбиваем на строки и убираем пустые
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            
            # Ищем строку с ответом
            for line in lines:
                # Проверяем как на английском, так и на русском
                if ("reply from" in line.lower() or 
                    "ответ от" in line.lower() or 
                    "reply" in line.lower() or
                    "ttl=" in line.lower() or
                    "время=" in line.lower() or
                    "time=" in line.lower()):
                    return line.strip()
            
            # Если не нашли конкретную строку с ответом, но ping успешен,
            # возвращаем первую непустую строку вывода
            if lines:
                return lines[0].strip()
            
            return "No response"
        except Exception as e:
            print(f"DEBUG - Error in extract_response_time: {str(e)}")
            return f"Error: {str(e)}"
        
    # Удаляем метод update_online_status, так как он больше не нужен
        
    def create_widgets(self):
        try:
            # Настраиваем глобальные привязки клавиш для всего окна
            self.setup_global_bindings()
            
            # Создаем панель с двумя фреймами
            main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
            main_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Создаем левый фрейм для элементов управления
            left_frame = ttk.Frame(main_panel, width=300)
            main_panel.add(left_frame, weight=1)
            
            # Создаем правый фрейм для отображения логов
            right_frame = ttk.Frame(main_panel)
            main_panel.add(right_frame, weight=2)
            
            # Заголовок для области логов
            log_header = ttk.Label(right_frame, text="Log Output")
            log_header.pack(anchor=tk.W, padx=5, pady=2)
            
            # Создаем фрейм для текстового поля и полосы прокрутки
            log_frame = ttk.Frame(right_frame)
            log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Создаем текстовое поле для отображения логов
            self.log_text = tk.Text(log_frame, wrap=tk.NONE, bg='#F8F9FA', width=80, height=20, font=('Consolas', 9))
            self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Добавляем полосу прокрутки
            log_scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
            log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.log_text.config(yscrollcommand=log_scrollbar.set)
            
            # Разрешаем выделение текста, но запрещаем редактирование
            self.log_text.config(state=tk.NORMAL)
            
            # Добавляем контекстное меню для копирования
            self.log_context_menu = tk.Menu(self.root, tearoff=0)
            self.log_context_menu.add_command(label="Copy", command=self.copy_selected_log)
            self.log_text.bind("<Button-3>", self.show_log_context_menu)
            
            # Добавляем привязку к Ctrl+C для копирования
            self.log_text.bind("<Control-c>", lambda event: self.copy_selected_log())
            self.log_text.bind("<Control-C>", lambda event: self.copy_selected_log())
            
            # Создаем фреймы для разных частей интерфейса в левой части
            top_frame = ttk.Frame(left_frame)
            top_frame.pack(fill=tk.X, padx=5, pady=5)
            
            middle_frame = ttk.Frame(left_frame)
            middle_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Добавляем фрейм для выбора режима логирования
            log_mode_frame = ttk.Frame(left_frame)
            log_mode_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Создаем метку для выбора режима логирования
            log_mode_label = ttk.Label(log_mode_frame, text="Log Mode:")
            log_mode_label.pack(side=tk.LEFT, padx=5)
            
            # Создаем переключатели для выбора режима
            combined_radio = ttk.Radiobutton(log_mode_frame, text="Combined File", variable=self.log_mode, value="combined")
            combined_radio.pack(side=tk.LEFT, padx=5)
            
            separate_radio = ttk.Radiobutton(log_mode_frame, text="Separate Files", variable=self.log_mode, value="separate")
            separate_radio.pack(side=tk.LEFT, padx=5)
            
            ip_frame = ttk.Frame(left_frame)
            ip_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            button_frame = ttk.Frame(left_frame)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            input_frame = ttk.Frame(top_frame)
            input_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(input_frame, text="IP Address:").pack(side=tk.LEFT, padx=5)
            self.ip_entry = ttk.Entry(input_frame, width=20)
            self.ip_entry.pack(side=tk.LEFT, padx=5)
            
            # Добавляем поддержку вставки из буфера обмена
            self.setup_clipboard_support(self.ip_entry)
            
            # Кнопка добавления IP
            ttk.Button(input_frame, text="Add IP", command=self.add_ip).pack(side=tk.LEFT, padx=5)
            
            # Кнопка импорта из CSV
            csv_frame = ttk.Frame(top_frame)
            csv_frame.pack(fill=tk.X, pady=5)
            
            ttk.Button(csv_frame, text="Import from CSV", command=self.add_from_csv).pack(side=tk.LEFT, padx=5)
            
            # Кнопка с вопросом для шаблона CSV
            ttk.Button(csv_frame, text="?", command=self.show_csv_template, width=2).pack(side=tk.LEFT, padx=5)
            
            # Список IP-адресов
            list_frame = ttk.Frame(middle_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            ttk.Label(list_frame, text="IP Addresses:").pack(anchor=tk.W)
            
            # Создаем фрейм со скроллбаром для списка IP
            listbox_frame = ttk.Frame(list_frame)
            listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            self.ip_listbox = tk.Listbox(listbox_frame, height=10, bg='white', borderwidth=1, relief="solid")
            self.ip_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Добавляем скроллбар к списку, который появляется только при необходимости
            scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.ip_listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Настраиваем автоматическое появление скроллбара
            def update_scrollbar(*args):
                if self.ip_listbox.yview() == (0.0, 1.0):
                    # Если все элементы видны, скрываем скроллбар
                    scrollbar.pack_forget()
                else:
                    # Иначе показываем скроллбар
                    if not scrollbar.winfo_manager():
                        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Привязываем функцию обновления к изменению списка
            self.ip_listbox.config(yscrollcommand=lambda first, last: [scrollbar.set(first, last), update_scrollbar()])
            
            # Кнопка удаления IP
            ttk.Button(list_frame, text="Remove Selected IP", command=self.remove_selected_ip).pack(pady=5)
            
            # Интервал пинга
            interval_frame = ttk.Frame(button_frame)
            interval_frame.pack(fill=tk.X, pady=5)
            
            self.interval_var = tk.StringVar(value="2")
            ttk.Label(interval_frame, text="Ping Interval (seconds):").pack(side=tk.LEFT, padx=5)
            self.interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=5)
            self.interval_entry.pack(side=tk.LEFT, padx=5)
            
            # Кнопки управления - делаем их минималистичными
            control_frame = ttk.Frame(button_frame)
            control_frame.pack(fill=tk.X, pady=5)
            
            # Кнопка запуска мониторинга
            self.start_button = ttk.Button(
                control_frame, 
                text="Start", 
                command=self.start_monitoring,
                style='Start.TButton',
                width=10
            )
            self.start_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
            
            # Кнопка остановки мониторинга
            self.stop_button = ttk.Button(
                control_frame, 
                text="Stop", 
                command=self.stop_monitoring,
                style='Stop.TButton',
                width=10
            )
            self.stop_button.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)
            
            # Добавляем небольшой отступ внизу
            ttk.Frame(button_frame, height=10).pack(fill=tk.X, pady=5)
            
            print("Widgets created successfully")
        except Exception as e:
            print(f"Error creating widgets: {str(e)}")
        
    def is_valid_ip(self, ip):
        """Проверяет, является ли строка корректным IP-адресом"""
        try:
            # Проверяем формат IP-адреса (4 числа от 0 до 255, разделенные точками)
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not part.isdigit():
                    return False
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except Exception:
            return False
            
    def add_ip(self):
        ip = self.ip_entry.get().strip()
        if ip and self.is_valid_ip(ip):
            if ip not in self.ip_addresses:
                self.ip_addresses.append(ip)
                self.ip_listbox.insert(tk.END, ip)
                self.ip_entry.delete(0, tk.END)
                
                # Проверяем необходимость отображения скроллбара
                self.ip_listbox.yview_moveto(1.0)  # Прокручиваем вниз, чтобы вызвать обновление скроллбара
            else:
                messagebox.showinfo("Duplicate IP", f"IP address {ip} is already in the list")
        else:
            messagebox.showwarning("Invalid IP", f"Please enter a valid IP address (e.g. 192.168.1.1)")

    def add_from_csv(self):
        """Добавляет IP-адреса из CSV файла"""
        try:
            file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
            if not file_path:
                return
                
            added_count = 0
            with open(file_path, 'r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if row:  # Проверяем, что строка не пустая
                        ip = row[0].strip()
                        if self.is_valid_ip(ip) and ip not in self.ip_addresses:
                            self.ip_addresses.append(ip)
                            self.ip_listbox.insert(tk.END, ip)
                            added_count += 1
            
            # Проверяем необходимость отображения скроллбара
            if added_count > 0:
                self.ip_listbox.yview_moveto(1.0)  # Прокручиваем вниз, чтобы вызвать обновление скроллбара
                messagebox.showinfo("Success", f"Added {added_count} IP addresses from CSV")
            else:
                messagebox.showinfo("No IPs Added", "No valid IP addresses found in the CSV file or all IPs are already in the list")
        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file: {str(e)}")

    def show_csv_template(self):
        """Показывает шаблон CSV файла"""
        template = """
CSV File Format Example:
{{ ... }}

Each line should contain one IP address (one per line):
172.17.15.15
192.168.1.1
8.8.8.8

In Excel:
- Put each IP address in column A (one IP per cell)
- Save as CSV file (comma-separated values)
- No headers or other data needed

Note: Only valid IP addresses will be added
"""
        messagebox.showinfo("CSV Template", template)

    def remove_selected_ip(self):
        """Удаляет выбранный IP-адрес"""
        try:
            selected_index = self.ip_listbox.curselection()
            if selected_index:
                ip = self.ip_listbox.get(selected_index)
                self.ip_addresses.remove(ip)
                self.ip_listbox.delete(selected_index)
                
                # Проверяем необходимость отображения скроллбара
                self.ip_listbox.yview_moveto(0.0)  # Прокручиваем вверх, чтобы вызвать обновление скроллбара
        except Exception as e:
            print(f"Error removing IP: {str(e)}")
        
    def start_monitoring(self):
        """Запускает мониторинг пинга"""
        if not self.ip_addresses:
            messagebox.showwarning("Warning", "Please add at least one IP address")
            return
        
        try:
            # Получаем интервал пинга
            self.ping_interval = float(self.interval_var.get())
            if self.ping_interval <= 0:
                messagebox.showwarning("Warning", "Ping interval must be greater than 0")
                return
        except ValueError:
            messagebox.showwarning("Warning", "Please enter a valid number for ping interval")
            return
        
        if not self.running:
            self.running = True
            
            # Изменяем состояние кнопок
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Запускаем поток мониторинга
            self.ping_thread = threading.Thread(target=self.ping_loop)
            self.ping_thread.daemon = True
            self.ping_thread.start()
            
            # Загружаем существующий лог-файл, если он есть
            self.load_existing_log()
            
            # Добавляем запись о запуске мониторинга
            start_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Monitoring started\n"
            self.update_log_display(start_message)
            
    def load_existing_log(self):
        """Загружает существующий лог-файл в область отображения"""
        try:
            log_dir = "logs"
            
            # Выбираем файлы для загрузки в зависимости от режима
            if self.log_mode.get() == "combined" or not self.ip_addresses:
                # Загружаем общий файл
                log_file = os.path.join(log_dir, "ping_log.txt")
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        # Читаем последние 100 строк файла
                        lines = f.readlines()
                        last_lines = lines[-100:] if len(lines) > 100 else lines
                        
                        # Добавляем строки в область отображения
                        for line in last_lines:
                            self.update_log_display(line)
            else:
                # Загружаем отдельные файлы для каждого IP
                for ip in self.ip_addresses:
                    safe_ip = ip.replace('.', '_')
                    log_file = os.path.join(log_dir, f"ping_log_{safe_ip}.txt")
                    if os.path.exists(log_file):
                        with open(log_file, "r", encoding="utf-8") as f:
                            # Читаем последние 50 строк файла для каждого IP
                            lines = f.readlines()
                            last_lines = lines[-50:] if len(lines) > 50 else lines
                            
                            # Добавляем строки в область отображения
                            for line in last_lines:
                                self.update_log_display(line)
        except Exception as e:
            print(f"Error loading existing log: {str(e)}")
    
    def stop_monitoring(self):
        """Останавливает мониторинг пинга"""
        if self.running:
            self.running = False
            
            # Изменяем состояние кнопок
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)  # Серый цвет для Stop
        
        # Добавляем запись о остановке мониторинга
        stop_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Monitoring stopped\n"
        self.update_log_display(stop_message)
        
    def log_ping_result(self, ip, result):
        """Записывает результат пинга в лог-файл и отображает в интерфейсе"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_dir = "logs"
            
            # Формируем строку лога
            log_entry = f"{timestamp} - {ip}: {result}\n"
            
            # Создаем директорию для логов, если она не существует
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Выбираем режим логирования
            if self.log_mode.get() == "combined":
                # Режим общего файла
                log_file = os.path.join(log_dir, "ping_log.txt")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry)
            else:
                # Режим отдельных файлов для каждого IP
                # Заменяем точки в IP на подчеркивания для имени файла
                safe_ip = ip.replace('.', '_')
                log_file = os.path.join(log_dir, f"ping_log_{safe_ip}.txt")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry)
            
            # Отображаем результат в интерфейсе
            self.update_log_display(log_entry)
        except Exception as e:
            print(f"Error writing to log file: {str(e)}")
        
    def ping_ip(self, ip):
        """Выполняет пинг и возвращает результат"""
        try:
            result = subprocess.run(
                ['ping', '-n', '1', ip],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='cp866'
            )
            
            if result.returncode == 0:
                return self.extract_response_time(result.stdout)
            else:
                return "No response (Host unreachable)"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def ping_loop(self):
        """Цикл пинга всех IP-адресов"""
        while self.running:
            for ip in self.ip_addresses:
                if not self.running:
                    break
                    
                # Выполняем пинг и получаем результат
                result = self.ping_ip(ip)
                
                # Записываем результат в лог
                self.log_ping_result(ip, result)
            
            time.sleep(self.ping_interval)
            
    def update_log_display(self, log_entry):
        """Обновляет отображение логов в интерфейсе"""
        try:
            # Добавляем новую запись в конец
            self.log_text.insert(tk.END, log_entry)
            
            # Прокручиваем до конца
            self.log_text.see(tk.END)
        except Exception as e:
            print(f"Error updating log display: {str(e)}")
    
    def clear_log_display(self):
        """Очищает область отображения логов"""
        try:
            # Очищаем все содержимое
            self.log_text.delete(1.0, tk.END)
        except Exception as e:
            print(f"Error clearing log display: {str(e)}")
            
    def show_log_context_menu(self, event):
        """Показывает контекстное меню для области логов"""
        try:
            self.log_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.log_context_menu.grab_release()
            
    def copy_selected_log(self):
        """Копирует выделенный текст из области логов"""
        try:
            selected_text = self.log_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            # Нет выделенного текста
            pass
    
    def on_closing(self):
        """Обрабатывает закрытие окна"""
        self.running = False
        self.root.destroy()
        
    def setup_global_bindings(self):
        """Настраивает глобальные привязки клавиш для всего окна"""
        try:
            # Привязываем Ctrl+V для всего окна
            self.root.bind_all("<Control-v>", lambda event: self.handle_global_paste(event))
            self.root.bind_all("<Control-V>", lambda event: self.handle_global_paste(event))
            
            # Добавляем привязки для других раскладок
            if platform.system() == "Windows":
                # Для других раскладок
                self.root.bind_all("<Control-Insert>", lambda event: self.handle_global_paste(event))
                self.root.bind_all("<Shift-Insert>", lambda event: self.handle_global_paste(event))
                
                # Добавляем обработчик всех клавиш для перехвата Ctrl+М на русской раскладке
                self.root.bind_all("<KeyPress>", self.check_ctrl_key_combination)
        except Exception as e:
            print(f"Error setting up global bindings: {str(e)}")
    
    def check_ctrl_key_combination(self, event):
        """Проверяет нажатие Ctrl+клавиша для разных раскладок"""
        try:
            # Проверяем нажатие Ctrl
            if event.state & 0x4:  # 0x4 - маска для Ctrl
                # Проверяем код клавиши
                key_char = event.char.lower() if event.char else ''
                key_sym = event.keysym.lower() if event.keysym else ''
                
                # Дебаг информация
                print(f"DEBUG: Key pressed - char: '{key_char}', keysym: '{key_sym}', keycode: {event.keycode}")
                
                # Проверяем на русскую 'м' или украинскую 'в'
                if key_char in ['\u043c', '\u0432'] or key_sym in ['cyrillic_em', 'cyrillic_ve']:
                    return self.handle_global_paste(event)
                
                # Проверяем по коду клавиши (86 - код для 'v' или 'м' на русской раскладке)
                if event.keycode == 86:
                    return self.handle_global_paste(event)
        except Exception as e:
            print(f"Error in check_ctrl_key_combination: {str(e)}")
        return None
    
    def handle_global_paste(self, event):
        """Обрабатывает глобальную вставку из буфера обмена"""
        try:
            # Проверяем, что фокус находится в поле ввода IP
            focused_widget = self.root.focus_get()
            if hasattr(self, 'ip_entry') and focused_widget == self.ip_entry:
                return self.paste_from_clipboard(event)
        except Exception as e:
            print(f"Error in handle_global_paste: {str(e)}")
        return None  # Продолжаем стандартную обработку для других виджетов
    
    def setup_clipboard_support(self, entry):
        """Настраивает поддержку буфера обмена для поля ввода"""
        # Привязываем контекстное меню к правой кнопке мыши
        entry.bind("<Button-3>", self.show_context_menu)
        
        # Добавляем привязку к стандартному событию вставки
        entry.bind("<<Paste>>", lambda event: self.paste_from_clipboard(event))
        
    def show_context_menu(self, event):
        """Показывает контекстное меню при правом клике"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def paste_from_clipboard(self, event=None):
        """Вставляет текст из буфера обмена"""
        try:
            # Проверяем, что ip_entry уже создан
            if not hasattr(self, 'ip_entry') or not self.ip_entry:
                return "break"
                
            clipboard_text = self.root.clipboard_get()
            if clipboard_text:
                # Если есть выделенный текст, заменяем его
                try:
                    self.ip_entry.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass  # Нет выделенного текста
                
                # Вставляем текст из буфера обмена
                self.ip_entry.insert(tk.INSERT, clipboard_text)
                return "break"  # Предотвращаем стандартную обработку
        except Exception as e:
            print(f"Error pasting from clipboard: {str(e)}")
        return "break"

if __name__ == "__main__":
    root = tk.Tk()
    app = PingMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
