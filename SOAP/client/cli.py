import argparse
import base64
import json
import sys
import os
import time
from zeep import Client

WSDL_URL = "http://127.0.0.1:8000/service?wsdl"
REPORTS_DIR = "reports"


def get_client():
    """Inicjalizuje klienta SOAP."""
    try:
        return Client(WSDL_URL)
    except Exception as e:
        print(f"BŁĄD: Nie można połączyć z serwerem: {e}")
        sys.exit(1)


def get_next_index(op_name):
    """Generuje kolejny numer pliku dla danej operacji (1, 2, 3...)."""
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    existing = [f for f in os.listdir(REPORTS_DIR)
                if f.startswith(op_name) and not f.startswith("result_")]
    return len(existing) + 1


def save_all_to_reports(op_name, server_response_report, result_content=None):
    """Zapisuje raport JSON zgodnie z wymogami (status, elapsed_ms, details)."""
    idx = get_next_index(op_name)

    final_report = {
        "status": server_response_report.get("status", "unknown"),
        "elapsed_ms": server_response_report.get("elapsed_ms", 0),
        "details": server_response_report.get("details", "Brak dodatkowych szczegółów"),
        "operation": op_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    report_path = os.path.join(REPORTS_DIR, f"{op_name}_{idx}.json")
    with open(report_path, "w", encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    if result_content:
        result_path = os.path.join(REPORTS_DIR, f"result_{op_name}_{idx}.json")
        with open(result_path, "wb") as f:
            f.write(result_content)
        print(f"✅  SUKCES: Wynik zapisano w: {result_path}")

    print(f"[INFO] Raport JSON zapisano w: {report_path}")


def cmd_convert(args):
    client = get_client()
    try:
        with open(args.input, "rb") as f:
            b64_in = base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"❌  BŁĄD: Plik {args.input} nie istnieje.")
        sys.exit(1)

    print(f"🚀 Konwertowanie: {args.src} -> {args.dst} ...")
    response = client.service.ConvertXtoY(args.src, args.dst, b64_in, None)

    data_out_b64 = getattr(response, 'ConvertXtoYResult0', None)
    report_raw = getattr(response, 'ConvertXtoYResult1', None)

    if report_raw:
        service_report = json.loads(report_raw)

        if service_report.get("status") == "error":
            print(f"❌  BŁĄD SERWERA: {service_report.get('details')}")
            save_all_to_reports("convert", service_report, None)
            sys.exit(1)

        decoded_result = base64.b64decode(data_out_b64) if data_out_b64 else None
        save_all_to_reports("convert", service_report, decoded_result)
        print("✨ Konwersja zakończona pomyślnie.")


def cmd_detect(args):
    client = get_client()
    try:
        with open(args.input, "rb") as f:
            b64_in = base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        print("❌  BŁĄD: Brak pliku.")
        sys.exit(1)

    response = client.service.DetectFormat(b64_in)
    fmt = getattr(response, 'DetectFormatResult0', "unknown")
    meta = json.loads(getattr(response, 'DetectFormatResult1', "{}"))

    # Logika sprawdzania czy detekcja faktycznie się udała
    status = "success" if fmt != "unknown" else "error"

    print(f"🔍 Wykryty format: {fmt}")
    if status == "error":
        print("⚠️  Ostrzeżenie: Serwer nie rozpoznał struktury pliku jako XML ani JSON.")

    detect_report = {
        "status": status,
        "elapsed_ms": 0,
        "details": f"Detected format: {fmt}. Metadata: {meta}"
    }
    save_all_to_reports("detect", detect_report)


def cmd_validate(args):
    client = get_client()
    try:
        with open(args.src_file, "rb") as f:
            src_b64 = base64.b64encode(f.read()).decode('utf-8')
        with open(args.dst_file, "rb") as f:
            dst_b64 = base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        print("❌  BŁĄD: Brak plików do walidacji.")
        sys.exit(1)

    response = client.service.ValidateConversion(args.src_fmt, args.dst_fmt, src_b64, dst_b64, "{}")
    is_valid = getattr(response, 'ValidateConversionResult0', False)
    val_details = json.loads(getattr(response, 'ValidateConversionResult1', "{}"))

    status = "success" if is_valid else "error"
    print(f"⚖️  Czy konwersja poprawna? {'✅ TAK' if is_valid else '❌ NIE'}")

    validate_report = {
        "status": status,
        "elapsed_ms": 0,
        "details": val_details
    }
    save_all_to_reports("validate", validate_report)

    if not is_valid:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="SOAP Converter Client")
    subparsers = parser.add_subparsers(dest='command')

    p_conv = subparsers.add_parser('convert')
    p_conv.add_argument('--in', dest='input', required=True)
    p_conv.add_argument('--from', dest='src', required=True)
    p_conv.add_argument('--to', dest='dst', required=True)

    p_det = subparsers.add_parser('detect')
    p_det.add_argument('--in', dest='input', required=True)

    p_val = subparsers.add_parser('validate')
    p_val.add_argument('--src', dest='src_file', required=True)
    p_val.add_argument('--dst', dest='dst_file', required=True)
    p_val.add_argument('--srcfmt', dest='src_fmt', required=True)
    p_val.add_argument('--dstfmt', dest='dst_fmt', required=True)

    args = parser.parse_args()
    if args.command == 'convert':
        cmd_convert(args)
    elif args.command == 'detect':
        cmd_detect(args)
    elif args.command == 'validate':
        cmd_validate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()