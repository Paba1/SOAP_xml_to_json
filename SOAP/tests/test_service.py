import pytest
import base64
import json
import os
from zeep import Client

WSDL = "http://127.0.0.1:8000/service?wsdl"


@pytest.fixture(scope="module")
def client():
    """Tworzy klienta SOAP dla testów."""
    return Client(WSDL)


def test_1_list_supported_conversions(client):
    """Sprawdza ListSupportedConversions (README Pkt 8.2)."""
    resp = client.service.ListSupportedConversions()
    data_str = getattr(resp, 'ListSupportedConversionsResult', str(resp))
    data = json.loads(data_str)
    assert any(item['from'] == 'xml' and item['to'] == 'json' for item in data)


def test_2_detect_format(client):
    """Sprawdza DetectFormat (README Pkt 8.4)."""
    content = "<root>Hello</root>"
    b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    resp = client.service.DetectFormat(b64)
    fmt = getattr(resp, 'DetectFormatResult0', None)
    meta_raw = getattr(resp, 'DetectFormatResult1', "{}")
    meta = json.loads(meta_raw)

    assert fmt == 'xml'
    assert "base64_len" in meta  # Weryfikacja metadanych wymaganych w Pkt 2.2


def test_3_convert_xml_to_json(client):
    """Sprawdza ConvertXtoY i strukturę raportu (README Pkt 2.1 & 8.6)."""
    xml_input = "<person><name>Jan</name></person>"
    b64_in = base64.b64encode(xml_input.encode('utf-8')).decode('utf-8')

    resp = client.service.ConvertXtoY("xml", "json", b64_in, None)
    data_out_b64 = getattr(resp, 'ConvertXtoYResult0', None)
    report_raw = getattr(resp, 'ConvertXtoYResult1', None)

    assert data_out_b64 is not None
    report = json.loads(report_raw)

    # WERYFIKACJA ZGODNOŚCI Z README PKT 2.1 i 8.6
    assert "status" in report, "Raport musi zawierać pole 'status'"
    assert "elapsed_ms" in report, "Raport musi zawierać pole 'elapsed_ms'"
    assert "details" in report, "Raport musi zawierać pole 'details'"
    assert report['status'] == 'success'
    assert isinstance(report['elapsed_ms'], (int, float))

    # Weryfikacja treści
    json_text = base64.b64decode(data_out_b64).decode('utf-8')
    parsed = json.loads(json_text)
    assert 'person' in parsed


def test_4_validate_conversion(client):
    """Sprawdza ValidateConversion (README Pkt 2.3 & 8.5)."""
    xml_data = "<note>test</note>"
    json_data = '{"note": "test"}'

    b64_xml = base64.b64encode(xml_data.encode('utf-8')).decode('utf-8')
    b64_json = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')

    resp = client.service.ValidateConversion("xml", "json", b64_xml, b64_json, "{}")
    is_valid = getattr(resp, 'ValidateConversionResult0', False)
    details_raw = getattr(resp, 'ValidateConversionResult1', "{}")
    details = json.loads(details_raw)

    assert is_valid is True
    assert "details" in details or isinstance(details, dict)


def test_5_report_files_exist():
    """Weryfikacja Pkt 7: Czy klient zapisał raporty w folderze reports/."""
    report_dir = "reports"
    assert os.path.exists(report_dir), "Folder reports/ nie istnieje"

    # Sprawdzamy czy są jakiekolwiek pliki .json (wynik Twoich manualnych testów)
    files = [f for f in os.listdir(report_dir) if f.endswith('.json')]
    assert len(files) > 0, "Brak wygenerowanych raportów JSON w folderze reports/"


def test_6_convert_invalid_xml_error(client):
    """Sprawdza czy serwer poprawnie zwraca status 'error' dla błędnego XML."""
    invalid_xml = "To nie jest nawet XML <tag"
    b64_in = base64.b64encode(invalid_xml.encode('utf-8')).decode('utf-8')

    resp = client.service.ConvertXtoY("xml", "json", b64_in, None)
    report_raw = getattr(resp, 'ConvertXtoYResult1', None)

    report = json.loads(report_raw)

    # Weryfikacja czy system wykrył błąd
    assert report['status'] == 'error'
    assert "XML Parsing Error" in report['details']


def test_7_validate_mismatch(client):
    """Testuje czy ValidateConversion wykryje różnicę w danych."""
    xml_data = "<root><val>1</val></root>"
    json_data = '{"root": {"val": "2"}}'  # Inna wartość niż w XML

    b64_xml = base64.b64encode(xml_data.encode('utf-8')).decode('utf-8')
    b64_json = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')

    resp = client.service.ValidateConversion("xml", "json", b64_xml, b64_json, "{}")
    is_valid = getattr(resp, 'ValidateConversionResult0', False)

    assert is_valid is False  # Powinno być False, bo 1 != 2