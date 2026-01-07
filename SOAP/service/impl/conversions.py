import xmltodict
import json
import base64
import time


def xml_to_json_logic(xml_base64: str):
    """
    Konwertuje XML (Base64) na JSON (Base64).
    Zwraca krotkę: (data_out_b64, report_dict)
    """
    start_time = time.time()
    try:
        # 1. Dekodowanie
        xml_data = base64.b64decode(xml_base64).decode('utf-8')

        # 2. Parsowanie XML do słownika
        data_dict = xmltodict.parse(xml_data)

        # 3. Zrzut do JSON
        json_str = json.dumps(data_dict, indent=2)
        data_out_b64 = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

        elapsed_ms = int((time.time() - start_time) * 1000)

        # RAPORT ZGODNY Z README (Pkt 7)
        report = {
            "status": "success",
            "elapsed_ms": elapsed_ms,
            "details": f"Successfully converted XML to JSON. Nodes processed: {len(data_dict)}"
        }

        return data_out_b64, report

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        report = {
            "status": "error",
            "elapsed_ms": elapsed_ms,
            "details": f"XML Parsing Error: {str(e)}"
        }
        return None, report


def detect_format_logic(data_base64: str):
    """
    Wykrywa format i zwraca metadane (README Pkt 2.2).
    Zwraca krotkę: (format_name, metadata_dict)
    """
    try:
        raw_bytes = base64.b64decode(data_base64)
        content = raw_bytes.decode('utf-8').strip()

        metadata = {
            "base64_len": len(data_base64),
            "raw_size_bytes": len(raw_bytes)
        }

        if content.startswith('<') and content.endswith('>'):
            return "xml", metadata
        if content.startswith('{') or content.startswith('['):
            return "json", metadata

        return "unknown", metadata
    except Exception:
        return "unknown", {"error": "Could not decode data"}