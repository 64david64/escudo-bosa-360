
from pathlib import Path
from core.extract import extract_entities

ruta = Path("data/captura_prueba.png")

if not ruta.exists():
    raise FileNotFoundError(
        "No se encontró data/captura_prueba.png"
    )

print("Enviando imagen a Gemini...")

resultado = extract_entities(
    image_bytes=ruta.read_bytes()
)

print("\nTEXTO DETECTADO:")
print(resultado["extracted_text"])

print("\nENLACES:")
print(resultado["urls"])

print("\nDOMINIOS:")
print(resultado["domains"])

print("\nTELÉFONOS:")
print(resultado["phones"])
