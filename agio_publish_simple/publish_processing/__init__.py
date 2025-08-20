from pathlib import Path
from ._base import PublishProcessingBase
from agio.core.utils.modules_utils import import_modules_from_dir, iter_subclasses


def iter_publishers():
    import_modules_from_dir(Path(__file__).parent, __name__)
    yield from iter_subclasses(PublishProcessingBase)


def get_publisher(product_type: str):
    for cls in iter_publishers():
        if cls.product_type == product_type:
            return cls
    raise ValueError(f'Unknown product type: {product_type}')