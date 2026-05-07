# search tab 
# gui/tabs/search_tab.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from pathlib import Path

from gui.widgets.article_entry import ArticleEntry
from core.nomenclature import NomenclatureDB
from core.address_manager import AddressDB
from commands import CommandHandler

logger = logging.getLogger(__name__)

class SearchTab(ttk.Frame):
    """Вкладка поиска товара"""
    
    def __init__(self, parent, nomenclature: NomenclatureDB, addresses: AddressDB, settings):
        super().__init__(parent)
        self.nomenclature = nomenclature
        self.addresses = addresses
        self.settings = settings
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создает виджеты вкладки"""
        # Основной контейнер с отступами
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="Поиск товара по артикулу или штрих-коду",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Поле ввода
        input_frame = ttk.LabelFrame(main_frame, text="Ввод", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.article_entry = ArticleEntry(
            input_frame,
            on_submit_callback=self._on_search
        )
        self.article_entry.pack(fill=tk.X)
        
        # Кнопка поиска (на случай ручного ввода)
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Найти",
            command=self._on_search_button,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Очистить",
            command=self._clear_result,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Область результатов
        result_frame = ttk.LabelFrame(main_frame, text="Результат поиска", padding="15")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # Текстовое поле для отображения результатов
        self.result_text = tk.Text(
            result_frame,
            height=15,
            width=80,
            font=('Consolas', 11),
            wrap=tk.WORD,
            bg='#f8f9fa',
            fg='#212529'
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # Настройка тегов для форматирования
        self.result_text.tag_config('header', font=('Arial', 12, 'bold'), foreground='#2c3e50')
        self.result_text.tag_config('label', font=('Arial', 10, 'bold'), foreground='#34495e')
        self.result_text.tag_config('value', font=('Consolas', 11), foreground='#16a085')
        self.result_text.tag_config('error', font=('Arial', 10, 'bold'), foreground='#e74c3c')
        self.result_text.tag_config('info', font=('Arial', 9), foreground='#7f8c8d')
        
        # Блок импорта адресов
        import_frame = ttk.LabelFrame(main_frame, text="Импорт адресов", padding="10")
        import_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Label(
            import_frame,
            text="Импорт адресов из Excel-файла:",
            font=('Arial', 9)
        ).pack(anchor=tk.W)
        
        import_buttons = ttk.Frame(import_frame)
        import_buttons.pack(pady=(10, 0))
        
        ttk.Button(
            import_buttons,
            text="Импорт с автоопределением",
            command=self._import_addresses_auto,
            width=25
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            import_buttons,
            text="Импорт с выбором колонок",
            command=self._import_addresses_manual,
            width=25
        ).pack(side=tk.LEFT, padx=5)
        
        # Статусная строка
        self.status_label = ttk.Label(
            main_frame,
            text="Готов к поиску. Введите артикул или отсканируйте штрих-код.",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=(10, 0))
    
    def _on_search(self, code: str, is_command: bool = False):
        """Обработка поиска"""
        self._perform_search(code)
    
    def _on_search_button(self):
        """Обработка нажатия кнопки поиска"""
        code = self.article_entry.entry.get().strip()
        if code:
            self._perform_search(code)
        else:
            messagebox.showwarning("Внимание", "Введите артикул или штрих-код")
        
    def _display_command_result(self, code: str):
        """Отображает результат для служебной команды"""
        from commands import COMMANDS
        
        self.result_text.delete(1.0, tk.END)
        
        cmd_id = None
        for cid, cmd in COMMANDS.items():
            if cmd['code'] == code or cid == code:
                cmd_id = cid
                break
        
        self.result_text.insert(tk.END, "=" * 50 + "\n", 'header')
        self.result_text.insert(tk.END, "СЛУЖЕБНАЯ КОМАНДА\n", 'header')
        self.result_text.insert(tk.END, "=" * 50 + "\n\n", 'header')
        
        self.result_text.insert(tk.END, "Введенный код: ", 'label')
        self.result_text.insert(tk.END, f"{code}\n\n", 'value')
        
        if cmd_id:
            cmd_name = COMMANDS[cmd_id]['name']
            self.result_text.insert(tk.END, "Команда: ", 'label')
            self.result_text.insert(tk.END, f"{cmd_name}\n\n", 'value')
            
            desc = self._get_command_description(cmd_id)
            self.result_text.insert(tk.END, "Описание:\n", 'label')
            self.result_text.insert(tk.END, f"{desc}\n", 'info')
        else:
            self.result_text.insert(tk.END, "⚠ Неизвестная команда\n", 'error')

    def _get_command_description(self, cmd_id: str) -> str:
        desc = {
            'CMD_START_INV': "Начинает новую инвентаризацию",
            'CMD_FINISH_INV': "Завершает текущую инвентаризацию",
            'CMD_RESET_ACTUAL': "Обнуляет ВСЕ фактические остатки во вкладках Подсчёт и Инвентаризация",
            'CMD_ADD1': "Добавляет +1 к последнему отсканированному товару",
            'CMD_ADD10': "Добавляет +10 к последнему отсканированному товару",
            'CMD_ADD100': "Добавляет +100 к последнему отсканированному товару",
            'CMD_SUB1': "Вычитает 1 из последнего отсканированного товара",
            'CMD_SUB10': "Вычитает 10 из последнего отсканированного товара",
            'CMD_SUB100': "Вычитает 100 из последнего отсканированного товара",
            'CMD_MANUAL_NEXT': "Переход к следующей позиции",
            'CMD_MANUAL_LAST': "Возврат к предыдущей позиции",
            'CMD_ZERO_LAST': "Обнуляет последнюю отсканированную позицию",
            'CMD_SHOW_LAST': "Показывает информацию о последней позиции",
            'CMD_SHOW_EXPECTED': "Показывает ожидаемые остатки",
            'CMD_SHOW_STATS': "Показывает статистику инвентаризации",
        }
        return desc.get(cmd_id, "Служебная команда для управления инвентаризацией")

    def _perform_search(self, code: str):
        from commands import CommandHandler
        
        if CommandHandler.is_command(code):
            self._display_command_result(code)
            return
        
        # Поиск товара
        product = self.nomenclature.find_by_article_or_barcode(code)
        
        if product:
            address = self.addresses.get_address(product.article)
            self._display_result(product, address)
            self.status_label.config(
                text=f"✓ Найден товар: {product.name[:50]}",
                foreground="green"
            )
            self.after(2000, lambda: self.status_label.config(foreground="black"))
        else:
            self._display_not_found(code)
            self.status_label.config(
                text=f"✗ Товар с кодом '{code}' не найден в базе",
                foreground="red"
            )
            self.after(2000, lambda: self.status_label.config(foreground="black"))
    
    def _display_result(self, product, address):
        """Отображает результат поиска"""
        self.result_text.delete(1.0, tk.END)
        
        self.result_text.insert(tk.END, "=" * 50 + "\n", 'header')
        self.result_text.insert(tk.END, "РЕЗУЛЬТАТ ПОИСКА\n", 'header')
        self.result_text.insert(tk.END, "=" * 50 + "\n\n", 'header')
        
        # Артикул
        self.result_text.insert(tk.END, "Артикул: ", 'label')
        self.result_text.insert(tk.END, f"{product.article}\n", 'value')
        
        # Наименование
        self.result_text.insert(tk.END, "Наименование: ", 'label')
        self.result_text.insert(tk.END, f"{product.name}\n", 'value')
        
        # Штрих-коды (если есть)
        if product.barcodes:
            self.result_text.insert(tk.END, "Штрих-коды: ", 'label')
            barcodes_str = ", ".join(product.barcodes[:5])
            if len(product.barcodes) > 5:
                barcodes_str += f" (+{len(product.barcodes) - 5} шт.)"
            self.result_text.insert(tk.END, f"{barcodes_str}\n", 'value')
        
        # Адрес
        self.result_text.insert(tk.END, "Адрес хранения: ", 'label')
        if address:
            self.result_text.insert(tk.END, f"{address}\n", 'value')
        else:
            self.result_text.insert(tk.END, "Не указан\n", 'info')
        
        self.result_text.insert(tk.END, "\n" + "-" * 50 + "\n", 'info')
        self.result_text.insert(tk.END, "✓ Товар найден в базе", 'info')
    
    def _display_not_found(self, code: str):
        """Отображает сообщение о ненайденном товаре"""
        self.result_text.delete(1.0, tk.END)
        
        self.result_text.insert(tk.END, "=" * 50 + "\n", 'error')
        self.result_text.insert(tk.END, "ТОВАР НЕ НАЙДЕН\n", 'error')
        self.result_text.insert(tk.END, "=" * 50 + "\n\n", 'error')
        
        self.result_text.insert(tk.END, "Введенный код: ", 'label')
        self.result_text.insert(tk.END, f"{code}\n\n", 'value')
        
        self.result_text.insert(tk.END, "Возможные причины:\n", 'info')
        self.result_text.insert(tk.END, "• Товар отсутствует в базе номенклатуры\n", 'info')
        self.result_text.insert(tk.END, "• Штрих-код не привязан к товару\n", 'info')
        self.result_text.insert(tk.END, "• Ошибка при сканировании\n\n", 'info')
        
        self.result_text.insert(tk.END, "Рекомендации:\n", 'info')
        self.result_text.insert(tk.END, "1. Проверьте корректность ввода\n", 'info')
        self.result_text.insert(tk.END, "2. Обновите базу номенклатуры\n", 'info')
        self.result_text.insert(tk.END, "3. Добавьте товар в базу вручную\n", 'info')
    
    def _clear_result(self):
        """Очищает результат поиска"""
        self.result_text.delete(1.0, tk.END)
        self.article_entry.clear()
        self.article_entry.focus()
        self.status_label.config(text="Готов к поиску")
    
    def _import_addresses_auto(self):
        """Импорт адресов с автоопределением"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл с адресами",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            import pandas as pd
            df = pd.read_excel(file_path, header=None)
            
            # Автоопределение колонок
            article_col = None
            address_col = None
            
            for col in range(min(20, len(df.columns))):
                sample = df.iloc[:min(50, len(df)), col].dropna()
                if len(sample) == 0:
                    continue
                
                # Проверяем на артикулы (цифры, точки, тире)
                sample_str = sample.astype(str)
                if sample_str.str.match(r'^[\d\.\-]+$').sum() > len(sample) * 0.7:
                    if article_col is None:
                        article_col = col
                
                # Проверяем на адреса (буквы + цифры, или просто буквы)
                elif sample_str.str.match(r'^[A-ZА-Я][\d]*$').sum() > len(sample) * 0.5:
                    if address_col is None:
                        address_col = col
            
            if article_col is None or address_col is None:
                # Если не удалось определить, предлагаем ручной выбор
                if messagebox.askyesno(
                    "Не удалось определить колонки",
                    "Не удалось автоматически определить колонки с артикулами и адресами.\n"
                    "Хотите выбрать их вручную?"
                ):
                    self._import_addresses_manual(file_path)
                return
            
            # Импортируем
            success, msg, count = self.addresses.import_from_excel(
                file_path, article_col, address_col
            )
            
            if success:
                messagebox.showinfo("Успех", f"Импортировано {count} адресов")
                self.status_label.config(text=f"Импортировано {count} адресов")
            else:
                messagebox.showerror("Ошибка", msg)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл: {e}")
    
    def _import_addresses_manual(self, file_path=None):
        """Импорт адресов с ручным выбором колонок"""
        if file_path is None:
            file_path = filedialog.askopenfilename(
                title="Выберите файл с адресами",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
            )
        
        if not file_path:
            return
        
        # Создаем диалог выбора колонок
        self._show_column_selection_dialog(file_path)
    
    def _show_column_selection_dialog(self, file_path):
        """Показывает диалог выбора колонок"""
        try:
            import pandas as pd
            df = pd.read_excel(file_path, header=None, nrows=10)
            
            dialog = tk.Toplevel(self)
            dialog.title("Выбор колонок")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Выберите колонку с артикулами:", font=('Arial', 10, 'bold')).pack(pady=(10, 5))
            
            article_var = tk.StringVar()
            article_combo = ttk.Combobox(dialog, textvariable=article_var, state='readonly')
            article_combo['values'] = [f"Колонка {i+1}: {str(df.iloc[0, i])[:30]}" for i in range(min(20, len(df.columns)))]
            article_combo.pack(pady=5, padx=20, fill=tk.X)
            
            ttk.Label(dialog, text="Выберите колонку с адресами:", font=('Arial', 10, 'bold')).pack(pady=(10, 5))
            
            address_var = tk.StringVar()
            address_combo = ttk.Combobox(dialog, textvariable=address_var, state='readonly')
            address_combo['values'] = [f"Колонка {i+1}: {str(df.iloc[0, i])[:30]}" for i in range(min(20, len(df.columns)))]
            address_combo.pack(pady=5, padx=20, fill=tk.X)
            
            # Предпросмотр
            ttk.Label(dialog, text="Предпросмотр первых строк:", font=('Arial', 10, 'bold')).pack(pady=(10, 5))
            
            preview_text = tk.Text(dialog, height=8, width=60, font=('Consolas', 9))
            preview_text.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
            
            def update_preview(*args):
                preview_text.delete(1.0, tk.END)
                try:
                    art_idx = int(article_var.get().split(':')[0].replace('Колонка', '').strip()) - 1
                    addr_idx = int(address_var.get().split(':')[0].replace('Колонка', '').strip()) - 1
                    
                    for i in range(min(10, len(df))):
                        art = df.iloc[i, art_idx] if art_idx < len(df.columns) else ""
                        addr = df.iloc[i, addr_idx] if addr_idx < len(df.columns) else ""
                        preview_text.insert(tk.END, f"{art} -> {addr}\n")
                except:
                    pass
            
            article_var.trace('w', update_preview)
            address_var.trace('w', update_preview)
            
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=20)
            
            def do_import():
                try:
                    art_idx = int(article_var.get().split(':')[0].replace('Колонка', '').strip()) - 1
                    addr_idx = int(address_var.get().split(':')[0].replace('Колонка', '').strip()) - 1
                    
                    success, msg, count = self.addresses.import_from_excel(file_path, art_idx, addr_idx)
                    
                    if success:
                        messagebox.showinfo("Успех", f"Импортировано {count} адресов")
                        dialog.destroy()
                        self.status_label.config(text=f"Импортировано {count} адресов")
                    else:
                        messagebox.showerror("Ошибка", msg)
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))
            
            ttk.Button(button_frame, text="Импортировать", command=do_import, width=15).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Отмена", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")