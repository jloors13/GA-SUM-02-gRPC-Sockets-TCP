
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# Directorios del proyecto
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIGURES_DIR = ROOT / "analysis" / "figures"

# Archivos de entrada
TCP_LATENCY = DATA_DIR / "tcp_latency.csv"
GRPC_LATENCY = DATA_DIR / "grpc_latency.csv"

TCP_CONCURRENCY = DATA_DIR / "tcp_concurrency.csv"
GRPC_CONCURRENCY = DATA_DIR / "grpc_concurrency.csv"

# Archivos de salida
STATISTICS_OUTPUT = DATA_DIR / "comparative_statistics.csv"
CONCURRENCY_OUTPUT = DATA_DIR / "comparative_concurrency.csv"

CONFIDENCE_Z = 1.96

REQUIRED_LATENCY_COLUMNS = {
    "mechanism",
    "message_size",
    "message_bytes",
    "repetition",
    "sample",
    "latency_ms",
    "run_duration_s",
    "throughput_msg_s",
    "timestamp",
}

REQUIRED_CONCURRENCY_COLUMNS = {
    "sender",
    "destination",
    "latency_ms",
    "response",
    "timestamp",
}


def load_latency_file(path, expected_mechanism):
    """Carga y comprueba los registros de latencia."""

    if not path.is_file():
        raise FileNotFoundError(
            f"No se encontró el archivo: {path}"
        )

    data = pd.read_csv(path)

    if data.empty:
        raise ValueError(f"El archivo está vacío: {path}")

    missing = REQUIRED_LATENCY_COLUMNS - set(data.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas en {path.name}: {sorted(missing)}"
        )

    data["mechanism"] = data["mechanism"].astype(str).str.strip()
    data["message_size"] = (
        data["message_size"].astype(str).str.strip()
    )

    if not data["mechanism"].eq(expected_mechanism).all():
        raise ValueError(
            f"El archivo {path.name} contiene mecanismos inesperados"
        )

    numeric_columns = [
        "message_bytes",
        "repetition",
        "sample",
        "latency_ms",
        "run_duration_s",
        "throughput_msg_s",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    if not np.isfinite(
        data[numeric_columns].to_numpy(dtype=float)
    ).all():
        raise ValueError(
            f"Hay valores numéricos inválidos en {path.name}"
        )

    if (data[numeric_columns] <= 0).any().any():
        raise ValueError(
            f"Hay valores menores o iguales a cero en {path.name}"
        )

    if data["timestamp"].isna().any():
        raise ValueError(
            f"Hay timestamps vacíos en {path.name}"
        )

    return data


def load_concurrency_file(path, expected_routes):
    """Carga y comprueba los resultados de concurrencia."""

    if not path.is_file():
        raise FileNotFoundError(
            f"No se encontró el archivo: {path}"
        )

    data = pd.read_csv(path)

    if data.empty:
        raise ValueError(f"El archivo está vacío: {path}")

    missing = REQUIRED_CONCURRENCY_COLUMNS - set(data.columns)

    if missing:
        raise ValueError(
            f"Faltan columnas en {path.name}: {sorted(missing)}"
        )

    data["latency_ms"] = pd.to_numeric(
        data["latency_ms"], errors="coerce"
    )

    if not np.isfinite(data["latency_ms"]).all():
        raise ValueError(
            f"Latencias inválidas en {path.name}"
        )

    if (data["latency_ms"] <= 0).any():
        raise ValueError(
            f"Latencias no positivas en {path.name}"
        )

    if data["response"].isna().any() or data["response"].eq("").any():
        raise ValueError(
            f"Hay respuestas vacías en {path.name}"
        )

    routes = set(zip(data["sender"], data["destination"]))

    if routes != expected_routes or len(data) != len(expected_routes):
        raise ValueError(
            f"Las rutas de concurrencia no coinciden en {path.name}"
        )

    return data


def calculate_statistics(data):
    """Calcula estadísticas por mecanismo y tamaño."""

    results = []

    for (mechanism, size), group in data.groupby(
        ["mechanism", "message_size"],
        sort=True
    ):
        latency = group["latency_ms"].to_numpy(dtype=float)
        throughput = group["throughput_msg_s"].to_numpy(dtype=float)

        samples = len(latency)
        mean = float(np.mean(latency))
        std = float(np.std(latency, ddof=1))

        margin = CONFIDENCE_Z * std / np.sqrt(samples)

        results.append({
            "mechanism": mechanism,
            "message_size": size,
            "message_bytes": int(group["message_bytes"].iloc[0]),
            "samples": samples,
            "mean_ms": mean,
            "median_ms": float(np.median(latency)),
            "minimum_ms": float(np.min(latency)),
            "maximum_ms": float(np.max(latency)),
            "std_ms": std,
            "p95_ms": float(np.percentile(latency, 95)),
            "mean_throughput_msg_s": float(np.mean(throughput)),
            "ci95_lower_ms": mean - margin,
            "ci95_upper_ms": mean + margin,
        })

    return pd.DataFrame(results)


def compare_mechanisms(statistics):
    """Calcula diferencias entre TCP y gRPC."""

    results = []

    for size in sorted(statistics["message_size"].unique()):
        group = statistics[
            statistics["message_size"] == size
        ]

        tcp = group[group["mechanism"] == "TCP"]
        grpc = group[group["mechanism"] == "gRPC"]

        if len(tcp) != 1 or len(grpc) != 1:
            raise ValueError(
                f"No se encontraron ambos mecanismos para {size}"
            )

        tcp = tcp.iloc[0]
        grpc = grpc.iloc[0]

        difference = tcp["mean_ms"] - grpc["mean_ms"]

        standard_error = np.sqrt(
            tcp["std_ms"] ** 2 / tcp["samples"]
            + grpc["std_ms"] ** 2 / grpc["samples"]
        )

        margin = CONFIDENCE_Z * standard_error

        improvement = (
            difference / tcp["mean_ms"]
        ) * 100

        throughput_difference = (
            (grpc["mean_throughput_msg_s"]
             - tcp["mean_throughput_msg_s"])
            / tcp["mean_throughput_msg_s"]
        ) * 100

        results.append({
            "message_size": size,
            "tcp_mean_ms": tcp["mean_ms"],
            "grpc_mean_ms": grpc["mean_ms"],
            "tcp_minus_grpc_ms": difference,
            "difference_ci95_lower_ms": difference - margin,
            "difference_ci95_upper_ms": difference + margin,
            "grpc_latency_reduction_percent": improvement,
            "tcp_throughput_msg_s": tcp["mean_throughput_msg_s"],
            "grpc_throughput_msg_s": grpc["mean_throughput_msg_s"],
            "grpc_throughput_change_percent": throughput_difference,
        })

    return pd.DataFrame(results)


def calculate_concurrency(tcp, grpc):
    """Resume los resultados de las pruebas concurrentes."""

    results = []

    for mechanism, data in [
        ("TCP", tcp),
        ("gRPC", grpc)
    ]:
        latency = data["latency_ms"]

        results.append({
            "mechanism": mechanism,
            "requests": len(data),
            "mean_ms": latency.mean(),
            "median_ms": latency.median(),
            "minimum_ms": latency.min(),
            "maximum_ms": latency.max(),
            "std_ms": latency.std(ddof=1),
            "successful_responses": data["response"].notna().sum(),
        })

    return pd.DataFrame(results)


def generate_latency_graph(statistics):
    """Genera la comparación de latencia media."""

    sizes = sorted(statistics["message_size"].unique())

    fig, ax = plt.subplots(figsize=(9, 5))

    x = np.arange(len(sizes))
    width = 0.35

    for index, mechanism in enumerate(["TCP", "gRPC"]):
        subset = statistics[
            statistics["mechanism"] == mechanism
        ].set_index("message_size").reindex(sizes)

        means = subset["mean_ms"].to_numpy()
        lower = means - subset["ci95_lower_ms"].to_numpy()
        upper = subset["ci95_upper_ms"].to_numpy() - means

        ax.bar(
            x + (index - 0.5) * width,
            means,
            width,
            label=mechanism,
            yerr=np.vstack([lower, upper]),
            capsize=5
        )

    ax.set_title("Latencia media: TCP frente a gRPC")
    ax.set_xlabel("Tamaño del mensaje")
    ax.set_ylabel("Latencia (ms)")
    ax.set_xticks(x)
    ax.set_xticklabels(sizes)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "comparative_latency.png", dpi=300)
    plt.close(fig)


def generate_distribution_graph(data):
    """Genera histogramas de distribución de latencias."""

    fig, ax = plt.subplots(figsize=(10, 5))

    for (mechanism, size), group in data.groupby(
        ["mechanism", "message_size"]
    ):
        ax.hist(
            group["latency_ms"],
            bins=30,
            alpha=0.45,
            label=f"{mechanism} - {size}"
        )

    ax.set_title("Distribución de latencias")
    ax.set_xlabel("Latencia (ms)")
    ax.set_ylabel("Frecuencia")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        FIGURES_DIR / "comparative_distribution.png",
        dpi=300
    )
    plt.close(fig)


def generate_throughput_graph(statistics):
    """Genera la comparación del throughput."""

    pivot = statistics.pivot(
        index="message_size",
        columns="mechanism",
        values="mean_throughput_msg_s"
    )

    ax = pivot.plot(
        kind="bar",
        figsize=(9, 5),
        width=0.7
    )

    ax.set_title("Throughput medio: TCP frente a gRPC")
    ax.set_xlabel("Tamaño del mensaje")
    ax.set_ylabel("Mensajes por segundo")
    ax.legend(title="Mecanismo")
    ax.grid(axis="y", alpha=0.3)

    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(
        FIGURES_DIR / "comparative_throughput.png",
        dpi=300
    )
    plt.close()


def print_results(statistics, comparison, concurrency):
    """Muestra los resultados principales."""

    print("\n=== ESTADÍSTICAS POR MECANISMO ===")
    print(statistics.round(6).to_string(index=False))

    print("\n=== COMPARACIÓN TCP Y gRPC ===")
    print(comparison.round(6).to_string(index=False))

    print("\n=== RESULTADOS DE CONCURRENCIA ===")
    print(concurrency.round(6).to_string(index=False))


def main():
    print("INICIANDO ANÁLISIS COMPARATIVO TCP Y gRPC")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    tcp = load_latency_file(TCP_LATENCY, "TCP")
    grpc = load_latency_file(GRPC_LATENCY, "gRPC")

    tcp_sizes = set(
        zip(tcp["message_size"], tcp["message_bytes"])
    )
    grpc_sizes = set(
        zip(grpc["message_size"], grpc["message_bytes"])
    )

    if tcp_sizes != grpc_sizes:
        raise ValueError(
            "TCP y gRPC no utilizan los mismos tamaños de mensaje"
        )

    counts = pd.concat([tcp, grpc]).groupby(
        ["mechanism", "message_size"]
    ).size().unstack(fill_value=0)

    if len(counts.columns) < 1 or (counts.nunique(axis=0) == 0).any():
        raise ValueError("No se pudieron comprobar las muestras")

    for size in set(tcp["message_size"]):
        tcp_count = len(tcp[tcp["message_size"] == size])
        grpc_count = len(grpc[grpc["message_size"] == size])

        if tcp_count != grpc_count:
            raise ValueError(
                f"Cantidad de muestras diferente para {size}"
            )

    expected_routes = {
        ("nodo-A", "nodo-B"),
        ("nodo-B", "nodo-C"),
        ("nodo-C", "nodo-A"),
    }

    tcp_concurrency = load_concurrency_file(
        TCP_CONCURRENCY, expected_routes
    )
    grpc_concurrency = load_concurrency_file(
        GRPC_CONCURRENCY, expected_routes
    )

    statistics = calculate_statistics(
        pd.concat([tcp, grpc], ignore_index=True)
    )

    comparison = compare_mechanisms(statistics)

    concurrency = calculate_concurrency(
        tcp_concurrency,
        grpc_concurrency
    )

    statistics.to_csv(
        STATISTICS_OUTPUT,
        index=False,
        float_format="%.6f",
        encoding="utf-8"
    )

    comparison.to_csv(
        DATA_DIR / "comparative_differences.csv",
        index=False,
        float_format="%.6f",
        encoding="utf-8"
    )

    concurrency.to_csv(
        CONCURRENCY_OUTPUT,
        index=False,
        float_format="%.6f",
        encoding="utf-8"
    )

    generate_latency_graph(statistics)

    generate_distribution_graph(
        pd.concat([tcp, grpc], ignore_index=True)
    )

    generate_throughput_graph(statistics)

    print_results(statistics, comparison, concurrency)

    print("\n=== ARCHIVOS GENERADOS ===")
    print(STATISTICS_OUTPUT)
    print(DATA_DIR / "comparative_differences.csv")
    print(CONCURRENCY_OUTPUT)
    print(FIGURES_DIR)

    print("\nAnálisis comparativo finalizado correctamente.")


if __name__ == "__main__":
    main()
