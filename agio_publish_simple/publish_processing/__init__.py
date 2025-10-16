from pathlib import Path

from agio_pipe.entities.product_type import AProductType
from ._base import PublishProcessingBase
from agio.core.utils.modules_utils import import_modules_from_dir, iter_subclasses


def iter_publishers():
    import_modules_from_dir(Path(__file__).parent, __name__)
    yield from iter_subclasses(PublishProcessingBase)


def get_publisher(product_type: str|dict|AProductType):
    if isinstance(product_type, AProductType):
        product_type = product_type.name
    elif isinstance(product_type, dict):
        product_type = product_type['name']
    for cls in iter_publishers():
        if cls.product_type == product_type:
            return cls
    raise ValueError(f'Unknown product type: {product_type}')