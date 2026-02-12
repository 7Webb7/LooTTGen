import sqlite3
import json
import random
import csv
from pathlib import Path


class LootTableManager:


    def __init__(self, db_path="data/loot_tables.db"):
        self.db_path = Path(db_path)
        # Создаем папку, если не существует
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Подключаемся к SQLite
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()



    def create_tables(self):
        cursor = self.conn.cursor()


        # Таблица предметов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                custom_data TEXT
            )
        ''')

        # Таблица лута (таблицы выпадения)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loot_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                is_container BOOLEAN DEFAULT 0
            )
        ''')

        # Таблица записей в лута-таблицах (с процентами)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER,
                item_id INTEGER,
                subtable_id INTEGER,
                chance_percent REAL NOT NULL,
                quantity_min INTEGER DEFAULT 1,
                quantity_max INTEGER DEFAULT 1,
                is_unique BOOLEAN DEFAULT 0,
                is_mandatory BOOLEAN DEFAULT 0,
                FOREIGN KEY (table_id) REFERENCES loot_tables (id),
                FOREIGN KEY (item_id) REFERENCES items (id),
                FOREIGN KEY (subtable_id) REFERENCES loot_tables (id)
            )
        ''')

        # Таблица контейнеров (специальный тип лута-таблицы)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS containers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                loot_table_id INTEGER,
                FOREIGN KEY (loot_table_id) REFERENCES loot_tables (id)
            )
        ''')

        self.conn.commit()

        self._migrate_table_entries()

    def _migrate_table_entries(self):
        cursor = self.conn.cursor()

        cursor.execute("PRAGMA table_info(table_entries)")
        columns = [col[1] for col in cursor.fetchall()]

        if "is_unique" not in columns:
            cursor.execute("ALTER TABLE table_entries ADD COLUMN is_unique BOOLEAN DEFAULT 0")

        if "is_mandatory" not in columns:
            cursor.execute("ALTER TABLE table_entries ADD COLUMN is_mandatory BOOLEAN DEFAULT 0")

        self.conn.commit()

    def add_item(self, name, category=None, description=None, custom_data=None):
        cursor = self.conn.cursor()
        custom_json = json.dumps(custom_data) if custom_data else None
        cursor.execute('''
            INSERT INTO items (name, category, description, custom_data)
            VALUES (?, ?, ?, ?)
        ''', (name, category, description, custom_json))
        self.conn.commit()
        return cursor.lastrowid

    def create_loot_table(self, name, description="", is_container=False):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO loot_tables (name, description, is_container)
            VALUES (?, ?, ?)
        ''', (name, description, 1 if is_container else 0))
        self.conn.commit()
        return cursor.lastrowid

    def create_container(self, name, description="", loot_table_id=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO containers (name, description, loot_table_id)
            VALUES (?, ?, ?)
        ''', (name, description, loot_table_id))
        self.conn.commit()
        return cursor.lastrowid

    def add_entry_to_table(self, table_id, item_id=None, subtable_id=None,
                           chance_percent=1.0, quantity_min=1, quantity_max=1,
                           is_unique=False, is_mandatory=False):
        cursor = self.conn.cursor()

        # Проверяем, что указан либо предмет, либо подтаблица
        if item_id is None and subtable_id is None:
            raise ValueError("Должен быть указан item_id или subtable_id")

        cursor.execute('''
            INSERT INTO table_entries 
            (table_id, item_id, subtable_id, chance_percent, quantity_min, quantity_max,
             is_unique, is_mandatory)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            table_id,
            item_id,
            subtable_id,
            chance_percent,
            quantity_min,
            quantity_max,
            1 if is_unique else 0,
            1 if is_mandatory else 0
        ))
        self.conn.commit()
        return cursor.lastrowid

    def generate_from_table(self, table_id, rolls=1, min_items=1, max_items=1):
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT te.id, te.item_id, te.subtable_id, te.chance_percent,
                   te.quantity_min, te.quantity_max,
                   te.is_unique, te.is_mandatory,
                   i.name as item_name, lt.name as table_name
            FROM table_entries te
            LEFT JOIN items i ON te.item_id = i.id
            LEFT JOIN loot_tables lt ON te.subtable_id = lt.id
            WHERE te.table_id = ?
        ''', (table_id,))

        entries = cursor.fetchall()
        if not entries:
            return []

        loot_results = []

        for _ in range(rolls):

            mandatory_entries = []
            unique_entries = []
            normal_entries = []

            # Разделяем по типам
            for entry in entries:
                (
                    entry_id, item_id, subtable_id, chance_percent,
                    qty_min, qty_max, is_unique, is_mandatory,
                    item_name, table_name
                ) = entry

                entry_data = {
                    "item_id": item_id,
                    "subtable_id": subtable_id,
                    "chance_percent": chance_percent,
                    "qty_min": qty_min,
                    "qty_max": qty_max,
                    "item_name": item_name,
                    "table_name": table_name
                }

                if is_mandatory:
                    mandatory_entries.append(entry_data)
                elif is_unique:
                    unique_entries.append(entry_data)
                else:
                    normal_entries.append(entry_data)

            roll_loot = []

            # ---- 1. Обязательные ----
            for entry in mandatory_entries:
                quantity = random.randint(entry["qty_min"], entry["qty_max"])
                roll_loot.extend(
                    self._resolve_entry(entry, quantity)
                )

            # ---- 2. Уникальные ----
            successful_unique = []

            for entry in unique_entries:
                if random.random() * 100 <= entry["chance_percent"]:
                    successful_unique.append(entry)

            if successful_unique:
                chosen = random.choice(successful_unique)
                quantity = random.randint(chosen["qty_min"], chosen["qty_max"])
                roll_loot.extend(
                    self._resolve_entry(chosen, quantity)
                )

            # ---- 3. Обычные ----
            successful_normals = []

            for entry in normal_entries:
                if random.random() * 100 <= entry["chance_percent"]:
                    quantity = random.randint(entry["qty_min"], entry["qty_max"])
                    successful_normals.append(
                        (entry, quantity)
                    )

            # Определяем сколько обычных брать
            num_items = random.randint(min_items, max_items)

            if successful_normals:
                selected = random.sample(
                    successful_normals,
                    min(num_items, len(successful_normals))
                )

                for entry, quantity in selected:
                    roll_loot.extend(
                        self._resolve_entry(entry, quantity)
                    )

            loot_results.extend(roll_loot)

        return loot_results

    def generate_container_loot(self, container_id, rolls=1, min_items=0, max_items=None):
        cursor = self.conn.cursor()
        cursor.execute('SELECT loot_table_id FROM containers WHERE id = ?', (container_id,))
        result = cursor.fetchone()
        if not result or not result[0]:
            return []

        loot_table_id = result[0]

        loot = []
        for _ in range(rolls):
            loot.extend(self.generate_from_table(loot_table_id, 1))

        # Добиваем до min_items
        while len(loot) < min_items:
            loot.extend(self.generate_from_table(loot_table_id, 1))

        # Обрезаем до max_items
        if max_items is not None and len(loot) > max_items:
            loot = random.sample(loot, max_items)

        return loot

    def get_all_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, description FROM loot_tables')
        return cursor.fetchall()

    def get_all_items(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, category FROM items')
        return cursor.fetchall()

    def get_all_containers(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.id, c.name, c.description, lt.name as table_name
            FROM containers c
            LEFT JOIN loot_tables lt ON c.loot_table_id = lt.id
        ''')
        return cursor.fetchall()

    def get_table_entries(self, table_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT te.id,
                   te.item_id,
                   te.subtable_id,
                   te.chance_percent,
                   te.quantity_min,
                   te.quantity_max,
                   COALESCE(i.name, lt.name) as entry_name,
                   CASE 
                       WHEN te.item_id IS NOT NULL THEN 'Item'
                       ELSE 'Table'
                   END as entry_type,
                   te.is_unique,
                   te.is_mandatory
            FROM table_entries te
            LEFT JOIN items i ON te.item_id = i.id
            LEFT JOIN loot_tables lt ON te.subtable_id = lt.id
            WHERE te.table_id = ?
            ORDER BY te.id
        ''', (table_id,))
        return cursor.fetchall()


    def _resolve_entry(self, entry, quantity):
        result = []

        if entry["item_id"] and entry["item_name"]:
            result.append({
                "name": entry["item_name"],
                "quantity": quantity
            })

        elif entry["subtable_id"] and entry["table_name"]:
            sub_loot = self.generate_from_table(
                entry["subtable_id"],
                rolls=1,
                min_items=1,
                max_items=1
            )
            result.extend(sub_loot)

        return result