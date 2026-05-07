"""
Core module for path utilities.

Provides universal path handling functions compatible with both
development environment and PyInstaller EXE bundles.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Union


class PathUtils:
    """
    Utility class for path operations.
    
    Provides methods for resolving paths, ensuring directories exist,
    and handling PyInstaller bundle paths.
    
    Example:
        >>> utils = PathUtils()
        >>> data_dir = utils.ensure_dir(Path("./data"))
        >>> config_path = utils.resolve_path("config/settings.json")
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize PathUtils with optional base path.
        
        Args:
            base_path: Base directory for relative path resolution.
                      If None, uses current working directory.
        """
        self._base_path = base_path or Path.cwd()
    
    @property
    def base_path(self) -> Path:
        """Get the base path for relative resolutions."""
        return self._base_path
    
    @staticmethod
    def get_bundle_path() -> Path:
        """
        Get the base path considering PyInstaller bundle.
        
        Returns:
            Path to the bundle directory if running as EXE,
            otherwise current directory.
        """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            if hasattr(sys, '_MEIPASS'):
                return Path(sys._MEIPASS)
        except Exception:
            pass
        return Path.cwd()
    
    def resolve_path(self, *parts: Union[str, Path], 
                     relative_to_base: bool = True) -> Path:
        """
        Resolve a path from given parts.
        
        Args:
            *parts: Path components to join.
            relative_to_base: If True, resolves relative to base_path.
                            If False, treats first part as absolute or cwd-relative.
        
        Returns:
            Resolved absolute Path object.
        
        Example:
            >>> utils.resolve_path("data", "config", "settings.json")
            PosixPath('/project/data/config/settings.json')
        """
        if not parts:
            return self._base_path
        
        path_parts = [str(p) for p in parts]
        
        if relative_to_base:
            result = self._base_path.joinpath(*path_parts)
        else:
            result = Path(*path_parts)
        
        return result.resolve()
    
    @staticmethod
    def ensure_dir(path: Union[str, Path], 
                   parents: bool = True, 
                   exist_ok: bool = True) -> Path:
        """
        Ensure directory exists, creating it if necessary.
        
        Args:
            path: Path to the directory.
            parents: If True, create parent directories as needed.
            exist_ok: If True, don't raise error if directory exists.
        
        Returns:
            Path object to the ensured directory.
        
        Example:
            >>> PathUtils.ensure_dir("./output/reports")
            PosixPath('/project/output/reports')
        """
        dir_path = Path(path)
        dir_path.mkdir(parents=parents, exist_ok=exist_ok)
        return dir_path
    
    def ensure_file_dir(self, file_path: Union[str, Path]) -> Path:
        """
        Ensure the parent directory of a file exists.
        
        Args:
            file_path: Path to the file.
        
        Returns:
            Path object to the parent directory.
        
        Example:
            >>> utils.ensure_file_dir("./output/report.csv")
            PosixPath('/project/output')
        """
        file_path = Path(file_path)
        return self.ensure_dir(file_path.parent)
    
    @staticmethod
    def is_running_as_exe() -> bool:
        """
        Check if the application is running as a compiled EXE.
        
        Returns:
            True if running under PyInstaller, False otherwise.
        """
        return hasattr(sys, '_MEIPASS')


def get_resource_path(relative_path: Union[str, Path]) -> Path:
    """
    Get path to a resource file, works for both dev and PyInstaller EXE.
    
    This is a standalone function for quick access without instantiating
    the PathUtils class.
    
    Args:
        relative_path: Relative path to the resource from the bundle root.
    
    Returns:
        Absolute Path to the resource.
    
    Example:
        >>> icon = get_resource_path("icons/app.ico")
        >>> with open(icon, 'rb') as f:
        ...     data = f.read()
    """
    bundle_path = PathUtils.get_bundle_path()
    return bundle_path / relative_path


def ensure_dir(path: Union[str, Path], 
               parents: bool = True, 
               exist_ok: bool = True) -> Path:
    """
    Standalone function to ensure directory exists.
    
    Args:
        path: Path to the directory.
        parents: If True, create parent directories as needed.
        exist_ok: If True, don't raise error if directory exists.
    
    Returns:
        Path object to the ensured directory.
    """
    return PathUtils.ensure_dir(path, parents, exist_ok)


def resolve_path(*parts: Union[str, Path], 
                 base: Optional[Path] = None) -> Path:
    """
    Standalone function to resolve a path.
    
    Args:
        *parts: Path components to join.
        base: Base directory for resolution. Defaults to cwd.
    
    Returns:
        Resolved absolute Path object.
    """
    utils = PathUtils(base_path=base)
    return utils.resolve_path(*parts)
