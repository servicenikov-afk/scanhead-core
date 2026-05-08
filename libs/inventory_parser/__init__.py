"""
Inventory Parser Module for ScanHead Core.

Provides functionality to parse inventory files (Excel format) and extract
product positions with articles, names, quantities, and addresses.

Usage:
    # Simple usage with function
    from libs.inventory_parser import parse_inventory_file
    positions = parse_inventory_file("path/to/inventory.xlsx")
    
    # Advanced usage with class
    from libs.inventory_parser import InventoryParser
    parser = InventoryParser()
    positions = parser.parse_inventory_file("path/to/inventory.xlsx")
"""

from .core import InventoryParser


def parse_inventory_file(file_path: str):
    """
    Convenience function to parse an inventory file without creating a parser instance.
    
    Args:
        file_path: Path to the Excel file (.xlsx, .xls)
        
    Returns:
        List of dictionaries containing product information
    """
    parser = InventoryParser()
    return parser.parse_inventory_file(file_path)


__all__ = ['InventoryParser', 'parse_inventory_file']
__version__ = '1.0.0'
