from typing import Any, IO, Optional,List
import gradio
import os
import facefusion.globals
from facefusion import wording
from facefusion.uis.typing import File
from facefusion.filesystem import are_images
from facefusion.uis.core import register_ui_component

SOURCE_FILE : Optional[gradio.File] = None
SOURCE_IMAGE : Optional[gradio.Image] = None


def render() -> None:
	global SOURCE_FILE
	global SOURCE_IMAGE

	are_source_images = are_images(facefusion.globals.source_paths)
	SOURCE_FILE = gradio.File(
		file_count = 'single',
		file_types =
		[
			'.png',
			'.jpg',
			'.webp'
		],
		label = wording.get('source_file_label'),
		value = facefusion.globals.source_path if are_source_images else None
	)
	SOURCE_IMAGE = gradio.Image(
		value = SOURCE_FILE.value['name'] if are_source_images else None,
		visible = are_source_images,
		show_label = False
	)
	register_ui_component('source_image', SOURCE_IMAGE)
	arquivos = [f for f in os.listdir('/kaggle/working/facenico6/exemplos') if os.path.isfile(os.path.join('/kaggle/working/facenico6/exemplos', f))]
	files = []
	for x in arquivos:
		files.append('/kaggle/working/facenico6/exemplos/' + x)

	examples = gradio.Examples(sorted(files), SOURCE_FILE, examples_per_page=20)


def listen() -> None:
	SOURCE_FILE.change(update, inputs = SOURCE_FILE, outputs = SOURCE_IMAGE)


def update(file: IO[Any]) -> gradio.Image:
	if file and are_images(file.name):
		facefusion.globals.source_path = file.name
		return gradio.Image(value = file.name, visible = True)
	facefusion.globals.source_path = None
	return gradio.Image(value = None, visible = False)
