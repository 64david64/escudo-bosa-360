
import argparse
import json
import time
from pathlib import Path

from core.agent import analyze_evidence
from core.risk import evaluate_risk


def clasificar(resultado):
    nivel = resultado["risk_level"]

    if nivel in ("ALTO", "MEDIO"):
        return "alerta"
    if nivel == "BAJO":
        return "bajo"

    return "abstencion"


def evaluar(start=0, limit=5):
    ruta = Path("data/test_cases_25.json")
    casos = json.loads(ruta.read_text(encoding="utf-8"))

    seleccionados = casos[start:start + limit]
    resultados = []

    for caso in seleccionados:
        print(f"\nAnalizando {caso['id']}...")

        inicio = time.perf_counter()

        try:
            analisis = analyze_evidence(
                text=caso["text"],
                db_matches=None
            )

            resultado = evaluate_risk(
                ai_result=analisis,
                db_matches=None
            )

            duracion = round(
                time.perf_counter() - inicio, 2
            )

            registro = {
                "id": caso["id"],
                "expected": caso["expected"],
                "ai_risk": analisis["risk_level"],
                "final_risk": resultado["risk_level"],
                "decision": clasificar(resultado),
                "seconds": duracion,
                "indicators": analisis["indicators"]
            }

            resultados.append(registro)

            print(
                f"IA: {registro['ai_risk']} | "
                f"Final: {registro['final_risk']} | "
                f"Tiempo: {duracion}s"
            )

        except Exception as error:
            print(
                f"Error en {caso['id']}: "
                f"{type(error).__name__}"
            )

            if "429" in str(error) or "503" in str(error):
                print("Servicio saturado o cuota alcanzada.")
                break

        time.sleep(2)

    salida = Path(
        f"data/resultados_ia_{start}_{start + limit}.json"
    )

    salida.write_text(
        json.dumps(
            resultados,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    fraudes = [
        r for r in resultados
        if r["expected"] == "fraude"
    ]
    normales = [
        r for r in resultados
        if r["expected"] == "sin_indicios"
    ]
    ambiguos = [
        r for r in resultados
        if r["expected"] == "ambiguo"
    ]

    tp = sum(r["decision"] == "alerta" for r in fraudes)
    fp = sum(r["decision"] == "alerta" for r in normales)

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / len(fraudes) if fraudes else None
    tasa_alertas_incorrectas = (
        fp / len(normales) if normales else None
    )

    abstenciones = sum(
        r["decision"] == "abstencion"
        for r in resultados
    )

    print("\n=== RESULTADOS ===")
    print("Casos procesados:", len(resultados))
    print("Alertas correctas:", tp)
    print("Alertas sobre mensajes sin indicios:", fp)
    print("Abstenciones:", abstenciones)
    print("Casos ambiguos evaluados:", len(ambiguos))

    if precision is not None:
        print(f"Precisión de alertas: {precision:.2%}")

    if recall is not None:
        print(f"Recall de fraudes: {recall:.2%}")

    if tasa_alertas_incorrectas is not None:
        print(
            "Tasa de alertas sobre mensajes sin indicios: "
            f"{tasa_alertas_incorrectas:.2%}"
        )

    print("Resultados guardados en:", salida)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()
    evaluar(args.start, args.limit)
