import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from collections import Counter
import csv
from settings.dictionary import _
import random


class LootTableApp:
    def __init__(self, root, loot_manager):
        self.root = root
        self.root.title("D&D Loot Table Manager")
        self.root.geometry("1000x700")
        self.app_language = "English"

        self.manager = loot_manager

        self.setup_ui()
        ttk.Button(self.root, text=_('settings', self.app_language), command=self.open_settings_dialog).pack(side='bottom', pady=5)
        self.load_data()


    def setup_ui(self):
        # Создание вкладок
        tab_control = ttk.Notebook(self.root)




        # Вкладка предметов
        self.items_tab = ttk.Frame(tab_control)
        tab_control.add(self.items_tab, text=_('items', self.app_language))
        self.setup_items_tab()

        # Вкладка таблиц лута
        self.tables_tab = ttk.Frame(tab_control)
        tab_control.add(self.tables_tab, text='Таблицы лута')
        self.setup_tables_tab()

        # Вкладка контейнеров
        self.containers_tab = ttk.Frame(tab_control)
        tab_control.add(self.containers_tab, text='Контейнеры')
        self.setup_containers_tab()

        # Вкладка генерации
        self.generate_tab = ttk.Frame(tab_control)
        tab_control.add(self.generate_tab, text='Генерация')
        self.setup_generate_tab()
        tab_control.forget(self.generate_tab)

        tab_control.pack(expand=1, fill='both')

    def setup_items_tab(self):
        # Панель управления
        btn_frame = ttk.Frame(self.items_tab)
        btn_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(btn_frame, text="Добавить предмет",
                   command=self.add_item_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Импорт из CSV",
                   command=self.import_csv_dialog).pack(side='left', padx=5)

        # Таблица предметов
        columns = ('ID', 'Название', 'Категория', 'Описание')
        self.items_tree = ttk.Treeview(self.items_tab, columns=columns, show='headings', height=20)

        for col in columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(self.items_tab, orient='vertical',
                                  command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)

        self.items_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')

    def setup_tables_tab(self):
        main_frame = ttk.Frame(self.tables_tab)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Левая панель - список таблиц
        left_frame = ttk.LabelFrame(main_frame, text="Таблицы лута")
        left_frame.pack(side='left', fill='both', padx=5, pady=5)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(btn_frame, text="Новая таблица",
                   command=self.create_loot_table_dialog).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Дублировать",
                   command=self.duplicate_table).pack(side='left', padx=2)

        self.tables_listbox = tk.Listbox(left_frame, height=15)
        self.tables_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.tables_listbox.bind('<<ListboxSelect>>', self.on_table_select)

        # Правая панель - содержимое выбранной таблицы
        right_frame = ttk.LabelFrame(main_frame, text="Содержимое таблицы")
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Информация о таблице
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(info_frame, text="Название:").grid(row=0, column=0, sticky='w')
        self.table_name_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.table_name_var,
                  font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky='w', padx=10)

        ttk.Label(info_frame, text="Описание:").grid(row=1, column=0, sticky='w', pady=5)
        self.table_desc_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.table_desc_var,
                  wraplength=300).grid(row=1, column=1, sticky='w', padx=10, pady=5)

        # Кнопки управления содержимым
        btn_frame2 = ttk.Frame(right_frame)
        btn_frame2.pack(fill='x', padx=5, pady=5)

        ttk.Button(btn_frame2, text="Добавить предмет",
                   command=self.add_item_to_table_dialog).pack(side='left', padx=2)
        ttk.Button(btn_frame2, text="Добавить подтаблицу",
                   command=self.add_subtable_to_table_dialog).pack(side='left', padx=2)
        ttk.Button(btn_frame2, text="Удалить запись",
                   command=self.remove_table_entry).pack(side='left', padx=2)

        # Таблица записей с новыми колонками для галочек
        columns = ('ID', 'Тип', 'Название', 'Шанс%', 'Кол-во', 'Уникальный', 'Обязательный')
        self.entries_tree = ttk.Treeview(right_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.entries_tree.heading(col, text=col)
            self.entries_tree.column(col, width=80)

        scrollbar = ttk.Scrollbar(right_frame, orient='vertical',
                                  command=self.entries_tree.yview)
        self.entries_tree.configure(yscrollcommand=scrollbar.set)

        self.entries_tree.pack(fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

        # Двойной клик для галочек
        self.entries_tree.bind("<Double-1>", self.on_entry_double_click)

    def setup_containers_tab(self):
        main_frame = ttk.Frame(self.containers_tab)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Левая панель
        left_frame = ttk.LabelFrame(main_frame, text="Контейнеры")
        left_frame.pack(side='left', fill='both', padx=5, pady=5)

        ttk.Button(left_frame, text="Новый контейнер",
                   command=self.create_container_dialog).pack(pady=5)

        self.containers_tree = ttk.Treeview(left_frame, columns=('ID', 'Название', 'Таблица'),
                                            show='headings', height=15)
        self.containers_tree.heading('ID', text='ID')
        self.containers_tree.heading('Название', text='Название')
        self.containers_tree.heading('Таблица', text='Таблица')
        self.containers_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # Правая панель
        right_frame = ttk.LabelFrame(main_frame, text="Быстрая генерация")
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        ttk.Label(right_frame, text="Количество бросков:").pack(pady=5)
        self.rolls_var = tk.IntVar(value=1)
        ttk.Spinbox(right_frame, from_=1, to=100, textvariable=self.rolls_var,
                    width=10).pack(pady=5)

        # Новые поля для min/max предметов
        minmax_frame = ttk.Frame(right_frame)
        minmax_frame.pack(pady=5)

        ttk.Label(minmax_frame, text="Min Items:").grid(row=0, column=0, padx=5)
        self.min_items_var = tk.IntVar(value=1)
        ttk.Spinbox(minmax_frame, from_=0, to=1000, textvariable=self.min_items_var, width=5).grid(row=0, column=1,
                                                                                                   padx=5)

        ttk.Label(minmax_frame, text="Max Items:").grid(row=0, column=2, padx=5)
        self.max_items_var = tk.IntVar(value=10)
        ttk.Spinbox(minmax_frame, from_=1, to=1000, textvariable=self.max_items_var, width=5).grid(row=0, column=3,
                                                                                                   padx=5)

        # Кнопка генерации
        ttk.Button(right_frame, text="Сгенерировать лут",
                   command=self.quick_generate).pack(pady=20)

        # Результат
        ttk.Label(right_frame, text="Результат:").pack(pady=5)
        self.quick_result_text = tk.Text(right_frame, height=15, width=40)
        self.quick_result_text.pack(pady=5)

        ttk.Button(right_frame, text="Очистить",
                   command=lambda: self.quick_result_text.delete(1.0, tk.END)).pack(pady=5)

    def setup_generate_tab(self):
        main_frame = ttk.Frame(self.generate_tab)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Выбор источника
        source_frame = ttk.LabelFrame(main_frame, text="Источник")
        source_frame.pack(fill='x', padx=10, pady=10)

        self.source_type = tk.StringVar(value="container")
        ttk.Radiobutton(source_frame, text="Контейнер", variable=self.source_type,
                        value="container", command=self.update_source_list).pack(side='left', padx=10)
        ttk.Radiobutton(source_frame, text="Таблица лута", variable=self.source_type,
                        value="table", command=self.update_source_list).pack(side='left', padx=10)

        ttk.Label(source_frame, text="Выберите:").pack(side='left', padx=10)
        self.source_combo = ttk.Combobox(source_frame, state='readonly', width=30)
        self.source_combo.pack(side='left', padx=10)

        # Настройки
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки")
        settings_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(settings_frame, text="Количество бросков:").grid(row=0, column=0, padx=5, pady=5)
        self.generate_rolls_var = tk.IntVar(value=1)
        ttk.Spinbox(settings_frame, from_=1, to=1000, textvariable=self.generate_rolls_var,
                    width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(settings_frame, text="Деньги (опционально):").grid(row=1, column=0, padx=5, pady=5)
        self.money_frame = ttk.Frame(settings_frame)
        self.money_frame.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        self.money_type_var = tk.StringVar(value="золотых")
        ttk.Entry(self.money_frame, textvariable=self.money_type_var, width=10).pack(side='left', padx=2)
        ttk.Label(self.money_frame, text="от").pack(side='left', padx=2)
        self.money_min_var = tk.IntVar(value=0)
        ttk.Spinbox(self.money_frame, from_=0, to=1000000, textvariable=self.money_min_var,
                    width=8).pack(side='left', padx=2)
        ttk.Label(self.money_frame, text="до").pack(side='left', padx=2)
        self.money_max_var = tk.IntVar(value=0)
        ttk.Spinbox(self.money_frame, from_=0, to=1000000, textvariable=self.money_max_var,
                    width=8).pack(side='left', padx=2)

        # Кнопка генерации
        ttk.Button(main_frame, text="ГЕНЕРИРОВАТЬ ЛУТ",
                   command=self.generate_full_loot,
                   style='Accent.TButton').pack(pady=20)

        # Результат
        result_frame = ttk.LabelFrame(main_frame, text="Результат")
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.result_text = tk.Text(result_frame, height=15, width=80)
        self.result_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Стили
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 12, 'bold'))

    def load_data(self):
        # Загрузка предметов
        for row in self.items_tree.get_children():
            self.items_tree.delete(row)

        items = self.manager.get_all_items()
        for item in items:
            self.items_tree.insert('', 'end', values=item)

        # Загрузка таблиц
        self.tables_listbox.delete(0, tk.END)
        tables = self.manager.get_all_tables()
        self.table_data = {}
        for table in tables:
            table_id, name, desc = table
            display_name = f"{name} (ID: {table_id})"
            self.tables_listbox.insert(tk.END, display_name)
            self.table_data[display_name] = table_id

        # Загрузка контейнеров
        for row in self.containers_tree.get_children():
            self.containers_tree.delete(row)

        containers = self.manager.get_all_containers()
        self.container_data = {}
        for container in containers:
            container_id, name, desc, table_name = container
            self.containers_tree.insert('', 'end', values=(container_id, name, table_name or "Нет"))
            self.container_data[name] = container_id

        # Обновление списков в генераторе
        self.update_source_list()

    def update_source_list(self):
        source_type = self.source_type.get()
        self.source_combo.set('')

        if source_type == "container":
            containers = self.manager.get_all_containers()
            container_names = [name for _, name, _, _ in containers]
            self.source_combo['values'] = container_names
        else:  # table
            tables = self.manager.get_all_tables()
            table_names = [name for _, name, _ in tables]
            self.source_combo['values'] = table_names

    def add_item_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить предмет")
        dialog.geometry("400x300")

        ttk.Label(dialog, text="Название предмета:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)

        ttk.Label(dialog, text="Категория:").pack(pady=5)
        category_entry = ttk.Entry(dialog, width=30)
        category_entry.pack(pady=5)

        ttk.Label(dialog, text="Описание:").pack(pady=5)
        desc_entry = tk.Text(dialog, height=4, width=30)
        desc_entry.pack(pady=5)

        def save_item():
            name = name_entry.get()
            category = category_entry.get()
            description = desc_entry.get(1.0, tk.END).strip()

            if not name:
                messagebox.showerror("Ошибка", "Введите название предмета")
                return

            self.manager.add_item(name, category, description)
            self.load_data()
            dialog.destroy()

        ttk.Button(dialog, text="Сохранить", command=save_item).pack(pady=20)

    def create_loot_table_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Создать таблицу лута")
        dialog.geometry("400x200")

        ttk.Label(dialog, text="Название таблицы:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)

        ttk.Label(dialog, text="Описание:").pack(pady=5)
        desc_entry = tk.Text(dialog, height=3, width=30)
        desc_entry.pack(pady=5)

        def save_table():
            name = name_entry.get()
            description = desc_entry.get(1.0, tk.END).strip()

            if not name:
                messagebox.showerror("Ошибка", "Введите название таблицы")
                return

            self.manager.create_loot_table(name, description)
            self.load_data()
            dialog.destroy()

        ttk.Button(dialog, text="Сохранить", command=save_table).pack(pady=20)

    def on_table_select(self, event):
        selection = self.tables_listbox.curselection()
        if not selection:
            return

        display_name = self.tables_listbox.get(selection[0])
        table_id = self.table_data[display_name]

        # Получаем информацию о таблице
        cursor = self.manager.conn.cursor()
        cursor.execute('SELECT name, description FROM loot_tables WHERE id = ?', (table_id,))
        table_info = cursor.fetchone()

        if table_info:
            self.table_name_var.set(table_info[0])
            self.table_desc_var.set(table_info[1] or "")

        # Загружаем записи таблицы
        for row in self.entries_tree.get_children():
            self.entries_tree.delete(row)

        entries = self.manager.get_table_entries(table_id)
        for entry in entries:
            (
                entry_id,
                item_id,
                subtable_id,
                chance,
                qty_min,
                qty_max,
                entry_name,
                entry_type,
                is_unique,
                is_mandatory
            ) = entry

            if qty_min == qty_max:
                quantity = str(qty_min)
            else:
                quantity = f"{qty_min}-{qty_max}"

            self.entries_tree.insert('', 'end',
                                     values=(
                                         entry_id,
                                         entry_type,
                                         entry_name,
                                         f"{chance:.2f}%",
                                         f"{qty_min}-{qty_max}" if qty_min != qty_max else str(qty_min),
                                         "✔" if is_unique else "",
                                         "✔" if is_mandatory else ""
                                     )
                                     )

    def add_item_to_table_dialog(self):
        selection = self.tables_listbox.curselection()
        if not selection:
            messagebox.showwarning("Выбор", "Сначала выберите таблицу")
            return

        display_name = self.tables_listbox.get(selection[0])
        table_id = self.table_data[display_name]

        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить предмет в таблицу")
        dialog.geometry("900x600")

        ttk.Label(dialog, text="Поиск предмета:").pack(pady=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(dialog, textvariable=search_var, width=50)
        search_entry.pack(pady=5)

        # Список предметов
        columns = ('ID', 'Название', 'Категория')
        items_tree = ttk.Treeview(dialog, columns=columns, show='headings', height=20)
        for col in columns:
            items_tree.heading(col, text=col)
            items_tree.column(col, width=200)

        scrollbar = ttk.Scrollbar(dialog, orient='vertical', command=items_tree.yview)
        items_tree.configure(yscrollcommand=scrollbar.set)

        items_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

        all_items = self.manager.get_all_items()

        def populate_tree(filtered_items=None):
            items_tree.delete(*items_tree.get_children())
            for item in filtered_items or all_items:
                items_tree.insert('', 'end', values=item)

        populate_tree()

        def on_search(*args):
            query = search_var.get().lower()
            filtered = [itm for itm in all_items if query in itm[1].lower() or (itm[2] and query in itm[2].lower())]
            populate_tree(filtered)

        search_var.trace_add('write', on_search)

        # Настройки шанса и количества
        settings_frame = ttk.Frame(dialog)
        settings_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(settings_frame, text="Шанс выпадения (%):").grid(row=0, column=0, pady=5, sticky='w')
        chance_var = tk.DoubleVar(value=10.0)
        ttk.Entry(settings_frame, textvariable=chance_var, width=10).grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(settings_frame, text="Количество:").grid(row=1, column=0, pady=5, sticky='w')
        qty_frame = ttk.Frame(settings_frame)
        qty_frame.grid(row=1, column=1, pady=5, sticky='w')

        is_unique_var = tk.BooleanVar()
        is_mandatory_var = tk.BooleanVar()

        ttk.Checkbutton(settings_frame,
                        text="Уникальный (1 за ролл)",
                        variable=is_unique_var).grid(row=2, column=0, sticky='w')

        ttk.Checkbutton(settings_frame,
                        text="Обязательный",
                        variable=is_mandatory_var).grid(row=2, column=1, sticky='w')

        qty_min_var = tk.IntVar(value=1)
        qty_max_var = tk.IntVar(value=1)
        ttk.Spinbox(qty_frame, from_=1, to=100, textvariable=qty_min_var, width=5).pack(side='left', padx=2)
        ttk.Label(qty_frame, text="до").pack(side='left', padx=2)
        ttk.Spinbox(qty_frame, from_=1, to=100, textvariable=qty_max_var, width=5).pack(side='left', padx=2)

        def add_selected():
            selected = items_tree.selection()
            if not selected:
                messagebox.showwarning("Выбор", "Выберите предмет")
                return
            item_values = items_tree.item(selected[0])['values']
            item_id = item_values[0]
            chance = chance_var.get()
            qty_min = qty_min_var.get()
            qty_max = qty_max_var.get()
            if qty_min > qty_max:
                messagebox.showerror("Ошибка", "Минимальное количество не может быть больше максимального")
                return
            self.manager.add_entry_to_table(
                table_id,
                item_id=item_id,
                chance_percent=chance,
                quantity_min=qty_min,
                quantity_max=qty_max,
                is_unique=is_unique_var.get(),
                is_mandatory=is_mandatory_var.get()
            )
            self.on_table_select(None)
            dialog.destroy()

        ttk.Button(dialog, text="Добавить", command=add_selected).pack(pady=20)

    def add_subtable_to_table_dialog(self):
        selection = self.tables_listbox.curselection()
        if not selection:
            messagebox.showwarning("Выбор", "Сначала выберите таблицу")
            return

        display_name = self.tables_listbox.get(selection[0])
        table_id = self.table_data[display_name]

        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить подтаблицу")
        dialog.geometry("400x300")

        ttk.Label(dialog, text="Выберите таблицу:").pack(pady=5)

        tables_listbox = tk.Listbox(dialog, height=10)
        tables_listbox.pack(fill='both', expand=True, padx=10, pady=5)

        # Загрузка таблиц (исключая текущую)
        tables = self.manager.get_all_tables()
        for table in tables:
            table_id_2, name, desc = table
            if table_id_2 != table_id:
                tables_listbox.insert(tk.END, f"{name} (ID: {table_id_2})")

        # Настройки
        ttk.Label(dialog, text="Шанс выпадения (%):").pack(pady=5)
        chance_var = tk.DoubleVar(value=5.0)
        ttk.Entry(dialog, textvariable=chance_var, width=10).pack(pady=5)

        def add_selected():
            selection = tables_listbox.curselection()
            if not selection:
                messagebox.showwarning("Выбор", "Выберите таблицу")
                return

            selected_text = tables_listbox.get(selection[0])
            # Извлекаем ID из текста
            import re
            match = re.search(r'ID: (\d+)', selected_text)
            if not match:
                messagebox.showerror("Ошибка", "Не удалось определить ID таблицы")
                return

            subtable_id = int(match.group(1))
            chance = chance_var.get()

            self.manager.add_entry_to_table(table_id, subtable_id=subtable_id,
                                            chance_percent=chance)
            self.on_table_select(None)
            dialog.destroy()

        ttk.Button(dialog, text="Добавить", command=add_selected).pack(pady=10)

    def create_container_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Создать контейнер")
        dialog.geometry("500x400")

        ttk.Label(dialog, text="Название контейнера:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)

        ttk.Label(dialog, text="Описание:").pack(pady=5)
        desc_entry = tk.Text(dialog, height=3, width=30)
        desc_entry.pack(pady=5)

        ttk.Label(dialog, text="Таблица лута:").pack(pady=5)

        # Выбор таблицы
        tables_frame = ttk.Frame(dialog)
        tables_frame.pack(fill='both', expand=True, padx=10, pady=5)

        tables_listbox = tk.Listbox(tables_frame, height=8)
        tables_listbox.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(tables_frame, command=tables_listbox.yview)
        tables_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Загрузка таблиц
        tables = self.manager.get_all_tables()
        self.temp_table_data = {}
        for table in tables:
            table_id, name, desc = table
            display_name = f"{name} (ID: {table_id})"
            tables_listbox.insert(tk.END, display_name)
            self.temp_table_data[display_name] = table_id

        def save_container():
            name = name_entry.get()
            description = desc_entry.get(1.0, tk.END).strip()

            if not name:
                messagebox.showerror("Ошибка", "Введите название контейнера")
                return

            # Получаем выбранную таблицу
            selection = tables_listbox.curselection()
            if not selection:
                messagebox.showwarning("Выбор", "Выберите таблицу лута")
                return

            selected_text = tables_listbox.get(selection[0])
            loot_table_id = self.temp_table_data[selected_text]

            self.manager.create_container(name, description, loot_table_id)
            self.load_data()
            dialog.destroy()

        ttk.Button(dialog, text="Сохранить", command=save_container).pack(pady=20)

    def quick_generate(self):
        selection = self.containers_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите контейнер")
            return

        item = self.containers_tree.item(selection[0])
        values = item['values']
        container_id = values[0]

        rolls = self.rolls_var.get()
        min_items = self.min_items_var.get()
        max_items = self.max_items_var.get()

        loot = self.manager.generate_container_loot(
            container_id,
            rolls=rolls,
            min_items=min_items,
            max_items=max_items
        )

        # агрегируем quantity
        from collections import defaultdict
        loot_count = defaultdict(int)

        for item in loot:
            loot_count[item["name"]] += item["quantity"]

        # Вывод
        self.quick_result_text.delete(1.0, tk.END)
        self.quick_result_text.insert(tk.END, f"Лут из '{values[1]}' ({rolls} бросок(ов)):\n")
        self.quick_result_text.insert(tk.END, "=" * 50 + "\n\n")

        total_items = 0
        for item, count in sorted(loot_count.items()):
            self.quick_result_text.insert(tk.END, f"{item}")
            if count > 1:
                self.quick_result_text.insert(tk.END, f" (x{count})")
            self.quick_result_text.insert(tk.END, "\n")

        self.quick_result_text.insert(tk.END, f"\nВсего предметов: {total_items}\n")

    def generate_full_loot(self):
        source_type = self.source_type.get()
        source_name = self.source_combo.get()

        if not source_name:
            messagebox.showwarning("Выбор", "Выберите источник")
            return

        rolls = self.generate_rolls_var.get()

        # Генерация лута
        if source_type == "container":
            container_id = self.container_data[source_name]
            loot = self.manager.generate_container_loot(container_id, rolls)
        else:
            # Ищем ID таблицы по имени
            tables = self.manager.get_all_tables()
            table_id = None
            for table in tables:
                if table[1] == source_name:
                    table_id = table[0]
                    break

            if not table_id:
                messagebox.showerror("Ошибка", f"Таблица '{source_name}' не найдена")
                return

            loot = self.manager.generate_from_table(table_id, rolls)

        # Генерация денег (если указаны)
        money_result = ""
        money_min = self.money_min_var.get()
        money_max = self.money_max_var.get()

        if money_min > 0 and money_max >= money_min:
            money_amount = random.randint(money_min, money_max)
            money_type = self.money_type_var.get()
            money_result = f"\nДеньги: {money_amount} {money_type}\n"

        # Подсчет результатов
        from collections import Counter
        loot_count = Counter(loot)

        # Вывод
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"=== РЕЗУЛЬТАТ ГЕНЕРАЦИИ ===\n")
        self.result_text.insert(tk.END, f"Источник: {source_name}\n")
        self.result_text.insert(tk.END, f"Бросков: {rolls}\n")
        self.result_text.insert(tk.END, "=" * 50 + "\n\n")

        if money_result:
            self.result_text.insert(tk.END, money_result + "\n")

        if loot_count:
            self.result_text.insert(tk.END, "Предметы:\n")
            self.result_text.insert(tk.END, "-" * 30 + "\n")

            total_items = 0
            for item, count in sorted(loot_count.items()):
                self.result_text.insert(tk.END, f"• {item}")
                if count > 1:
                    self.result_text.insert(tk.END, f" ×{count}")
                self.result_text.insert(tk.END, "\n")
                total_items += count

            self.result_text.insert(tk.END, f"\nВсего предметов: {total_items}\n")
        else:
            self.result_text.insert(tk.END, "Ничего не выпало!\n")

    def import_csv_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл",
            filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                container_name = row.get('container_name')
                container_desc = row.get('container_description', "")
                item_name = row.get('item_name')
                item_category = row.get('item_category', None)
                item_desc = row.get('item_description', None)
                custom_data = row.get('item_custom_data', None)
                chance = float(row.get('chance_percent', 1))
                qty_min = int(row.get('quantity_min', 1))
                qty_max = int(row.get('quantity_max', 1))

                # Проверка и создание контейнера
                container_id = None
                for cont in self.manager.get_all_containers():
                    if cont[1] == container_name:
                        container_id = cont[0]
                        break

                if not container_id:
                    # Создаём таблицу лута для контейнера
                    table_id = self.manager.create_loot_table(container_name + " Loot Table", "")
                    container_id = self.manager.create_container(container_name, container_desc, table_id)

                # Создаём предмет (если не существует)
                item_id = None
                for itm in self.manager.get_all_items():
                    if itm[1] == item_name:
                        item_id = itm[0]
                        break
                if not item_id:
                    item_id = self.manager.add_item(item_name, item_category, item_desc, custom_data)

                # Добавляем запись в таблицу лута контейнера
                cursor = self.manager.conn.cursor()
                cursor.execute('SELECT loot_table_id FROM containers WHERE id = ?', (container_id,))
                table_id = cursor.fetchone()[0]
                self.manager.add_entry_to_table(
                    table_id,
                    item_id=item_id,
                    chance_percent=chance,
                    quantity_min=qty_min,
                    quantity_max=qty_max,
                    is_unique=False,
                    is_mandatory=False
                )

        self.load_data()
        messagebox.showinfo("Импорт", "Импорт завершён успешно")

    def duplicate_table(self):
        selection = self.tables_listbox.curselection()
        if not selection:
            messagebox.showwarning("Выбор", "Сначала выберите таблицу")
            return

        display_name = self.tables_listbox.get(selection[0])
        table_id = self.table_data[display_name]

        new_name = simpledialog.askstring("Дублирование",
                                          "Введите название для копии таблицы:")
        if not new_name:
            return

        # Получаем оригинальную таблицу
        cursor = self.manager.conn.cursor()
        cursor.execute('SELECT description FROM loot_tables WHERE id = ?', (table_id,))
        result = cursor.fetchone()
        description = result[0] if result else ""

        # Создаем новую таблицу
        new_table_id = self.manager.create_loot_table(new_name, description)

        # Копируем записи
        entries = self.manager.get_table_entries(table_id)
        for entry in entries:
            entry_id, item_id, subtable_id, chance, qty_min, qty_max, entry_name, entry_type = entry

            self.manager.add_entry_to_table(
                new_table_id,
                item_id=item_id,
                subtable_id=subtable_id,
                chance_percent=chance,
                quantity_min=qty_min,
                quantity_max=qty_max
            )

        messagebox.showinfo("Успех", f"Таблица '{display_name}' скопирована как '{new_name}'")
        self.load_data()

    def remove_table_entry(self):
        selection = self.entries_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите запись для удаления")
            return

        entry_id = self.entries_tree.item(selection[0])['values'][0]

        if messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            cursor = self.manager.conn.cursor()
            cursor.execute('DELETE FROM table_entries WHERE id = ?', (entry_id,))
            self.manager.conn.commit()
            self.on_table_select(None)  # Обновить список

    def open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки")
        dialog.geometry("400x200")

        ttk.Label(dialog, text="Язык интерфейса:").pack(pady=10)
        language_var = tk.StringVar(value=getattr(self, 'app_language', 'English'))

        languages = ['Русский', 'English', 'Deutsch']
        language_combo = ttk.Combobox(dialog, textvariable=language_var, values=languages, state='readonly')
        language_combo.pack(pady=5)

        def save_settings():
            self.app_language = language_var.get()
            messagebox.showinfo("Настройки", f"Язык установлен: {self.app_language}")
            dialog.destroy()

        ttk.Button(dialog, text="Сохранить", command=save_settings).pack(pady=20)

    def on_entry_double_click(self, event):
        item_id = self.entries_tree.identify_row(event.y)
        if not item_id:
            return

        col = self.entries_tree.identify_column(event.x)
        if col not in ('#6', '#7'):  # колонки "Уникальный" и "Обязательный"
            return

        current = self.entries_tree.set(item_id, col)
        new_val = "✔" if current == "" else ""  # переключаем галочку
        self.entries_tree.set(item_id, col, new_val)

        # Сохраняем изменения в базе
        entry_db_id = self.entries_tree.set(item_id, '#1')  # ID записи
        is_unique = self.entries_tree.set(item_id, '#6') == "✔"
        is_mandatory = self.entries_tree.set(item_id, '#7') == "✔"

        cursor = self.manager.conn.cursor()
        cursor.execute(
            'UPDATE table_entries SET is_unique = ?, is_mandatory = ? WHERE id = ?',
            (int(is_unique), int(is_mandatory), entry_db_id)
        )
        self.manager.conn.commit()