from agio_pipe.schemas.version import PublishedFileFull
from agio_publish_simple.publish_processing.review import PublishProcessingReview


class PublishProcessThumbnail(PublishProcessingReview):
    product_type = "thumbnail"
    publish_filename = "thumbnail"

    def execute(self, **options):
        seq = self.extract_sequence(self.instance.sources, max_files=1)
        thumbnail_file = seq[0]
        full_path, rel_path = self.get_save_path(thumbnail_file)
        self.copy_file_to(thumbnail_file, full_path)
        print('FILE SAVED TO:', full_path)
        file = PublishedFileFull(
            path=full_path,
            relative_path=rel_path,
        )
        return [file]