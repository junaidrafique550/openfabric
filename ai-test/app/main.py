import logging
from typing import Dict
import requests
import base64
import json
import os
import time

from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass
from ontology_dc8f06af066e4a7880a5938933236037.input import InputClass
from ontology_dc8f06af066e4a7880a5938933236037.output import OutputClass
from openfabric_pysdk.context import AppModel, State
from core.stub import Stub


configurations: Dict[str, ConfigClass] = dict()

MEMORY_FILE = os.path.join("datastore", "long_term_memory.json")
GENERATED_IMAGES_DIR = os.path.join("datastore", "generatedImages")

os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)


def config(configuration: Dict[str, ConfigClass], state: State) -> None:
    """
    Stores user-specific configuration data.

    Args:
        configuration (Dict[str, ConfigClass]): A mapping of user IDs to configuration objects.
        state (State): The current state of the application (not used in this implementation).
    """
    for uid, conf in configuration.items():
        logging.info(f"Saving new config for user with id:'{uid}'")
        configurations[uid] = conf


def expand_prompt_with_ollama(input_prompt, model="deepseek-r1:7b"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": f"Interpret and expand this prompt for visual generation: {input_prompt}",
            "stream": False
        }
    )
    return response.json()["response"]

def execute(model: AppModel) -> None:
    print("Type of model:", type(model))
    print("Type of model.state:", type(model.state))
    print("Attributes of model.state:", dir(model.state))

    request: InputClass = model.request


    user_config: ConfigClass = configurations.get('super-user', None)
    logging.info(f"{configurations}")

    app_ids = user_config.app_ids if user_config else []
    stub = Stub(app_ids)

    expanded_prompt = expand_prompt_with_ollama(request.prompt)
    logging.info(f"Expaned Prompt: {expanded_prompt}")


    text_to_image_app_id = 'c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network'
    text_to_image_result = stub.call(text_to_image_app_id, {'prompt': expanded_prompt}, 'super-user')
    logging.info(f"Text-to-Image result keys: {list(text_to_image_result.keys()) if text_to_image_result else 'None'}")

    image_resource = text_to_image_result.get('result') if text_to_image_result else None
    logging.info(f"Image resource: {str(image_resource)[:100]}")

    if not image_resource:
        response: OutputClass = model.response
        response.message = "Failed to generate image from prompt."
        return


    if isinstance(image_resource, bytes):
        image_b64 = base64.b64encode(image_resource).decode('utf-8')
    else:
        image_b64 = image_resource


    image_to_3d_app_id = 'f0b5f319156c4819b9827000b17e511a.node3.openfabric.network'
    image_to_3d_result = stub.call(image_to_3d_app_id, {'input_image': image_b64}, 'super-user')
    logging.info(f"Image-to-3D result keys: {list(image_to_3d_result.keys()) if image_to_3d_result else 'None'}")

    model3d = image_to_3d_result.get('generated_object') if image_to_3d_result else None

    if model3d:
        logging.info(f"3D model: {str(model3d)[:100]}")

    if not model3d:
        response: OutputClass = model.response
        response.message = "Failed to generate 3D model from image."
        return


    timestamp = time.strftime("%Y%m%d_%H%M%S")

    if isinstance(image_resource, bytes):
        image_path = os.path.join(GENERATED_IMAGES_DIR, f"output_image_{timestamp}.png")
        with open(image_path, "wb") as f:
            f.write(image_resource)
    else:
        image_path = os.path.join(GENERATED_IMAGES_DIR, f"output_image_{timestamp}.png")


    if model3d and isinstance(model3d, bytes):
        model_path = os.path.join(GENERATED_IMAGES_DIR, f"output_model_{timestamp}.glb")
        with open(model_path, "wb") as f:
            f.write(model3d)
    else:
        model_path = os.path.join(GENERATED_IMAGES_DIR, f"output_model_{timestamp}.glb")


    session_memory = getattr(model.state, 'session_memory', [])
    session_memory.append({
        'prompt': request.prompt,
        'expanded_prompt': expanded_prompt,
        'image_file': image_path,
        'model_file': model_path
    })

    setattr(model.state, 'session_memory', session_memory)

    long_term_memory = load_long_term_memory()
    long_term_memory.append({
        'prompt': request.prompt,
        'expanded_prompt': expanded_prompt,
        'image_file': image_path,
        'model_file': model_path,
        'created_at': time.strftime("%Y-%m-%dT%H:%M:%S")
    })
    save_long_term_memory(long_term_memory)

    response: OutputClass = model.response
    response.message = f"Prompt expanded: {expanded_prompt}\nImage and 3D model generated successfully."

def load_long_term_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_long_term_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)