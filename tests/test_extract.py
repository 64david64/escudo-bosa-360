
import pytest

from core.extract import extract_entities


def test_extraer_urls():
    """Verifica que se detecten enlaces y dominios."""

    mensaje = (
        "Urgente, ingresa a "
        "https://subsidio-bosa.example/verificar "
        "para reclamar tu beneficio."
    )

    resultado = extract_entities(text=mensaje)

    assert (
        "https://subsidio-bosa.example/verificar"
        in resultado["urls"]
    )

    assert "subsidio-bosa.example" in resultado["domains"]


def test_extraer_telefono():
    """Verifica la extracción de celulares colombianos."""

    mensaje = (
        "Comunícate al +57 300 123 4567 "
        "para reclamar el premio."
    )

    resultado = extract_entities(text=mensaje)

    assert "3001234567" in resultado["phones"]


def test_mensaje_sin_indicadores():
    """Verifica mensajes que no contienen enlaces ni teléfonos."""

    mensaje = "Buenos días, nos vemos mañana."

    resultado = extract_entities(text=mensaje)

    assert resultado["urls"] == []
    assert resultado["phones"] == []
    assert resultado["domains"] == []


def test_estructura_resultado():
    """Verifica que la función devuelva los campos esperados."""

    resultado = extract_entities(
        text="Mensaje de prueba"
    )

    assert isinstance(resultado, dict)

    assert "extracted_text" in resultado
    assert "urls" in resultado
    assert "domains" in resultado
    assert "phones" in resultado


def test_campos_son_listas():
    """Verifica los tipos de datos para PostgreSQL y Streamlit."""

    resultado = extract_entities(
        text="Prueba de extracción"
    )

    assert isinstance(resultado["urls"], list)
    assert isinstance(resultado["domains"], list)
    assert isinstance(resultado["phones"], list)
    assert isinstance(resultado["extracted_text"], str)
