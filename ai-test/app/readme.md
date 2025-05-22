# Main Application Overview

## What Does `main.py` Do?

The `main.py` file is the core execution script for the AI pipeline. It orchestrates the following workflow:

1. **Receives a user prompt** via the Openfabric SDK.
2. **Expands the prompt** using a locally hosted LLM (Ollama, running DeepSeek or Llama models).
3. **Generates an image** from the expanded prompt using a Text-to-Image Openfabric app.
4. **Converts the image to a 3D model** using an Image-to-3D Openfabric app.
5. **Stores results in memory** for both short-term (session) and long-term (persistent) recall.
6. **Responds to the user** with a message and generated assets.

---

## Memory Management

### Short-Term Memory (Session Memory)
- Stored in the `model.state.session_memory` attribute.
- Keeps track of all prompts and generated assets within the current session.
- Not persisted to disk; only available during the active session.
- Example entry:
  ```json
  {
    "prompt": "original user prompt",
    "expanded_prompt": "expanded version",
    "image_file": "path/to/image.png",
    "model_file": "path/to/model.glb"
  }
  ```

### Long-Term Memory
- Persisted in `datastore/long_term_memory.json` as a flat file.
- Each entry includes all session memory fields **plus** a `created_at` timestamp (ISO format) for traceability.
- Survives application restarts and can be used for future recall or reference.
- Example entry:
  ```json
  {
    "prompt": "original user prompt",
    "expanded_prompt": "expanded version",
    "image_file": "datastore/generatedImages/output_image_20250522_153557.png",
    "model_file": "datastore/generatedImages/output_model_20250522_153557.glb",
    "created_at": "2025-05-22T15:35:57"
  }
  ```

---

## Model Usage
- **Prompt Expansion**: Uses a local Ollama server to run LLMs (DeepSeek or Llama) for creative prompt expansion.
- **Text-to-Image**: Calls an Openfabric app to generate images from the expanded prompt.
- **Image-to-3D**: Calls another Openfabric app to convert the image into a 3D model.

All model calls are handled via the Openfabric SDK's `Stub` class, and the results are saved for both immediate and future use.

---

## Local Ollama Integration
- The application communicates with a local Ollama server (`http://localhost:11434/api/generate`) to expand user prompts.
- No external LLM APIs are used; all inference is performed locally for privacy and speed.
- The model used for expansion can be configured (default: `deepseek-r1:7b`).

---

## File Structure Highlights
- `main.py`: Main execution logic and memory management.
- `datastore/long_term_memory.json`: Persistent memory store.
- `datastore/generatedImages/`: Stores all generated images and 3D models.
- `core/stub.py`: Handles Openfabric app calls.
- `ontology_dc8f06af066e4a7880a5938933236037/`: Contains schema and data classes for input/output/config.

---

## How It All Connects
1. **User prompt** → expanded by local LLM (Ollama)
2. **Expanded prompt** → image generated (Text-to-Image app)
3. **Image** → 3D model generated (Image-to-3D app)
4. **Session memory** updated for current run
5. **Long-term memory** updated for persistent recall

---

## Customization & Extensibility
- You can swap out the LLM model by changing the `model` parameter in `expand_prompt_with_ollama`.
- The memory system can be extended to use databases or vector stores for advanced recall.
- All Openfabric app IDs and endpoints are configurable.

---

## Requirements
- Python 3.8+
- Local Ollama server running (see [Ollama documentation](https://ollama.com/))
- Openfabric SDK and dependencies (see `pyproject.toml`)

---

## Running the App
- Start the Ollama server locally.
- Run the app using `start.sh` or via Docker (`Dockerfile` provided).
- Interact via the Openfabric API (Swagger UI available at `/swagger-ui/#/App/post_execution`).

---

## Contact
For questions or improvements, open an issue or contact the maintainer. 