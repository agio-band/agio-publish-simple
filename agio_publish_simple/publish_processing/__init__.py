from __future__ import annotations
from pathlib import Path

from agio_pipe.entities import product_type as pt
from ._base import PublishProcessingBase
from agio.core.utils.modules_utils import import_modules_from_dir, iter_subclasses


def iter_publishers():
    import_modules_from_dir(Path(__file__).parent, __name__)
    yield from iter_subclasses(PublishProcessingBase)


def get_publisher(product_type: str|dict|pt.AProductType):
    if isinstance(product_type, pt.AProductType):
        product_type = product_type.name
    elif isinstance(product_type, dict):
        product_type = product_type['name']
    for cls in iter_publishers():
        if cls.product_type == product_type:
            return cls
    raise ValueError(f'Unknown product type: {product_type}')