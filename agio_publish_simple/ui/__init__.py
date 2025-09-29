from PySide6.QtWidgets import QApplication

from agio_pipe.entities.task import ATask
from agio_publish_simple.simple_scene import scene as simple_scene
from agio_publish_simple.ui import main_window


def load_containers(scene_file, selected_instances: tuple[str] = None):
    scene_plugin = simple_scene.SimplePublishScene(scene_file)
    containers = scene_plugin.get_containers()
    if selected_instances:
        containers = [con for con in containers if con.name in selected_instances]
    return containers


def show_dialog(scene_file: str = None, selected_instances: tuple[str]=None, task_id: str = None) -> None:
    containers = load_containers(scene_file, selected_instances)
    task = None
    if task_id:
        task = ATask(task_id)
    else:
        if containers:
            task = containers[0].get_task()
    if not task:
        raise Exception("No task specified")
    app = QApplication([])
    dialog = main_window.PublishDialog(
        task=task,
        workfile_extensions=['.mb', '.ma', '.hip', '.psd', '.max', '.blend', '.ae'],
        review_extensions=['.png', '.jpg', '.mp4', '.mov', '.avi']
    )
    for cont in containers:
        product_type = cont.get_product().type
        if product_type == 'workfile':
            dialog.set_workfile(cont.get_sources())
        elif product_type == 'review':
            dialog.set_review(cont.get_sources())
    dialog.show()
    try:
        app.exec()
    except KeyboardInterrupt:
        app.quit()


