import tkinter as tk
import subprocess
import threading
import time
import os
import csv
import queue
import webbrowser
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import platform

class PingMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Pinglo")
        # Geometry is set below via minsize() and geometry()
        
        # Устанавливаем современную тему
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Используем тему clam для более современного вида
        
        # Настраиваем цвета
        bg_color = "#f5f5f5"  # Светло-серый фон
        # accent_color removed (unused)
        
        # Настраиваем стили для элементов ttk
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TLabel', background=bg_color, font=('Segoe UI', 9))
        self.style.configure('TButton', font=('Segoe UI', 9))
        self.style.configure('TRadiobutton', background=bg_color, font=('Segoe UI', 9))
        self.style.configure('TEntry', font=('Segoe UI', 9))
        
        # Using tk.Button for Start/Stop; no extra ttk styles needed
        
        # Устанавливаем фон окна
        self.root.configure(bg=bg_color)
        
        # Устанавливаем минимальный размер окна
        self.root.minsize(1100, 550)
        
        # Устанавливаем начальный размер окна
        self.root.geometry("1100x550")
        
        # Создаем контекстное меню для вставки
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Paste", command=lambda: self.paste_from_clipboard(None))
        
        self.ip_addresses = []
        self.ping_interval = 2
        self.running = False
        self.ping_thread = None
        self.log_mode = tk.StringVar(value="combined")
        self.log_queue = queue.Queue()
        
        try:
            print("Creating widgets...")
            self.create_widgets()
            print("Widgets created successfully")
        except Exception as e:
            print(f"Error creating widgets: {str(e)}")
        
        # Start periodic handler for log queue (thread-safe UI updates)
        self.root.after(100, self.process_log_queue)
        
    def extract_response_time(self, output):
        """Извлекает время отклика из результата ping"""
        try:
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
            return f"Error: {str(e)}"
        
    # Удаляем метод update_online_status, так как он больше не нужен
    
    def process_log_queue(self):
        """Processes log entries from a queue on the UI thread"""
        try:
            # Если окно уничтожено, прекращаем работу
            if not self.root.winfo_exists():
                return
            while True:
                line = self.log_queue.get_nowait()
                # временно разрешаем запись в текст, затем снова запрещаем
                try:
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, line + "\n")
                    self.log_text.see(tk.END)
                finally:
                    self.log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        except tk.TclError:
            # Окно закрыто или виджет уничтожен — прекращаем
            return
        finally:
            try:
                if self.root.winfo_exists():
                    self.root.after(100, self.process_log_queue)
            except tk.TclError:
                # Окно закрывается — не планируем следующий вызов
                pass
        
    def create_widgets(self):
        """Создает все виджеты интерфейса"""
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
            
            # Разрешаем выделение/копирование текста, но запрещаем редактирование пользователем
            self.log_text.config(state=tk.DISABLED)
            
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
            
            # removed unused ip_frame
            
            button_frame = ttk.Frame(left_frame)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            input_frame = ttk.Frame(top_frame)
            input_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(input_frame, text="IP Address:").pack(side=tk.LEFT, padx=5)
            self.ip_entry = ttk.Entry(input_frame, width=20)
            self.ip_entry.pack(side=tk.LEFT, padx=5)
            
            # Добавляем поддержку вставки из буфера обмена
            self.setup_clipboard_support(self.ip_entry)
            # Add Enter shortcut to add IP
            self.ip_entry.bind('<Return>', lambda e: self.add_ip())
            
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
            
            # Кнопки управления - используем grid вместо pack для точного контроля
            control_frame = ttk.Frame(button_frame)
            control_frame.pack(fill=tk.X, pady=5)
            
            # Настраиваем сетку для кнопок
            control_frame.columnconfigure(0, weight=1)
            control_frame.columnconfigure(1, weight=1)
            
            # Кнопка запуска мониторинга - используем обычную кнопку tk.Button вместо ttk
            self.start_button = tk.Button(
                control_frame, 
                text="Start", 
                command=self.start_monitoring,
                bg='#2ecc71',  # Зеленый цвет
                fg='white',    # Белый текст
                width=15,      # Ширина в символах
                height=1,      # Высота в строках
                font=('Segoe UI', 9, 'bold'),  # Жирный шрифт
                relief=tk.RAISED,  # Объемная кнопка
                borderwidth=2   # Толщина границы
            )
            self.start_button.grid(row=0, column=0, padx=10, pady=5, sticky='ew')
            
            # Кнопка остановки мониторинга - также используем tk.Button
            self.stop_button = tk.Button(
                control_frame, 
                text="Stop", 
                command=self.stop_monitoring,
                bg='#e74c3c',  # Красный цвет
                fg='white',    # Белый текст
                width=15,      # Ширина в символах
                height=1,      # Высота в строках
                font=('Segoe UI', 9, 'bold'),  # Жирный шрифт
                relief=tk.RAISED,  # Объемная кнопка
                borderwidth=2   # Толщина границы
            )
            self.stop_button.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
            # Disable Stop on start
            self.stop_button.config(state=tk.DISABLED)
            
            # Добавляем небольшой отступ внизу
            ttk.Frame(button_frame, height=10).pack(fill=tk.X, pady=5)
            
            # Добавляем ссылку на GitHub в нижней части левого фрейма
            github_frame = ttk.Frame(left_frame)
            github_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2, before=top_frame)
            
            # Создаем метку-ссылку на GitHub
            link_label = ttk.Label(
                github_frame, 
                text="GitHub: avelender/Pinglo", 
                font=("Segoe UI", 8),
                foreground="blue",
                cursor="hand2"
            )
            link_label.pack(side=tk.LEFT, padx=5, pady=2)
            
            # Привязываем событие клика
            link_label.bind("<Button-1>", lambda e: self.open_github_link())
            
            # Добавляем подчеркивание при наведении
            link_label.bind("<Enter>", lambda e: link_label.config(font=("Segoe UI", 8, "underline")))
            link_label.bind("<Leave>", lambda e: link_label.config(font=("Segoe UI", 8)))
            
            print("Widgets created successfully")
        except Exception as e:
            print(f"Error creating widgets: {str(e)}")
    
    def open_github_link(self):
        """Открывает репозиторий GitHub в браузере"""
        webbrowser.open("https://github.com/avelender/Pinglo")
    
    def setup_global_bindings(self):
        """Настраивает глобальные привязки клавиш"""
        # Привязываем Ctrl+V к вставке из буфера обмена
        self.root.bind("<Control-v>", self.paste_from_clipboard)
        self.root.bind("<Control-V>", self.paste_from_clipboard)
        
        # Для русской раскладки (Ctrl+М)
        self.root.bind("<Control-KeyPress>", self.handle_control_key)
    
    def handle_control_key(self, event):
        """Обрабатывает нажатие клавиш с Ctrl для поддержки вставки на разных раскладках"""
        if event.keysym == 'v' or event.keysym == 'V' or event.keysym == 'м' or event.keysym == 'М':
            return self.paste_from_clipboard(event)
    
    def setup_clipboard_support(self, entry):
        """Настраивает поддержку буфера обмена для поля ввода"""
        # Привязываем правый клик к показу контекстного меню
        entry.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Показывает контекстное меню при правом клике"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def show_log_context_menu(self, event):
        """Показывает контекстное меню для лога при правом клике"""
        try:
            self.log_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.log_context_menu.grab_release()
    
    def copy_selected_log(self):
        """Копирует выделенный текст из лога в буфер обмена"""
        try:
            selected_text = self.log_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            # Нет выделенного текста
            pass
    
    def add_ip(self):
        """Добавляет IP-адрес в список"""
        ip = self.ip_entry.get().strip()
        if ip and self.is_valid_ip(ip) and ip not in self.ip_addresses:
            self.ip_addresses.append(ip)
            self.ip_listbox.insert(tk.END, ip)
            self.ip_entry.delete(0, tk.END)
        elif not ip:
            messagebox.showwarning("Warning", "Please enter an IP address.")
        elif not self.is_valid_ip(ip):
            messagebox.showwarning("Warning", "Please enter a valid IP address.")
        else:
            messagebox.showwarning("Warning", "This IP address is already in the list.")
    
    def is_valid_ip(self, ip):
        """Проверяет, является ли строка допустимым IP-адресом"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
        return True
    
    def remove_selected_ip(self):
        """Удаляет выбранный IP-адрес из списка"""
        try:
            selected_index = self.ip_listbox.curselection()[0]
            ip = self.ip_listbox.get(selected_index)
            self.ip_addresses.remove(ip)
            self.ip_listbox.delete(selected_index)
        except IndexError:
            messagebox.showwarning("Warning", "Please select an IP address to remove.")
    
    def add_from_csv(self):
        """Добавляет IP-адреса из CSV-файла"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select CSV File",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if not file_path:
                return
            
            with open(file_path, 'r', encoding='utf-8-sig', newline='') as file:
                reader = csv.reader(file)
                added_count = 0
                for row in reader:
                    if row and row[0].strip() and self.is_valid_ip(row[0].strip()) and row[0].strip() not in self.ip_addresses:
                        self.ip_addresses.append(row[0].strip())
                        self.ip_listbox.insert(tk.END, row[0].strip())
                        added_count += 1
            
            if added_count > 0:
                messagebox.showinfo("Success", f"Added {added_count} IP addresses from CSV.")
            else:
                messagebox.showinfo("Info", "No new valid IP addresses found in the CSV file.")
        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file: {str(e)}")
    
    def show_csv_template(self):
        """Показывает шаблон CSV-файла"""
        messagebox.showinfo(
            "CSV Template",
            "CSV file should contain IP addresses in the first column (A), one per row/cell.\n\n"
            "Example (Excel):\n"
            "192.168.1.1\n"
            "192.168.1.2\n"
            "10.0.0.1"
        )
    
    def start_monitoring(self):
        """Запускает мониторинг IP-адресов"""
        if not self.ip_addresses:
            messagebox.showwarning("Warning", "Please add at least one IP address.")
            return
        
        try:
            self.ping_interval = int(self.interval_var.get())
            if self.ping_interval < 1:
                self.ping_interval = 1
                self.interval_var.set("1")
        except ValueError:
            self.ping_interval = 2
            self.interval_var.set("2")
            messagebox.showwarning("Warning", "Invalid interval. Using default (2 seconds).")
        
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Создаем директорию для логов, если её нет
            if not os.path.exists("logs"):
                os.makedirs("logs")
            
            # Запускаем поток мониторинга
            self.ping_thread = threading.Thread(target=self.ping_loop)
            self.ping_thread.daemon = True
            self.ping_thread.start()
    
    def stop_monitoring(self):
        """Останавливает мониторинг IP-адресов"""
        if self.running:
            self.running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    def ping_ip(self, ip):
        """Пингует IP-адрес и возвращает результат"""
        try:
            # Determine ping params with timeouts
            sys_name = platform.system().lower()
            if sys_name == "windows":
                # Windows: hide console window and 1000ms reply timeout
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                cmd = ["ping", "-n", "1", "-w", "1000", ip]
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    encoding='cp866',
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=3
                )
            elif sys_name == "darwin":
                # macOS: 1 packet, 1000 ms timeout
                cmd = ["ping", "-c", "1", "-W", "1000", ip]
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    timeout=3
                )
            else:
                # Linux: 1 packet, 1 second timeout
                cmd = ["ping", "-c", "1", "-W", "1", ip]
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    timeout=3
                )
            return result.returncode, result.stdout
        except subprocess.TimeoutExpired:
            return 1, "Timeout"
        except Exception as e:
            print(f"Error pinging {ip}: {str(e)}")
            return 1, str(e)
    
    def ping_loop(self):
        """Основной цикл мониторинга"""
        while self.running:
            for ip in list(self.ip_addresses):
                if not self.running:
                    break
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return_code, output = self.ping_ip(ip)
                
                if return_code == 0:
                    # Успешный пинг
                    response = self.extract_response_time(output)
                else:
                    # Неудачный пинг
                    response = "No response"
                
                # Формируем строку лога
                log_entry = f"{timestamp} - {ip} - {response}"
                
                # Выводим в консоль
                print(log_entry)
                
                # Thread-safe UI update via queue
                self.log_queue.put(log_entry)
                
                # Записываем в файл
                if self.log_mode.get() == "combined":
                    # Общий лог для всех IP
                    log_file = os.path.join("logs", "combined_ping_log.txt")
                    with open(log_file, "a", encoding='utf-8') as f:
                        f.write(log_entry + "\n")
                else:
                    # Отдельный лог для каждого IP
                    log_file = os.path.join("logs", f"{ip.replace('.', '_')}_ping_log.txt")
                    with open(log_file, "a", encoding='utf-8') as f:
                        f.write(log_entry + "\n")
            
            # Пауза между циклами пинга
            time.sleep(self.ping_interval)
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        if self.running:
            self.running = False
            # Даем потоку время на завершение
            if self.ping_thread and self.ping_thread.is_alive():
                self.ping_thread.join(1.0)
        self.root.destroy()
    
    def paste_from_clipboard(self, event):
        """Вставляет текст из буфера обмена в поле ввода"""
        try:
            # Получаем текст из буфера обмена
            clipboard_text = self.root.clipboard_get()
            
            # Если фокус на поле ввода IP, вставляем туда
            if self.root.focus_get() == self.ip_entry:
                # Проверяем, есть ли выделенный текст
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
