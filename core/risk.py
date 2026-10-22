
from typing import Any


# =====================================================
# ESCUDO BOSA 360
# MOTOR DE EVALUACION DE RIESGO DIGITAL
# =====================================================

VALID_LEVELS = {
    "ALTO",
    "MEDIO",
    "BAJO",
    "EVIDENCIA_INSUFICIENTE",
}


def evaluate_risk(
    ai_result: dict[str, Any],
    db_matches: list[dict] | None = None
) -> dict[str, Any]:
    """
    Combina el analisis de Gemini con las coincidencias
    obtenidas mediante PostgreSQL o fuentes externas.

    IMPORTANTE:
    El nivel de riesgo y el estado de verificacion
    son dos dimensiones independientes.

    Parametros
    ----------
    ai_result:
        Diccionario generado por core/agent.py.

    db_matches:
        None: no se ha ejecutado la verificacion.
        []: consulta realizada sin coincidencias.
        Lista: coincidencias encontradas.

    Retorna
    -------
    dict:
        Resultado estructurado con:
        - risk_level
        - ai_risk_level
        - verification_status
        - risk_reasons
        - risk_justification
        - risk_method
        - explanation
        - recommendations
    """

    # -------------------------------------------------
    # 1. VALIDACION DE ENTRADAS
    # -------------------------------------------------

    if not isinstance(ai_result, dict):
        raise TypeError(
            "ai_result debe ser un diccionario."
        )

    if db_matches is not None:
        if not isinstance(db_matches, list):
            raise TypeError(
                "db_matches debe ser una lista o None."
            )

    # -------------------------------------------------
    # 2. OBTENER LA CLASIFICACION DE GEMINI
    # -------------------------------------------------

    model_level = str(
        ai_result.get(
            "risk_level",
            "EVIDENCIA_INSUFICIENTE"
        )
    ).upper()

    if model_level not in VALID_LEVELS:
        raise ValueError(
            f"Nivel de riesgo no valido: {model_level}"
        )

    # -------------------------------------------------
    # 3. VALIDAR LOS INDICADORES
    # -------------------------------------------------

    raw_indicators = ai_result.get(
        "indicators",
        []
    )

    if isinstance(raw_indicators, list):
        indicators = [
            indicator.strip()
            for indicator in raw_indicators
            if isinstance(indicator, str)
            and indicator.strip()
        ]
    else:
        indicators = []

    # -------------------------------------------------
    # 4. INICIALIZAR LA EVALUACION
    # -------------------------------------------------

    final_level = model_level
    reasons = []

    # -------------------------------------------------
    # 5. DETERMINAR EL ESTADO DE VERIFICACION
    # -------------------------------------------------

    if db_matches is None:
        verification_status = "PENDIENTE"

    elif len(db_matches) == 0:
        verification_status = "SIN_COINCIDENCIAS"

    else:
        verification_status = "CON_COINCIDENCIAS"

    # -------------------------------------------------
    # 6. IDENTIFICAR COINCIDENCIAS
    # -------------------------------------------------

    # Se consideran únicamente indicadores reportados
    # como maliciosos. Una coincidencia con un dato
    # conocido como benigno no debe elevar el riesgo.

    exact_matches = [
        match
        for match in (db_matches or [])
        if isinstance(match, dict)
        and match.get("match_type") == "exact"
        and match.get("indicator_status")
        == "listed_malicious"
    ]

    # Coincidencias respaldadas por una consulta real
    # a un servicio externo de reputacion.

    external_matches = [
        match
        for match in exact_matches
        if match.get("source_type")
        == "external_reputation"
        and match.get("verified_by_service") is True
        and match.get("is_demo") is False
    ]

    # -------------------------------------------------
    # 7. VALIDAR LA JUSTIFICACION DE LA IA
    # -------------------------------------------------

    if (
        model_level in {"ALTO", "MEDIO"}
        and not indicators
    ):
        final_level = "EVIDENCIA_INSUFICIENTE"

        reasons.append(
            "La inteligencia artificial no proporciono "
            "indicios concretos que justifiquen "
            "su clasificacion inicial."
        )

    # -------------------------------------------------
    # 8. INCORPORAR VERIFICACIONES
    # -------------------------------------------------

    if external_matches:

        final_level = "ALTO"

        reasons.append(
            "Se encontro una coincidencia exacta "
            "con un indicador malicioso reportado "
            "por un servicio externo de reputacion. "
            "Esto no confirma por si solo la totalidad "
            "del incidente."
        )

    elif exact_matches:

        if final_level in {
            "BAJO",
            "EVIDENCIA_INSUFICIENTE"
        }:
            final_level = "MEDIO"

        reasons.append(
            "Se encontro una coincidencia exacta "
            "en registros locales o comunitarios. "
            "Su origen debe verificarse antes de "
            "considerarla una confirmacion de fraude."
        )

    # -------------------------------------------------
    # 9. JUSTIFICAR LA EVALUACION DE GEMINI
    # -------------------------------------------------

    if model_level == "ALTO" and indicators:

        reasons.append(
            "La inteligencia artificial identifico "
            "senales importantes de posible fraude "
            "en la evidencia analizada."
        )

    elif model_level == "MEDIO" and indicators:

        reasons.append(
            "La evidencia presenta indicios de riesgo "
            "que requieren precaucion y verificacion."
        )

    elif model_level == "BAJO":

        reasons.append(
            "Se identificaron pocos indicios de "
            "posible fraude en la evidencia examinada."
        )

    elif (
        model_level == "EVIDENCIA_INSUFICIENTE"
        and not exact_matches
    ):

        reasons.append(
            "La informacion disponible no permite "
            "determinar razonablemente el nivel "
            "de riesgo del mensaje."
        )

    # -------------------------------------------------
    # 10. CORRECCION: RIESGO BAJO
    # -------------------------------------------------

    # Un riesgo BAJO no debe transformarse
    # automaticamente en EVIDENCIA_INSUFICIENTE
    # cuando la verificacion esta pendiente.

    if final_level == "BAJO":

        reasons.append(
            "El riesgo bajo significa que se observaron "
            "pocos indicios sospechosos. No demuestra "
            "que el mensaje sea autentico ni seguro."
        )

    # -------------------------------------------------
    # 11. ACLARAR EL ESTADO DE VERIFICACION
    # -------------------------------------------------

    if verification_status == "PENDIENTE":

        reasons.append(
            "No se ha realizado una verificacion "
            "contra fuentes externas."
        )

    elif verification_status == "SIN_COINCIDENCIAS":

        reasons.append(
            "No se encontraron coincidencias en "
            "las fuentes consultadas. Esto no "
            "garantiza que el contenido sea seguro."
        )

    elif verification_status == "CON_COINCIDENCIAS":

        reasons.append(
            "Se encontraron registros coincidentes. "
            "Las coincidencias deben interpretarse "
            "segun su fuente y confiabilidad."
        )

    # -------------------------------------------------
    # 12. CONSTRUIR EL RESULTADO FINAL
    # -------------------------------------------------

    result = ai_result.copy()

    # Clasificacion original del modelo
    result["ai_risk_level"] = model_level

    # Clasificacion final del motor
    result["risk_level"] = final_level

    # Estado independiente de verificacion
    result["verification_status"] = (
        verification_status
    )

    # Indicadores normalizados
    result["indicators"] = indicators

    # Razones de la decision final
    result["risk_reasons"] = reasons

    result["risk_justification"] = " ".join(
        reasons
    )

    # Metodo de evaluacion
    result["risk_method"] = (
        "HEURISTICO_NO_CALIBRADO"
    )

    # Conservar la explicacion de Gemini
    result["ai_explanation"] = (
        ai_result.get("explanation", "")
    )

    # Explicacion final del sistema
    result["explanation"] = (
        result["risk_justification"]
    )

    return result
