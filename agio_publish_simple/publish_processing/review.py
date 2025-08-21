import json
import logging
import shutil
from pathlib import Path

import pyseq

from agio_pipe.exceptions import PublishError
from agio_pipe.schemas.version import PublishedFileFull
from agio_publish_simple.publish_processing._base import PublishProcessingBase
from agio_publish_simple import ffmpeg_tools
import mimetypes
from frame_stamp import FrameStamp

logger = logging.getLogger(__name__)


class PublishProcessingReview(PublishProcessingBase):
    product_type = "review"
    publish_filename = "review"

    def execute(self, **options):
        # get one single file and publish to project
        review_file = self.make_review_output(self.instance.sources)
        full_path, rel_path = self.get_save_path(review_file)
        logger.info('Workfile save path %s', rel_path)
        self.copy_file_to(review_file, full_path)
        print('FILE SAVED TO:', full_path)
        file = PublishedFileFull(
            path=full_path,
            relative_path=rel_path,
        )
        return [file]

    def make_review_output(self, source_files) -> str:
        # extract to images
        seq = self.extract_sequence(source_files)
        # burn in template
        burned_seq = self.process_burn_in(seq)
        # compile to video
        video_file = self.compile_to_video(burned_seq)
        return video_file

    def get_burn_in_template(self):
        return json.loads(self.project_settings.get('agio_pipe.review_template'))

    def process_burn_in(self, sequence):
        if not self.project_settings.get('agio_pipe.apply_burn_in'):
            return sequence

        new_sequence = []
        seq = pyseq.Sequence(sorted(sequence))
        output_dir = self.tempdir/'burn-in'
        output_dir.mkdir(parents=True, exist_ok=True)
        template = self.get_burn_in_template()
        for i, img in enumerate(seq):
            variables = {
                **self.context,
                "frame_num": img.frame,
                "index": i,
                "source_length": len(seq)
            }
            output_file = output_dir / img.name
            renderer = FrameStamp(img.path, template, variables)
            logger.info(f"Rendering {img.name}")
            renderer.render(save_path=output_file)
            new_sequence.append(output_file)
        return new_sequence

    def compile_to_video(self, sequence: list[str]) -> str:
        fps = self.instance.project.fields.get('fps')
        return ffmpeg_tools.sequence_to_video(sequence, self.tempdir/'render-review', fps)

    def extract_sequence(self, source_files: list[str], max_files: int = None) -> list[str]:
        if len(source_files) == 1 and Path(source_files[0]).is_dir():
            source_files = sorted(self.extract_sequence_from_dir(Path(source_files[0])))
        # from video
        if len(source_files) == 1:
            if self.is_video_file(source_files[0]):
                return sorted(ffmpeg_tools.video_to_sequence(source_files[0], self.tempdir/'from-video', max_files))
            # from single image
            else:
                self.check_valid_image_format(source_files[0])
                orig_file = Path(source_files[0])
                fps = self.instance.project.fields.get('fps')
                sequence = []
                output_dir = self.tempdir / 'extracted_sequence'
                output_dir.mkdir(parents=True, exist_ok=True)
                if max_files:
                    rng = range(min(fps, max_files))
                else:
                    rng = range(fps)
                for i in rng:
                    save_path = output_dir / f'{orig_file.stem}{i:05d}{orig_file.suffix}'
                    sequence.append(shutil.copy(orig_file, save_path))
                return sequence
        else:
            # from sequence
            self.check_valid_image_format(source_files[0])
            if max_files:
                return source_files[:max_files]
            return source_files

    def check_valid_image_format(self, file_name: str):
        mtp = mimetypes.guess_type(str(file_name))[0]
        if not mtp.startswith('image'):
            raise PublishError(detail=f'Invalid image file format {file_name}')
        ext = Path(file_name).suffix
        if ext not in ['.png', '.jpg', '.jpeg']:
            raise PublishError(detail=f'Unsupported image file format "{ext}"')

    def is_video_file(self, file_name: str) -> bool:
        mtp = mimetypes.guess_type(str(file_name))[0]
        return mtp.startswith('video')

    def extract_sequence_from_dir(self, path: Path|str) -> list[str]:
        return [x.as_posix() for x in Path(path).iterdir()]