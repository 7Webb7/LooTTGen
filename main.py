from loot_manager.manager import LootTableManager
from loot_ui.ui import LootTableApp
import tkinter as tk

def main():
    db_path = "data/dnd_loot_tables.db"  # путь к БД
    loot_manager = LootTableManager(db_path=db_path)

    root = tk.Tk()
    app = LootTableApp(root, loot_manager)
    root.mainloop()

if __name__ == "__main__":
    main()
