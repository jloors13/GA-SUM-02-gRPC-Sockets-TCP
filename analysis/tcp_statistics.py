
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "data" / "tcp_latency.csv"
OUTPUT_FILE = ROOT / "data" / "tcp_statistics.csv"
GRAPH_DIRECTORY = ROOT / "analysis" / "figures"

REQUIRED_COLUMNS = [
    "mechanism",
    "message_size",
    "message_bytes",
    "repetition",
    "sample",
    "latency_ms",
    "run_duration_s",
    "throughput_msg_s",
    "timestamp"
]

NUMERIC_COLUMNS = [
    "message_bytes",
    "repetition",
    "sample",
    "latency_ms",
    "run_duration_s",
    "throughput_msg_s"
]


def load_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"No se encontro el archivo: {INPUT_FILE}"
        )

    data = pd.read_csv(INPUT_FILE)

    if data.empty:
        raise ValueError("El archivo CSV no contiene registros")

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Faltan columnas obligatorias: {missing}"
        )

    for column in ["mechanism", "message_size"]:
        data[column] = data[column].astype("string").str.strip()

        if data[column].isna().any() or data[column].eq("").any():
            raise ValueError(
                f"Existen valores vacios en {column}"
            )

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    if not np.isfinite(data[NUMERIC_COLUMNS].to_numpy()).all():
        raise ValueError(
            "Existen valores numericos vacios o invalidos"
        )

    if (data["latency_ms"] <= 0).any():
        raise ValueError("Las latencias deben ser positivas")

    if (data["throughput_msg_s"] <= 0).any():
        raise ValueError("El throughput debe ser positivo")

    if (data["run_duration_s"] <= 0).any():
        raise ValueError("La duracion debe ser positiva")

    if (data["message_bytes"] <= 0).any():
        raise ValueError("El tamaño del mensaje debe ser positivo")

    if (data["repetition"] <= 0).any() or (data["sample"] <= 0).any():
        raise ValueError("Las repeticiones y muestras deben ser positivas")

    sizes = data.groupby(
        ["mechanism", "message_size"]
    )["message_bytes"].nunique()

    if (sizes != 1).any():
        raise ValueError(
            "Un mismo tamaño de mensaje tiene diferentes cantidades de bytes"
        )

    return data


def calculate_statistics(data):
    results = []

    groups = data.groupby(
        ["mechanism", "message_size"],
        sort=True
    )

    for (mechanism, message_size), group in groups:
        latency = group["latency_ms"]

        results.append({
            "mechanism": mechanism,
            "message_size": message_size,
            "message_bytes": int(group["message_bytes"].iloc[0]),
            "samples": len(group),
            "mean_ms": latency.mean(),
            "median_ms": latency.median(),
            "minimum_ms": latency.min(),
            "maximum_ms": latency.max(),
            "std_ms": latency.std(),
            "p95_ms": latency.quantile(0.95),
            "mean_throughput_msg_s":
                group["throughput_msg_s"].mean()
        })

    return pd.DataFrame(results)


def export_statistics(statistics):
    statistics.to_csv(
        OUTPUT_FILE,
        index=False,
        float_format="%.6f",
        encoding="utf-8"
    )

    print(f"Estadisticas guardadas en: {OUTPUT_FILE}")


def generate_graphs(data, statistics):
    GRAPH_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.figure(figsize=(9, 5))

    labels = (
        statistics["mechanism"] + " - " +
        statistics["message_size"]
    )

    plt.bar(labels, statistics["mean_ms"])

    plt.title("Latencia media por mecanismo y tamaño de mensaje")
    plt.xlabel("Mecanismo y tamaño del mensaje")
    plt.ylabel("Latencia media (ms)")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        GRAPH_DIRECTORY / "tcp_latency_comparison.png",
        dpi=300
    )

    plt.close()

    plt.figure(figsize=(9, 5))

    for (mechanism, name), group in data.groupby(
        ["mechanism", "message_size"]
    ):
        plt.hist(
            group["latency_ms"],
            bins=30,
            alpha=0.5,
            label=f"{mechanism} - {name}"
        )

    plt.title("Distribución de latencias")
    plt.xlabel("Latencia (ms)")
    plt.ylabel("Frecuencia")
    plt.legend(title="Mecanismo y mensaje")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        GRAPH_DIRECTORY / "tcp_latency_distribution.png",
        dpi=300
    )

    plt.close()

    print("Graficos generados correctamente")


def main():
    print("Iniciando analisis estadistico")

    data = load_data()

    statistics = calculate_statistics(data)

    print("\nResultados estadisticos:")
    print(statistics.to_string(index=False))

    export_statistics(statistics)

    generate_graphs(data, statistics)

    print("\nAnalisis finalizado correctamente")


if __name__ == "__main__":
    main()
