from loot_manager import manager
from loot_ui import ui
import tkinter as tk

def main():
    db_path = "data/dnd_loot_tables.db"  # путь к БД
    loot_manager = manager.LootTableManager(db_path=db_path)

    root = tk.Tk()
    app = ui.LootTableApp(root, loot_manager)
    root.mainloop()

if __name__ == "__main__":
    main()
