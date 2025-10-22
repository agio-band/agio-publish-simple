import shutil
import tempfile
from datetime import datetime
from functools import cache, cached_property
from pathlib import Path

from agio.core.entities import profile
from agio.core.events import emit
from agio_pipe.exceptions import PublishError
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.utils import path_solver


class PublishProcessingBase:
    product_type = None
    template_name = 'publish'
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
            self.__project_settings = self.project.workspace.get_settings()
        return self.__project_settings

    def publish(self, **options):
        if not self.instance.sources:
            raise PublishError(detail=f'No sources files in instance {self.instance}')
        self.context = self.collect_context()
        result = self.execute(**options)
        return result

    def execute(self, **options):
        raise NotImplementedError()

    @cached_property
    def tempdir(self):
        return Path(tempfile.mkdtemp())

    @cache
    def get_export_templates(self):
        templates = self.project_settings.get('agio_pipe.publish_templates')
        if templates is None:
            raise RuntimeError('No agio publish templates configured')
        templates = {tmpl.name: tmpl.pattern for tmpl in templates}
        return templates

    def get_save_path(self, orig_file: str|Path) -> [str, str]:
        templates = self.get_export_templates()
        context = self.context.copy()
        context.update(self.create_file_context(orig_file))
        solver = path_solver.TemplateSolver(templates)
        emit('pipe.publish.save_file_context_ready', {'context': context, 'template_name': self.template_name})
        full_path = solver.solve(self.template_name, context)
        company_root = Path(context['project'].get_roots()['projects']).joinpath(context['company'].code)   # TODO
        relative_path = Path(full_path).relative_to(company_root)
        self.context['current_template_name'] = self.template_name
        self.context['current_template'] = templates[self.template_name]
        self.context['templates'] = templates
        emit('pipe.publish.save_path_ready', {'full_path': full_path, 'relative_path': relative_path.as_posix()})
        self.context['save_path'] = full_path
        self.context['save_path_relative'] = relative_path.as_posix()
        emit('pipe.publish.file_context_ready', {'context': self.context, 'template_name': self.template_name})
        return full_path, relative_path.as_posix()

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
            app_name='agio-publish-simple',
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
            return shutil.copy(src_path, dist_path)