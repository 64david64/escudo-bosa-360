
import json
from core.agent import analyze_evidence

mensaje = (
    "URGENTE: su cuenta ha sido bloqueada. "
    "Ingrese a https://banco-falso.example/verificar "
    "y confirme su contraseña."
)

print("Analizando posible fraude...")

resultado = analyze_evidence(
    text=mensaje,
    db_matches=None
)

print(json.dumps(
    resultado,
    indent=2,
    ensure_ascii=False
))
