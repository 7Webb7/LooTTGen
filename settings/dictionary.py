translations = {
    "Русский": {
        "add_item": "Добавить предмет",
        "loot_table": "Таблица лута",
        "container": "Контейнер",
        "generate": "Генерация",
        "save": "Сохранить",
        "cancel": "Отмена",
        "settings": 'Настройки',
        'items' : 'Предметы'
    },
    "English": {
        "add_item": "Add Item",
        "loot_table": "Loot Table",
        "container": "Container",
        "generate": "Generate",
        "save": "Save",
        "cancel": "Cancel",
        'settings': 'Settings',
        'items' : 'Items'
        # … другие ключи
    }
}


def _(text, key):
    return translations[key][text]

