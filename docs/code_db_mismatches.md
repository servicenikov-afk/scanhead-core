## code_db_mismatches.md

### 1. Потокобезопасность NomenclatureAdapter.search_async()

**Файл:** `gui/services/adapters/nomenclature_adapter.py`

**Проблема:** Метод `search_async()` вызывает callback из фонового потока, что небезопасно для Tkinter/CustomTkinter.

**Код с проблемой:**
```python
def search_async(self, query: str, callback: Callable[[List['Product']], None]) -> None:
    def _search_thread():
        results = self.search(query)
        callback(results)  # ← Вызов из фонового потока!
    thread = threading.Thread(target=_search_thread, daemon=True)
    thread.start()
```
**Решение:** Использовать `master.after(0, callback)` для передачи результата в главный поток GUI.