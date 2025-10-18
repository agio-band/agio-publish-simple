import yaml
from pathlib import Path

__all__ = ['__version__']
__version__ = yaml.safe_load(Path(__file__, '../__agio__.yml').resolve().read_text(encoding='utf-8'))['version']
