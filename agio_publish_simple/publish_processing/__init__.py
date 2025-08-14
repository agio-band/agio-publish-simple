from pathlib import Path
from ._base import PublishProcessingBase
from agio.core.utils.modules_utils import import_modules_from_dir


def iter_publishers():
    root = Path(__file__).parent
    name = __name__.rsplit('.', 1)[0]
    import_modules_from_dir(root, name)
    for cls in PublishProcessingBase.__subclasses__():
        yield cls


def get_publisher(product_type: str):
    for cls in iter_publishers():
        if cls.product_type == product_type:
            return cls
    raise ValueError(f'Unknown product type: {product_type}')