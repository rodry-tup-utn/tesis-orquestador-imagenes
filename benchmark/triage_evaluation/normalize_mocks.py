"""Normaliza las 50 órdenes de los mocks a un formato uniforme para evaluación."""
import csv
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOCKS_DIR = os.path.join(REPO_ROOT, "mocks")

MODALITY_MAP = {
    "Tomografia": "CT",
    "Ecografia": "US",
    "Radiologia": "DX",
    "CR": "DX",
    "CT": "CT",
    "MR": "MR",
    "US": "US",
    "DX": "DX",
    "MG": "MG",
    "XA": "XA",
    "NM": "NM",
    "PT": "PT",
}

PROCEDURE_MODALITY = {
    "Resonancia Magnetica": "MR",
    "Resonancia": "MR",
    "Tomografia": "CT",
    "Ecografia": "US",
    "Radiografia": "DX",
    "Rx": "DX",
    "Ecocardiograma": "US",
    "Doppler": "US",
    "Angiotomografia": "CT",
    "Urotomografia": "CT",
}


def extract_modality_from_procedure(procedure: str) -> str:
    for keyword, mod in PROCEDURE_MODALITY.items():
        if keyword.lower() in procedure.lower():
            return mod
    return "DX"


def normalize_guardia(data: list) -> list[dict]:
    orders = []
    for item in data:
        mod_raw = item.get("modalidad", "")
        modality = MODALITY_MAP.get(mod_raw, mod_raw)
        orders.append({
            "order_id": item["id_transaccion"],
            "modality": modality,
            "diagnosis": item["diagnostico"],
            "origin_service": "Guardia",
            "patient_location": item.get("ubicacion_actual", ""),
            "is_urgent": item.get("urgente", "NO") == "SI",
        })
    return orders


def normalize_internacion(data: list) -> list[dict]:
    orders = []
    for item in data:
        co = item.get("clinical_order", {})
        mod_raw = co.get("modality", "")
        modality = MODALITY_MAP.get(mod_raw, mod_raw)
        orders.append({
            "order_id": item["request_id"],
            "modality": modality,
            "diagnosis": co.get("diagnosis", ""),
            "origin_service": "Internacion",
            "patient_location": co.get("sector", ""),
            "is_urgent": item.get("is_urgent", False),
        })
    return orders


def normalize_ambulatorio(data: list) -> list[dict]:
    orders = []
    for item in data:
        procedure = item.get("PRESTACION_DESC", "")
        modality = extract_modality_from_procedure(procedure)
        orders.append({
            "order_id": item["ID_CITA"],
            "modality": modality,
            "diagnosis": item.get("DIAGNOSTICO", ""),
            "origin_service": "Ambulatorio",
            "patient_location": "",
            "is_urgent": False,
        })
    return orders


def main():
    all_orders = []

    with open(os.path.join(MOCKS_DIR, "guardia.json"), encoding="utf-8") as f:
        all_orders.extend(normalize_guardia(json.load(f)))

    with open(os.path.join(MOCKS_DIR, "internacion.json"), encoding="utf-8") as f:
        all_orders.extend(normalize_internacion(json.load(f)))

    with open(os.path.join(MOCKS_DIR, "ambulatorio.json"), encoding="utf-8") as f:
        all_orders.extend(normalize_ambulatorio(json.load(f)))

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orders_for_evaluation.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["order_id", "modality", "diagnosis", "origin_service", "patient_location", "is_urgent"])
        writer.writeheader()
        writer.writerows(all_orders)

    print(f"Total órdenes normalizadas: {len(all_orders)}")
    print(f"Guardia: {sum(1 for o in all_orders if o['origin_service'] == 'Guardia')}")
    print(f"Internacion: {sum(1 for o in all_orders if o['origin_service'] == 'Internacion')}")
    print(f"Ambulatorio: {sum(1 for o in all_orders if o['origin_service'] == 'Ambulatorio')}")
    print(f"Guardado en: {output_path}")


if __name__ == "__main__":
    main()
