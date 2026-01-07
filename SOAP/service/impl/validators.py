import json
import base64
import xmltodict


def validate_xml_json(xml_b64: str, json_b64: str) -> bool:
    """
    Sprawdza spójność danych między źródłem XML a wynikiem JSON.
    Wymagane przez operację ValidateConversion.
    """
    try:
        # Dekodowanie
        xml_content = base64.b64decode(xml_b64).decode('utf-8')
        json_content = base64.b64decode(json_b64).decode('utf-8')

        # Sprowadzenie obu formatów do wspólnego mianownika (Python Dict)
        obj_from_xml = xmltodict.parse(xml_content)
        obj_from_json = json.loads(json_content)

        # Porównanie struktur
        return obj_from_xml == obj_from_json
    except Exception:
        return False