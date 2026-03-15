import logging
import shutil
import tempfile
from datetime import datetime
from functools import cache, cached_property
from pathlib import Path

from agio.core.entities import profile
from agio.core.events import emit
from agio_pipe.exceptions import PublishError
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.schemas.version import PublishedFileFull
from agio_pipe.utils import template_solver

logger = logging.getLogger(__name__)


class PublishProcessingBase:
    product_type = None
    default_path_template_name = 'default'
    publish_filename = 'not-set'

    def __init__(self, instance: PublishInstance, publish_options: dict|None):
        self.instance = instance
        self.project = self.instance.project
        self.publish_options = publish_options
        self.context = None
        self.__project_settings = None

    @property
    def is_no_file_mode(self):
        return self.publish_options and 'no_files' in self.publish_options.keys()

    @property
    def project_settings(self):
        if self.__project_settings is None:
            self.__project_settings = self.project.get_settings()
        return self.__project_settings

    def publish(self, **options) -> list[PublishedFileFull]:
        if not self.instance.sources:
            raise PublishError(detail=f'No sources files in instance {self.instance}')
        self.context = self.collect_context()
        return self.execute(**options)

    def execute(self, **options) -> list[PublishedFileFull]:
        raise NotImplementedError()

    @cached_property
    def tempdir(self):
        return Path(tempfile.mkdtemp())

    @cache
    def get_export_templates(self) -> dict:
        templates = self.project_settings.get('agio_pipe.publish_templates')
        if templates is None:
            raise RuntimeError('No agio publish templates configured')
        templates = {tmpl.name: tmpl for tmpl in templates}
        return templates

    def get_save_path(self, orig_file: str|Path, **options) -> tuple[str, str]:
        templates = self.get_export_templates()
        template_name = options.get('path_template_name') or self.default_path_template_name
        if template_name not in templates:
            raise NameError(f'Path template name "{template_name}" not in templates: {templates.keys()!r}')
        context = self.context.copy()
        context.update(self.create_file_context(orig_file))
        solver = template_solver.TemplateSolver({k: v.path for k, v in templates.items()})
        context.update(templates[template_name].variables or {})

        emit('pipe.publish.save_file_context_ready', {'context': context, 'template_name': template_name})

        relative_path = solver.solve(template_name, context)
        full_path = self.instance.project.company_root / relative_path
        self.context['current_template_name'] = template_name
        self.context['current_template'] = templates[template_name].path
        self.context['templates'] = templates
        self.context['save_path'] = full_path
        self.context['save_path_relative'] = str(relative_path)

        emit('pipe.publish.file_context_ready', {'context': self.context, 'template_name': template_name})

        return str(full_path), str(relative_path)

    def collect_context(self):
        # from instance
        cmp = self.instance.project.get_company()
        instance_context = dict(    # TODO Use schema
            mount_point=self.instance.project.mount_root,
            company=cmp,
            project=self.instance.project,
            task=self.instance.task,
            entity=self.instance.task.entity,
            product=self.instance.product,
            product_type=self.instance.product.type,
            variant=self.instance.product.variant,
            version=self.instance.version
        )

        # from host
        host_context = dict(
            user=profile.AProfile.current().full_name,
            current_date=datetime.now(),
            date=datetime.now().strftime('%d.%m.%Y'),
        )

        # from current app TODO
        from agio_publish_simple import __version__

        app_context = dict(
            app_name='agio_publish_simple',
            app_version=__version__
        )

        # from local settings
        local_settings_context = dict(
            local_roots=self.instance.project.get_roots(),
        )

        # product options
        publish_options = self.instance.project.fields.get('publish_options', {})
        full_context = {
            **instance_context,
            **host_context,
            **app_context,
            **local_settings_context,
            **publish_options,
        }
        emit('pipe.publish.context_ready', {'context': full_context})
        return full_context

    def create_file_context(self, file_path: str|Path) -> dict:
        file_path = Path(file_path)
        file_context = dict(
            original_file_name=file_path.stem,
            file_dirname=file_path.parent.as_posix(),
            ext=file_path.suffix.strip('.'),
            publish_filename=self.publish_filename,
        )
        return file_context

    def copy_file_to(self, src_path: str, dst_path: str) -> None:
        if not self.is_no_file_mode:
            dist_path = Path(dst_path)
            dist_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, dist_path)