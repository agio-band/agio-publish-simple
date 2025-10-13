from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCursor, QScreen
from PySide6.QtCore import QPoint

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
    show_on_center(dialog, app)
    try:
        app.exec()
    except KeyboardInterrupt:
        app.quit()


def show_on_center(widget, app):
    cursor_pos: QPoint = QCursor.pos()
    current_screen: QScreen = app.screenAt(cursor_pos)
    if current_screen is None:
        current_screen = app.primaryScreen()
        if current_screen is None:
            print("Ошибка: Не удалось найти ни один экран.")
            return
    screen_geometry = current_screen.availableGeometry()
    widget_frame = widget.frameGeometry()
    new_x = screen_geometry.x() + (screen_geometry.width() - widget_frame.width()) // 2
    new_y = screen_geometry.y() + (screen_geometry.height() - widget_frame.height()) // 2
    widget.move(new_x, new_y)
    widget.show()
