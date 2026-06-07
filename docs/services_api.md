# API сервисов

## ProductDetailsService

**Файл:** `gui/services/product_details_service.py`

Сервис агрегации детальной информации о товаре из трёх источников.

### Класс: `ProductDetailsService`

#### Конструктор

```python
def __init__(
    self,
    nomenclature_adapter: NomenclatureAdapter,
    store_adapter: StoreAdapter,
    css_adapter: CssExportAdapter
)
```

**Параметры:**
- `nomenclature_adapter` - адаптер к базе номенклатуры
- `store_adapter` - адаптер к базе складских адресов
- `css_adapter` - адаптер к базе запчастей Franke

---

#### Метод: `get_product_details()`

Получить детальную информацию о товаре по артикулу.

```python
def get_product_details(
    self,
    article: str,
    callback: Optional[Callable[[Optional[Product]], None]] = None
) -> Optional[Product]
```

**Параметры:**
- `article` - Артикул товара для поиска
- `callback` - Опциональный callback для асинхронного результата

**Возвращает:**
- `Product` с заполненными полями или `None`

**Пример использования (асинхронно):**
```python
def on_loaded(product: Optional[Product]):
    if product:
        print(f"Найдено: {product.name}")
        print(f"Адреса: {product.storage_locations}")
        print(f"Модели: {product.models}")

service.get_product_details("566.0000.004", callback=on_loaded)
```

**Пример использования (синхронно):**
```python
product = service.get_product_details("566.0000.004", callback=None)
if product:
    print(product.unit)
```

---

#### Метод: `get_enriched_product_sync()`

Синхронная версия получения данных (для использования в диалогах).

```python
def get_enriched_product_sync(self, article: str) -> Optional[Product]
```

**Параметры:**
- `article` - Артикул товара

**Возвращает:**
- `Product` или `None`

---

### Модель данных: `Product`

**Файл:** `libs/domain_models/product.py`

```python
@dataclass
class Product:
    article: str                              # Артикул товара
    name: str                                 # Наименование товара
    barcodes: List[str]                       # Список штрих-кодов
    address: Optional[str] = None             # Адрес хранения (основной)
    unit: Optional[str] = None                # Единица измерения
    description: Optional[str] = None         # Описание товара
    category: Optional[str] = None            # Категория товара
    manufacturer_info: List[Dict[str, Any]]   # Информация от производителя
    storage_locations: List[str]              # Все адреса хранения
    models: List[str]                         # Модели оборудования
```

---

## Адаптеры

### NomenclatureAdapter

**Файл:** `gui/services/adapters/nomenclature_adapter.py`

Адаптер для работы с основной базой номенклатуры (`nomenclature.db`).

#### Основные методы:

```python
def search(self, query: str) -> List[Product]
```
Поиск товаров по артикулу, названию или штрихкоду.

```python
def get_by_article(self, article: str) -> Optional[Product]
```
Получить товар по точному артикулу.

```python
def search_async(self, query: str, callback: Callable[[List[Product]], None]) -> None
```
Асинхронный поиск товаров.

---

### StoreAdapter

**Файл:** `gui/services/adapters/store_adapter.py`

Адаптер для управления адресами хранения товаров (`store.db`).

#### Основные методы:

```python
def get_location(self, article: str) -> Optional[str]
```
Получить первый адрес хранения для товара.

```python
def get_all_locations(self, article: str) -> List[str]
```
Получить все адреса хранения для товара.

```python
def update_location(self, article: str, location: str) -> bool
```
Обновить или создать адрес хранения.

```python
def set_locations(self, article: str, locations: List[str], notes: str = None) -> bool
```
Установить полный список адресов.

---

### CssExportAdapter

**Файл:** `gui/services/adapters/css_export_adapter.py`

Адаптер для получения данных о запчастях из `css_export.db`.

#### Основные методы:

```python
def get_by_article(self, article: str) -> List[Dict[str, Any]]
```
Получить информацию о детали по артикулу (может быть несколько записей для разных моделей).

**Возвращаемая структура:**
```python
{
    'product_model': str,           # Модель оборудования
    'position': str,                # Позиция в спецификации
    'art_no': str,                  # Артикул
    'name': str,                    # Название детали
    'usage_path': str,              # Путь использования
    'category1': str,               # Категория 1
    'category2': str,               # Категория 2
    'category3': str,               # Категория 3
    'production_date_from': str,    # Дата начала производства
    'production_date_to': str,      # Дата окончания производства
    'serial_from': str,             # Серийный номер ОТ
    'serial_to': str                # Серийный номер ДО
}
```

```python
def search_by_name(self, query: str) -> List[Dict[str, Any]]
```
Поиск деталей по названию.

---

## ProductInfoDialog

**Файл:** `gui/dialogs/product_info_dialog.py`

Диалог отображения детальной информации о товаре.

### Конструктор

```python
def __init__(
    self,
    master: Any,
    product: Dict[str, Any],
    nomenclature_adapter: Any = None,
    store_adapter: Any = None,
    css_adapter: Any = None,
    font_size: int = 14,
    details_service: Optional[ProductDetailsService] = None
)
```

**Параметры:**
- `master` - Родительское окно
- `product` - Словарь с данными товара
- `details_service` - Сервис для загрузки полных данных (рекомендуется)

### Вкладки диалога

1. **"📦 Номенклатура"** - данные из `nomenclature.db`
   - Артикул
   - Альт. артикул
   - Наименование
   - Штрихкоды
   - Ед. изм.
   - Описание
   - Категория

2. **"📍 Адрес хранения"** - данные из `store.db`
   - Текущий адрес
   - Редактирование адреса

3. **"📎 Дополнительно"** - данные из `css_export.db`
   - Модели оборудования
   - Информация от производителя
   - Расположение в спецификации

---

## 📝 Примечания

1. Все адаптеры поддерживают read-only режим для производственных БД
2. Сервис `ProductDetailsService` выполняет асинхронную загрузку данных в отдельном потоке
3. Для корректной работы необходимо передать все три адаптера в сервис
4. Физические файлы БД находятся только на тестовой машине
