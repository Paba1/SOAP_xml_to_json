import sys
import collections

# Fix kompatybilności dla Python 3.10+
if sys.version_info.major >= 3 and sys.version_info.minor >= 10:
    import collections.abc

    collections.MutableSet = collections.abc.MutableSet

try:
    import six

    sys.modules['spyne.util.six'] = six
    sys.modules['spyne.util.six.moves'] = six.moves
except ImportError:
    pass

import time
import json
import logging
from spyne import Application, rpc, ServiceBase, Unicode, Boolean
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server

# Import logiki biznesowej
from impl.conversions import xml_to_json_logic, detect_format_logic
from impl.validators import validate_xml_json

# Logowanie
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SoapConverter")


class ConverterService(ServiceBase):

    @rpc(Unicode, Unicode, Unicode, Unicode, _returns=(Unicode, Unicode))
    def ConvertXtoY(ctx, srcFormat, dstFormat, dataIn, options=None):
        """Operacja 1: Konwersja formatów (Zgodnie z README pkt 2.1)"""
        logger.info(f"REQ: Convert {srcFormat} -> {dstFormat}")

        # Jeśli używasz mojej nowej wersji conversions.py (tej z krotką):
        if srcFormat.lower() == 'xml' and dstFormat.lower() == 'json':
            data_out, report_dict = xml_to_json_logic(dataIn)
            return data_out, json.dumps(report_dict)

        # Obsługa błędnego formatu z zachowaniem struktury raportu z README
        error_report = {
            "status": "error",
            "elapsed_ms": 0,
            "details": f"Unsupported conversion pair: {srcFormat}->{dstFormat}"
        }
        return "", json.dumps(error_report)

    @rpc(Unicode, _returns=(Unicode, Unicode))
    def DetectFormat(ctx, data):
        """Operacja 2: Wykrywanie formatu (Zgodnie z README pkt 2.2)"""
        fmt, metadata = detect_format_logic(data)
        return fmt, json.dumps(metadata)

    @rpc(Unicode, Unicode, Unicode, Unicode, Unicode, _returns=(Boolean, Unicode))
    def ValidateConversion(ctx, srcFormat, dstFormat, dataSrc, dataDst, criteria):
        """Operacja 3: Walidacja konwersji (Zgodnie z README pkt 2.3)"""
        logger.info("REQ: ValidateConversion")
        is_valid = validate_xml_json(dataSrc, dataDst)

        # Details musi być stringiem JSON zgodnie z kontraktem
        details = {
            "check": "structural_equality",
            "src": srcFormat,
            "dst": dstFormat,
            "valid": is_valid
        }
        return is_valid, json.dumps(details)

    @rpc(_returns=Unicode)
    def ListSupportedConversions(ctx):
        """Operacja 4: Lista możliwości"""
        return json.dumps([{"from": "xml", "to": "json"}])


# Konfiguracja aplikacji SOAP
application = Application(
    [ConverterService],
    tns='converter.soap.service',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

if __name__ == '__main__':
    port = 8000
    wsgi_app = WsgiApplication(application)
    server = make_server('127.0.0.1', port, wsgi_app)

    print(f"--- SERWER SOAP START (Python {sys.version.split()[0]}) ---")
    print(f"WSDL: http://127.0.0.1:{port}/service?wsdl")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")