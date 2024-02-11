from typing import Optional, List
import gradio
import os
import facefusion.globals
from facefusion import wording
from facefusion.uis.typing import File
from facefusion.filesystem import are_images
from facefusion.uis.core import register_ui_component


SOURCE_IMAGE : Optional[gradio.Image] = None


def render() -> None:
	global SOURCE_IMAGE

	SOURCE_IMAGE = gradio.Image(
		visible = True,
	)
	register_ui_component('source_image', SOURCE_IMAGE)
	arquivos = [f for f in os.listdir('/kaggle/working/facenico6/exemplos') if os.path.isfile(os.path.join('/kaggle/working/facenico6/exemplos', f))]
	files = []
	for x in arquivos:
		files.append('/kaggle/working/facenico6/exemplos/' + x)

	examples = gradio.Examples(sorted(files), SOURCE_IMAGEour, examples_per_page=20)


def listen() -> None:
	SOURCE_IMAGE.change(update, inputs = SOURCE_IMAGE, outputs = SOURCE_IMAGE)


def update() -> gradio.Image:
	facefusion.globals.source_paths = [SOURCE_IMAGE.value]
	print(SOURCE_IMAGE.value)
	return SOURCE_IMAGE
