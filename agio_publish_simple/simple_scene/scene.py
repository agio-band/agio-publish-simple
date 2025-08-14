import json
from pathlib import Path
from typing import Iterable

from agio_pipe.entities.product import AProduct
from agio_pipe.entities.task import ATask
from agio_pipe.exceptions import DuplicateError
from .export_container import SimpleSceneExportContainer


class SimplePublishScene:
    def __init__(self, scene_file: str = None):
        self.containers = {}
        if scene_file is not None:
            self.load_from_file(scene_file)

    def __str__(self) -> str:
        return "SimpleScene: {}".format(self.containers)

    def __repr__(self) -> str:
        return f"<SimpleScene: {len(self.containers)}>"

    def load_from_file(self, file) -> None:
        file = Path(file).expanduser()
        with file.open("r") as f:
            json_data = json.load(f)
        for data in json_data["containers"]:
            container = SimpleSceneExportContainer(data)
            self.add_container(container)

    def save(self, file: str) -> None:
        file = Path(file).expanduser()
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("w") as f:
            json.dump({
                'containers': self.get_containers_dict()
            }, f, indent=2)

    def create_container(
            self,
            name:str,
            task: ATask,
            product: AProduct,
            sources: list[str] = None,
        ) -> SimpleSceneExportContainer:
        if not isinstance(sources, Iterable):
            raise TypeError("Sources must be a list")
        cont = SimpleSceneExportContainer.create(name=name, task=task, product=product, source_objects=sources)
        self.add_container(cont)
        return cont

    def add_container(self, container: SimpleSceneExportContainer):
        if container in self.containers.values():
            raise DuplicateError(detail='Container with same parameters already exists')
        self.containers[hash(container)] = container

    def remove_container(self, container_id: str) -> SimpleSceneExportContainer|None:
        return self.containers.pop(container_id, None)

    def get_containers(self) -> list[SimpleSceneExportContainer]:
        return list(self.containers.values())

    def get_containers_dict(self):
        return [cont.to_dict() for cont in self.containers.values()]
