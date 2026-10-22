
import json

from core.extract import extract_entities
from core.agent import analyze_evidence
from core.risk import evaluate_risk


def main():
    mensaje = (
        "URGENTE: Tu cuenta bancaria fue bloqueada. "
        "Para evitar la suspensión definitiva, "
        "ingresa a https://banco-falso.example/verificar "
        "y confirma tu contraseña."
    )

    print("\n=== ESCUDO BOSA 360 ===")

    # 1. EXTRAER EVIDENCIA
    extracted = extract_entities(text=mensaje)

    print("\n1. EXTRACCIÓN COMPLETADA")
    print(json.dumps(
        extracted,
        indent=2,
        ensure_ascii=False
    ))

    # 2. ANÁLISIS MEDIANTE GEMINI
    print("\n2. CONSULTANDO GEMINI...")

    ai_result = analyze_evidence(
        text=mensaje,
        db_matches=None,
        extracted=extracted
    )

    print("\nRESULTADO DE INTELIGENCIA ARTIFICIAL:")
    print(json.dumps(
        ai_result,
        indent=2,
        ensure_ascii=False
    ))

    # 3. EVALUACIÓN FINAL DEL RIESGO
    final_result = evaluate_risk(
        ai_result=ai_result,
        db_matches=None
    )

    print("\n3. EVALUACIÓN FINAL:")

    print("Riesgo de IA:",
          final_result["ai_risk_level"])

    print("Riesgo final:",
          final_result["risk_level"])

    print("Verificación:",
          final_result["verification_status"])

    print("\nJUSTIFICACIÓN:")
    print(final_result["risk_justification"])

    print("\nRECOMENDACIONES:")
    for i, recommendation in enumerate(
        final_result["recommendations"], start=1
    ):
        print(f"{i}. {recommendation}")

    print("\n=== PROCESO COMPLETADO ===")


if __name__ == "__main__":
    main()
