from typing import Any
from uuid import uuid4
from agio_pipe.entities.product import AProduct
from agio_pipe.entities.task import ATask
from agio_pipe.publish.containers.export_container_base import ExportContainerBase


class SimpleSceneExportContainer(ExportContainerBase):

    def __init__(self, scene_container: Any):
        super().__init__(scene_container)
        self._init_entities()

    def _init_entities(self):
        for field, id_field, cls in (
                ('task', 'task_id', ATask),
                ('product', 'product_id', AProduct),
            ):
            if field not in self.obj and id_field in self.obj:
                self.obj[field] = cls(self.obj[id_field])

    @property
    def name(self):
        return self.obj.get('name')

    @property
    def id(self):
        return self.obj['id']

    @classmethod
    def create_scene_container(cls, name: str):
        return {'name': name, 'id': uuid4().hex}

    def add_source(self, value: str):
        if 'sources' not in self.obj:
            self.obj['sources'] = []
        self.obj['sources'].append(value)

    def remove_source(self, value: str):
        if value in self.obj['sources']:
            self.obj['sources'].remove(value)
            return True
        return False

    def get_sources(self):
        return self.obj['sources']

    def set_product(self, product: AProduct):
        self.obj['product'] = product

    def get_product(self) -> AProduct:
        return self.obj['product']

    def set_task(self, task: 'ATask'):
        self.obj['task'] = task

    def get_task(self) -> 'ATask':
        return self.obj.get('task')

    def set_options(self, options: dict):
        self.obj['options'] = options

    def get_options(self) -> dict:
        return self.obj.get('options', {})