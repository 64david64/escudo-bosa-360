
from core.risk import evaluate_risk


def fake_analysis(level="ALTO", indicators=None):
    if indicators is None:
        indicators = ["Solicitud de contraseña"]

    return {
        "risk_level": level,
        "fraud_type": "PHISHING",
        "indicators": indicators,
        "explanation": "Análisis inicial de Gemini",
        "recommendations": [
            "No abrir el enlace.",
            "No compartir contraseñas.",
            "Consultar un canal oficial."
        ]
    }


def test_riesgo_alto_por_indicios():
    result = evaluate_risk(
        fake_analysis("ALTO"), db_matches=[]
    )

    assert result["risk_level"] == "ALTO"
    assert result["verification_status"] == "SIN_COINCIDENCIAS"


def test_coincidencia_simulada():
    matches = [{
        "indicator": "banco-falso.example",
        "match_type": "exact",
        "source_type": "synthetic",
        "indicator_status": "listed_malicious",
        "verified_by_service": False,
        "is_demo": True
    }]

    result = evaluate_risk(
        fake_analysis("BAJO", []), matches
    )

    assert result["risk_level"] == "MEDIO"


def test_coincidencia_externa_respaldada():
    matches = [{
        "indicator": "ejemplo-malicioso.test",
        "match_type": "exact",
        "source_type": "external_reputation",
        "indicator_status": "listed_malicious",
        "verified_by_service": True,
        "is_demo": False
    }]

    result = evaluate_risk(
        fake_analysis("MEDIO"), matches
    )

    assert result["risk_level"] == "ALTO"


def test_verificacion_pendiente():
    result = evaluate_risk(
        fake_analysis("BAJO", []),
        db_matches=None
    )

    assert result["risk_level"] == "BAJO"
    assert result["verification_status"] == "PENDIENTE"


def test_evidencia_insuficiente_real():
    result = evaluate_risk(
        fake_analysis("EVIDENCIA_INSUFICIENTE", []),
        db_matches=None
    )

    assert result["risk_level"] == "EVIDENCIA_INSUFICIENTE"



def test_evidencia_insuficiente_real():
    result = evaluate_risk(
        fake_analysis("EVIDENCIA_INSUFICIENTE", []),
        db_matches=None
    )

    assert result["risk_level"] == "EVIDENCIA_INSUFICIENTE"




def test_riesgo_bajo_no_significa_seguro():
    """
    Verifica que un riesgo BAJO no signifique
    que el mensaje sea seguro.
    """

    result = evaluate_risk(
        fake_analysis("BAJO", []),
        db_matches=[]
    )

    assert result["risk_level"] == "BAJO"

    assert (
        result["verification_status"]
        == "SIN_COINCIDENCIAS"
    )

    justificacion = result["risk_justification"].lower()

    assert "no garantiza" in justificacion
    assert "seguro" in justificacion


def test_ia_sin_indicios():
    result = evaluate_risk(
        fake_analysis("ALTO", []),
        db_matches=[]
    )

    assert result["risk_level"] == "EVIDENCIA_INSUFICIENTE"
