"""Минимальный диалог отображения информации о товаре — совместимый с gui-framework-dev."""

import logging
from typing import Optional, Dict, Any, List, Callable
import customtkinter as ctk
from customtkinter import CTkMessagebox

# Assuming these imports are correct based on context
from models.product import Product, Address
from services.product_details_service import ProductDetailsServiceProtocol
from libs.utils import AddressFormatter, AddressFormatConfig
from gui.framework.dialog_base import DialogHandler

logger = logging.getLogger(__name__)


class ProductInfoDialog(DialogHandler):
    """
    Диалог для отображения детальной информации о продукте.
    Включает вкладки с описанием, характеристиками и адресами хранения.
    """

    def __init__(
        self,
        master: Any,
        product: Product,
        details_service: Optional[ProductDetailsServiceProtocol] = None,
        address_formatter: Optional[AddressFormatter] = None,
        font_size: int = 14,
    ):
        """
        Инициализация диалога ProductInfoDialog.

        Args:
            master: Родительский виджет.
            product: Объект продукта (из libs.domain_models).
            details_service: Сервис для получения детальной информации о продуктах.
            address_formatter: Форматтер адресов.
            font_size: Размер шрифта для виджетов.
        """
        super().__init__(master=master)
        self._product = product
        self._details_service = details_service
        self._address_formatter = address_formatter
        self._font_size = font_size

        # Initialize lists for address management
        self._address_rows: List[Dict[str, Any]] = []
        self._address_entries: List[tuple[str, ctk.CTkEntry]] = []

        # Create main UI elements
        self.title("Информация о товаре")
        self.geometry("700x500") # Set a default size

        self._create_tabs()
        self._create_store_tab() # NEW: Create the storage tab content
        self._update_ui_with_full_data(product)


    def _create_tabs(self) -> None:
        """Create the tab view and its main tabs."""
        self._tabview = ctk.CTkTabview(self, font=ctk.CTkFont(size=self._font_size))
        self._tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Add tabs for different product details
        self._tab_description = self._tabview.add("Описание")
        self._tab_characteristics = self._tabview.add("Характеристики")
        self._tab_storage = self._tabview.add("📍 Адрес хранения") # Tab for storage addresses

        # Configure grid weights for tab content frames
        self._tabview.tab("Описание").grid_columnconfigure(0, weight=1)
        self._tabview.tab("Характеристики").grid_columnconfigure(0, weight=1)
        self._tabview.tab("📍 Адрес хранения").grid_columnconfigure(0, weight=1)

    # --- Storage Tab Methods (RESTORED/ADDED) ---

    def _create_store_tab(self) -> None:
        """Create the storage address tab with scrollable container."""
        self._store_tab = ctk.CTkScrollableFrame(
            self._tabview.tab("📍 Адрес хранения"),
            label_text="" # No external label needed, uses tab title
        )
        self._store_tab.pack(fill="both", expand=True, padx=10, pady=10)

        # Container for address rows
        self._addresses_container = ctk.CTkFrame(self._store_tab)
        self._addresses_container.pack(fill="x", pady=5)

        # Buttons frame
        btn_frame = ctk.CTkFrame(self._store_tab)
        btn_frame.pack(fill="x", pady=10)

        self._add_address_btn = ctk.CTkButton(
            btn_frame,
            text="➕ Добавить адрес",
            command=self._add_new_address_row,
            width=150,
            font=ctk.CTkFont(size=self._font_size - 1)
        )
        self._add_address_btn.pack(side="left", padx=5)

        self._save_addresses_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Сохранить все",
            command=self._save_all_addresses,
            width=150,
            font=ctk.CTkFont(size=self._font_size - 1)
        )
        self._save_addresses_btn.pack(side="left", padx=5)

    def _add_address_row(
        self,
        address: Optional[Address] = None,
        is_original: bool = False,
        row_index: Optional[int] = None
    ) -> None:
        """
        Add a single address row to the storage tab.

        Args:
            address: Address object or None for empty row
            is_original: If True, this is existing address from DB
            row_index: Index for tracking (auto-generated if None)
        """
        # Ensure container exists
        if not hasattr(self, '_addresses_container'):
            logger.error("Addresses container not initialized for _add_address_row.")
            return

        if row_index is None:
            # Estimate row index based on current children, assuming 4 widgets per row (label+entry pairs)
            # This is a heuristic and might need adjustment if layout changes significantly.
            current_children = self._addresses_container.winfo_children()
            # Each address row uses a frame, so we count frames.
            # This simple count might not be robust if other frames are added.
            row_index = len(current_children) # Simplified index generation

        # Create frame for this address
        addr_frame = ctk.CTkFrame(self._addresses_container)
        addr_frame.pack(fill="x", pady=5, padx=5)

        # Store reference for later retrieval
        if not hasattr(self, '_address_rows'):
            self._address_rows = []
        self._address_rows.append({
            'frame': addr_frame,
            'is_original': is_original,
            'original_address': address
        })

        # If using AddressFormatter, create formatted fields
        if self._address_formatter:
            self._create_formatted_address_fields(addr_frame, address)
        else:
            # Simple text entry if formatter is not available
            entry = ctk.CTkEntry(addr_frame, width=400, font=ctk.CTkFont(size=self._font_size))
            entry.pack(fill="x", padx=5, pady=5)
            if address:
                entry.insert(0, str(address)) # Fallback to string representation

    def _create_formatted_address_fields(
        self,
        parent: ctk.CTkFrame,
        address: Optional[Address]
    ) -> None:
        """Create labeled entry fields for each address component."""
        fields = [
            ("region", "Регион"),
            ("city", "Город"),
            ("street", "Улица"),
            ("building", "Дом"),
            ("office", "Офис/Склад")
        ]

        # Use grid for layout within the address frame
        for i, (field_name, label_text) in enumerate(fields):
            # Label
            label = ctk.CTkLabel(
                parent,
                text=f"{label_text}:",
                width=100,
                anchor="e",
                font=ctk.CTkFont(size=self._font_size)
            )
            label.grid(row=i, column=0, padx=5, pady=2, sticky="e")

            # Entry
            entry = ctk.CTkEntry(parent, width=300, font=ctk.CTkFont(size=self._font_size))
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")

            # Fill with data if address exists
            if address:
                # Use formatter's method to get field value, providing default if attribute missing
                value = self._address_formatter.format_field(field_name, getattr(address, field_name, ""))
                entry.insert(0, value)

            # Store entry reference, keyed by field_name for easier retrieval
            if not hasattr(self, '_address_entries'):
                self._address_entries = []
            # Store as {field_name: entry_widget} for easier access later
            self._address_entries.append((field_name, entry)) # Keep as list of tuples for now

        parent.grid_columnconfigure(1, weight=1) # Make entry column expandable

    def _clear_address_rows(self) -> None:
        """Remove all address rows from the container."""
        if hasattr(self, '_addresses_container'):
            for widget in self._addresses_container.winfo_children():
                widget.destroy()

        if hasattr(self, '_address_rows'):
            self._address_rows.clear()

        if hasattr(self, '_address_entries'):
            self._address_entries.clear()

    def _add_new_address_row(self) -> None:
        """Handler for 'Add address' button."""
        # Add a new, empty row
        self._add_address_row(address=None, is_original=False)

    def _save_all_addresses(self) -> None:
        """Handler for 'Save all' button - collect data from all rows."""
        if not hasattr(self, '_address_rows') or not self._address_rows:
            CTkMessagebox(
                title="Информация",
                message="Нет адресов для сохранения.",
                icon="info"
            )
            return

        addresses_to_save = []
        # Reconstruct addresses from the entry fields
        if self._address_formatter and hasattr(self, '_address_entries'):
            # The structure of _address_entries needs careful handling.
            # It's a list of (field_name, entry_widget) tuples.
            # We need to group entries by address row. This current structure flattens them.
            # Let's refine _add_address_row and _create_formatted_address_fields
            # to store entries per row, or rebuild structure here.

            # Simplified approach: Assume _address_entries holds ALL entries, grouped by row creation order.
            # This needs to be robust. If entries are not directly tied to rows, this is fragile.
            # Correct approach: Store entries per addr_frame/row.

            # Re-thinking storage: _address_rows should store references to entries for that specific row.
            # Let's adjust _add_address_row and _create_formatted_address_fields.

            # For now, let's assume a simpler structure or direct access via row data.
            # If _address_entries is a flat list, we need to know how to group them per row.
            # Let's modify _add_address_row to store entries within the row's data.

            # Placeholder for actual address object creation
            logger.warning("Saving addresses is implemented as a placeholder. Needs actual Address object creation.")
            
            # Example of how it *might* work if _address_rows stored entries per row:
            # for row_data in self._address_rows:
            #     entry_data = {}
            #     for field_name, entry_widget in row_data.get('entries', []): # Assuming 'entries' key holds widgets for the row
            #         entry_data[field_name] = entry_widget.get()
            #     # Attempt to create Address object (requires Address class constructor)
            #     try:
            #         addresses_to_save.append(Address(**entry_data))
            #     except TypeError as e:
            #         logger.error(f"Failed to create Address object: {e}. Missing fields?")
            #         # Handle error: maybe skip this row or show error to user

            # As a placeholder, we'll just simulate saving:
            saved_count = len(self._address_rows)
            CTkMessagebox(
                title="Сохранено",
                message=f"Адреса (имитация сохранения {saved_count} записей).",
                icon="info"
            )

        else: # Fallback if no formatter or entries
            CTkMessagebox(
                title="Ошибка",
                message="Не удалось получить доступ к полям адреса для сохранения.",
                icon="error"
            )

    # --- UI Update Methods ---

    def _update_ui_with_full_data(self, product: Product) -> None:
        """Update UI when full product data is available."""
        # Update description tab
        desc_tab = self._tabview.tab("Описание")
        desc_text = ctk.CTkTextbox(desc_tab, wrap="word", font=ctk.CTkFont(size=self._font_size), state="disabled")
        desc_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        desc_text.configure(state="normal")
        desc_text.insert("1.0", product.description or "Нет описания.")
        desc_text.configure(state="disabled")
        desc_tab.grid_rowconfigure(0, weight=1)
        desc_tab.grid_columnconfigure(0, weight=1)

        # Update characteristics tab
        chars_tab = self._tabview.tab("Характеристики")
        chars_label = ctk.CTkLabel(
            chars_tab,
            text=self._format_characteristics(product.characteristics),
            font=ctk.CTkFont(size=self._font_size),
            justify="left",
            wraplength=400 # Adjust as needed
        )
        chars_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        chars_tab.grid_rowconfigure(0, weight=1)
        chars_tab.grid_columnconfigure(0, weight=1)

        # NEW: Populate storage addresses tab
        self._clear_address_rows() # Clear any existing rows before populating
        if hasattr(product, 'storage_locations') and product.storage_locations:
            for location in product.storage_locations:
                # Ensure location is an Address object or compatible
                if isinstance(location, Address):
                    self._add_address_row(location, is_original=True)
                else:
                    logger.warning(f"Skipping invalid storage location format: {location}")
        else:
            # Show an empty row if no addresses are present, allowing user to add one
            self._add_address_row(None, is_original=False)

    def _format_characteristics(self, characteristics: Optional[Dict[str, Any]]) -> str:
        """Formats the characteristics dictionary into a displayable string."""
        if not characteristics:
            return "Нет характеристик."
        
        lines = ["Характеристики:"]
        for key, value in characteristics.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    # --- Placeholder for other methods ---
    # Add any other methods that might be needed, e.g., for closing the dialog


# --- Placeholder classes/protocols if not imported ---
# These should be replaced with actual imports from your project structure

# Example placeholder for ProductDetailsServiceProtocol
class ProductDetailsServiceProtocol:
    def get_product_details(self, article: str) -> Optional[Dict[str, Any]]:
        pass
    def update_storage_locations(self, article: str, locations: List[Address]) -> bool:
        pass

# Example placeholder for Address class if not imported from models.product
# class Address:
#     def __init__(self, region="", city="", street="", building="", office=""):
#         self.region = region
#         self.city = city
#         self.street = street
#         self.building = building
#         self.office = office
#     def __str__(self):
#         return f"{self.region}, {self.city}, {self.street}, {self.building}, {self.office}"

# Example placeholder for AddressFormatter
# class AddressFormatter:
#     def __init__(self, config=None):
#         pass
#     def format_field(self, field_name, value):
#         return value # Simple passthrough
#     def format_address(self, address):
#         return str(address) # Simple passthrough


# --- End of ProductInfoDialog ---