import subprocess
from pathlib import Path
import pyseq


def get_ffmpeg_executable() -> str:
    return 'ffmpeg'


def sequence_to_video(sequence: list[str], output_dir: Path, fps: int):
    sq = pyseq.Sequence(sequence)
    input_image_pattern = sq.format('%D%h%p%t')
    output_file = Path(output_dir) / f'output.mp4'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        get_ffmpeg_executable(),
        '-framerate', str(fps),
        '-i', input_image_pattern,
        '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
        '-c:v', 'libx264',
        '-crf', '18',
        '-preset', 'slow',
        '-pix_fmt', 'yuv420p',
        output_file
    ]
    print('FFMPEG CMD:', ' '.join(map(str, cmd)))
    resp = subprocess.run(cmd)
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