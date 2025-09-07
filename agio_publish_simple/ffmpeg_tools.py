import subprocess
from pathlib import Path
import pyseq


def get_ffmpeg_executable() -> str:
    return 'ffmpeg'

COLOR_MATRIX_NAME_MAP = {
    'rec709': 'bt709'
}


def sequence_to_video(sequence: list[str], output_dir: Path, fps: int, in_color='rec709', crf=18):
    sq = pyseq.Sequence(sequence)
    input_image_pattern = sq.format('%D%h%p%t')
    output_file = Path(output_dir) / f'output.mp4'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    colorspace = COLOR_MATRIX_NAME_MAP.get(in_color, in_color)
    cmd = [
        get_ffmpeg_executable(),
        '-framerate', fps,
        '-i', input_image_pattern,
        '-vf', f'scale=trunc(iw/2)*2:trunc(ih/2)*2:'
               f'in_color_matrix={colorspace}:in_range=full',
        '-c:v', 'libx264',
        '-crf', crf,
        '-preset', 'slow',
        '-pix_fmt', 'yuv444p',
        output_file
    ]
    print('FFMPEG CMD:', ' '.join(map(str, cmd)))
    resp = subprocess.run(list(map(str, cmd)))
    if resp.returncode != 0:
        raise Exception('ffmpeg error')
    if not Path(output_file).exists():
        raise Exception(f'ffmpeg error, file not created: {output_file}')
    return output_file


def video_to_sequence(video_input: str|Path, output_dir: Path, max_files: int = None) -> list[str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        get_ffmpeg_executable(),
        '-i', video_input,
        'frame_%04d.png'
    ]
    print('FFMPEG CMD:', ' '.join(map(str, cmd)))
    subprocess.run(cmd, cwd=output_dir)
    return [x.as_posix() for x in output_dir.glob('frame_*.png')]