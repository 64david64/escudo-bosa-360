
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median

from core.risk import evaluate_risk


ARCHIVOS = [
    "resultados_ia_0_3.json",
    "resultados_ia_3_10.json",
    "resultados_ia_10_15.json",
    "resultados_ia_15_20.json",
    "resultados_ia_20_25.json",
]

CARPETA = Path("data")
NIVELES = [
    "ALTO",
    "MEDIO",
    "BAJO",
    "EVIDENCIA_INSUFICIENTE"
]

resultados = []

# 1. Leer las evaluaciones ya guardadas
for nombre in ARCHIVOS:
    ruta = CARPETA / nombre

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta}"
        )

    casos = json.loads(
        ruta.read_text(encoding="utf-8")
    )

    resultados.extend(casos)

# 2. Verificar que estén los 25 casos
ids_esperados = (
    {f"F{i:02d}" for i in range(1, 11)}
    | {f"N{i:02d}" for i in range(1, 11)}
    | {f"A{i:02d}" for i in range(1, 6)}
)

ids_obtenidos = [caso["id"] for caso in resultados]

if (
    len(ids_obtenidos) != 25
    or set(ids_obtenidos) != ids_esperados
):
    raise ValueError(
        "Faltan casos o existen registros duplicados."
    )

consolidado = []

# 3. Recalcular el riesgo sin llamar a Gemini
for caso in resultados:
    ai_result = {
        "risk_level": caso["ai_risk"],
        "indicators": caso.get("indicators", []),
        "explanation": ""
    }

    evaluacion = evaluate_risk(
        ai_result=ai_result,
        db_matches=None
    )

    consolidado.append({
        "id": caso["id"],
        "expected": caso["expected"],
        "ai_risk": caso["ai_risk"],
        "previous_final_risk": caso["final_risk"],
        "final_risk": evaluacion["risk_level"],
        "verification_status": (
            evaluacion["verification_status"]
        ),
        "seconds": caso["seconds"]
    })

# 4. Mostrar resultados por grupo
print("\n=== ESCUDO BOSA 360 ===")
print("CONSOLIDADO DE 25 CASOS\n")

for grupo in ["fraude", "sin_indicios", "ambiguo"]:
    registros = [
        r for r in consolidado
        if r["expected"] == grupo
    ]

    conteo = Counter(
        r["final_risk"] for r in registros
    )

    print(f"\nGRUPO: {grupo.upper()}")
    print("Casos:", len(registros))

    for nivel in NIVELES:
        print(f"  {nivel}: {conteo[nivel]}")

# 5. Métricas sobre casos etiquetados
fraudes = [
    r for r in consolidado
    if r["expected"] == "fraude"
]

sin_indicios = [
    r for r in consolidado
    if r["expected"] == "sin_indicios"
]

niveles_alerta = {"ALTO", "MEDIO"}

tp = sum(
    r["final_risk"] in niveles_alerta
    for r in fraudes
)

fp = sum(
    r["final_risk"] in niveles_alerta
    for r in sin_indicios
)

abstenciones = sum(
    r["final_risk"] == "EVIDENCIA_INSUFICIENTE"
    for r in consolidado
)

precision = tp / (tp + fp) if tp + fp else None
recall = tp / len(fraudes) if fraudes else None

tiempos = [r["seconds"] for r in consolidado]

print("\n=== MÉTRICAS EXPLORATORIAS ===")
print("Fraudes con alerta:", f"{tp}/{len(fraudes)}")
print("Alertas sobre mensajes sin indicios:", fp)
print("Abstenciones totales:", abstenciones)

if precision is not None:
    print(f"Precisión de alertas: {precision:.2%}")

if recall is not None:
    print(f"Recall de fraudes: {recall:.2%}")

print(f"Tiempo promedio: {mean(tiempos):.2f} s")
print(f"Tiempo mediano: {median(tiempos):.2f} s")

# 6. Guardar el consolidado actualizado
salida = CARPETA / "resumen_evaluacion_25.json"

salida.write_text(
    json.dumps(
        consolidado,
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print("\nArchivo generado:", salida)
print("Consolidación completada.")
