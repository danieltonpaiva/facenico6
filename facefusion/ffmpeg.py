from typing import List
import subprocess

import facefusion.globals
from facefusion import logger
from facefusion.filesystem import get_temp_frames_pattern, get_temp_output_video_path
from facefusion.vision import detect_fps, count_video_frame_total
import ffmpeg
from tqdm import tqdm


def run_ffmpeg(input_command : List[str], desc="Processando video", target_path=""):
    frames = count_video_frame_total(target_path)
    commands = [ 'ffmpeg']
    commands.extend(input_command)
    # Cria um objeto tqdm para exibir a barra de progresso
    with tqdm(total=frames, desc=desc, position=0, leave=True) as progress:
        # Abre um processo para executar o comando ffmpeg
        process = subprocess.Popen(
            commands,
            stderr=subprocess.PIPE,  # Captura a saída de erro do ffmpeg
            universal_newlines=True,  # Usa strings para texto (em vez de bytes)
            bufsize=1,  # Buffer de linha a linha
        )

        # Lê a saída de erro do processo linha por linha
        for line in process.stderr:
            # Aqui você precisaria analisar a saída do ffmpeg para extrair informações de progresso
            # e atualizar a barra de progresso. Isso depende do formato específico de saída do ffmpeg.

            # Exemplo: Verifica se a linha contém informações de progresso
            if "frame=" in line and "fps=" in line:
                # Extraia o número do frame atual e atualize a barra de progresso
                current_frame = int(line.split("frame=")[1].split()[0])
                progress.update(current_frame - progress.n)

        # Aguarde o término do processo
        process.wait()

    # Verifica o código de saída do processo
    if process.returncode != 0:
        print(f"Erro ao executar o comando: {input_command}")

    return True

def run_ffmpeg2(args : List[str]) -> bool:
	commands = [ 'ffmpeg', '-hide_banner', '-loglevel', 'error' ]
	commands.extend(args)
	try:
		subprocess.run(commands, stderr = subprocess.PIPE, check = True)
		return True
	except subprocess.CalledProcessError as exception:
		logger.debug(exception.stderr.decode().strip(), __name__.upper())
		return False


def open_ffmpeg(args : List[str]) -> subprocess.Popen[bytes]:
	commands = [ 'ffmpeg', '-hide_banner', '-loglevel', 'error' ]
	commands.extend(args)
	return subprocess.Popen(commands, stdin = subprocess.PIPE)


def extract_frames(target_path : str, fps : float) -> bool:
	temp_frame_compression = round(31 - (facefusion.globals.temp_frame_quality * 0.31))
	trim_frame_start = facefusion.globals.trim_frame_start
	trim_frame_end = facefusion.globals.trim_frame_end
	temp_frames_pattern = get_temp_frames_pattern(target_path, '%04d')
	commands = [ '-hwaccel', 'auto', '-i', target_path, '-q:v', str(temp_frame_compression), '-pix_fmt', 'rgb24' ]
	if trim_frame_start is not None and trim_frame_end is not None:
		commands.extend([ '-vf', 'trim=start_frame=' + str(trim_frame_start) + ':end_frame=' + str(trim_frame_end) + ',fps=' + str(fps) ])
	elif trim_frame_start is not None:
		commands.extend([ '-vf', 'trim=start_frame=' + str(trim_frame_start) + ',fps=' + str(fps) ])
	elif trim_frame_end is not None:
		commands.extend([ '-vf', 'trim=end_frame=' + str(trim_frame_end) + ',fps=' + str(fps) ])
	else:
		commands.extend([ '-vf', 'fps=' + str(fps) ])
	commands.extend([ '-vsync', '0', temp_frames_pattern ])
	return run_ffmpeg(commands, "Extraindo frames", target_path)


def compress_image(output_path : str) -> bool:
	output_image_compression = round(31 - (facefusion.globals.output_image_quality * 0.31))
	commands = [ '-hwaccel', 'auto', '-i', output_path, '-q:v', str(output_image_compression), '-y', output_path ]
	return run_ffmpeg2(commands)


def merge_video(target_path : str, fps : float) -> bool:
	temp_output_video_path = get_temp_output_video_path(target_path)
	temp_frames_pattern = get_temp_frames_pattern(target_path, '%04d')
	commands = [ '-hwaccel', 'auto', '-r', str(fps), '-i', temp_frames_pattern, '-c:v', facefusion.globals.output_video_encoder ]
	if facefusion.globals.output_video_encoder in [ 'libx264', 'libx265' ]:
		output_video_compression = round(51 - (facefusion.globals.output_video_quality * 0.51))
		commands.extend([ '-crf', str(output_video_compression) ])
	if facefusion.globals.output_video_encoder in [ 'libvpx-vp9' ]:
		output_video_compression = round(63 - (facefusion.globals.output_video_quality * 0.63))
		commands.extend([ '-crf', str(output_video_compression) ])
	if facefusion.globals.output_video_encoder in [ 'h264_nvenc', 'hevc_nvenc' ]:
		output_video_compression = round(51 - (facefusion.globals.output_video_quality * 0.51))
		commands.extend([ '-cq', str(output_video_compression) ])
	commands.extend([ '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-y', temp_output_video_path ])
	return run_ffmpeg(commands, "Criando o vídeo", target_path)

def get_crf_value(quality):
    if facefusion.globals.output_video_encoder in ['libx264', 'libx265']:
        return round(51 - (quality * 0.51))
    elif facefusion.globals.output_video_encoder in ['libvpx-vp9']:
        return round(63 - (quality * 0.63))
    elif facefusion.globals.output_video_encoder in ['h264_nvenc', 'hevc_nvenc']:
        return round(51 - (quality * 0.51))
    else:
        return None  # Add handling for other cases as needed

def merge_video2(target_path: str, fps: float) -> bool:
    temp_output_video_path = get_temp_output_video_path(target_path)
    temp_frames_pattern = get_temp_frames_pattern(target_path, '%04d')

    ffmpeg.input(temp_frames_pattern, r=fps, hwaccel='cuda').output(
        temp_output_video_path,
        vcodec=facefusion.globals.output_video_encoder,
        crf=get_crf_value(facefusion.globals.output_video_quality),
        pix_fmt='yuv420p',
        colorspace='bt709',
        y='-y'
    ).run()

    return True  # Replace with appropriate logic for success/failure


def restore_audio(target_path : str, output_path : str) -> bool:
	fps = detect_fps(target_path)
	trim_frame_start = facefusion.globals.trim_frame_start
	trim_frame_end = facefusion.globals.trim_frame_end
	temp_output_video_path = get_temp_output_video_path(target_path)
	commands = [ '-hwaccel', 'auto', '-i', temp_output_video_path ]
	if trim_frame_start is not None:
		start_time = trim_frame_start / fps
		commands.extend([ '-ss', str(start_time) ])
	if trim_frame_end is not None:
		end_time = trim_frame_end / fps
		commands.extend([ '-to', str(end_time) ])
	commands.extend([ '-i', target_path, '-c', 'copy', '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_path ])
	return run_ffmpeg2(commands)
