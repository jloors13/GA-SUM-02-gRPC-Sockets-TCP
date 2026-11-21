
import argparse
import csv
import math
from pathlib import Path


NODES = {"nodo-A", "nodo-B", "nodo-C"}

SCHEMAS = {
    "latency": {
        "mechanism", "message_size", "message_bytes",
        "repetition", "sample", "latency_ms",
        "run_duration_s", "throughput_msg_s", "timestamp"
    },
    "exchanges": {
        "exchange", "sender", "destination", "message",
        "sender_timestamp", "receiver_timestamp",
        "response_timestamp", "client_receive_timestamp",
        "response", "timestamp"
    },
    "concurrency": {
        "sender", "destination", "latency_ms",
        "response", "timestamp"
    },
    "statistics": {
        "mechanism", "message_size", "message_bytes",
        "samples", "mean_ms", "median_ms", "minimum_ms",
        "maximum_ms", "std_ms", "p95_ms",
        "mean_throughput_msg_s"
    }
}


def load_csv(file_path, tipo):
    """Lee un CSV y comprueba sus columnas y registros."""

    path = Path(file_path)

    if tipo not in SCHEMAS:
        raise ValueError(f"Tipo de archivo desconocido: {tipo}")

    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("El CSV no contiene encabezados")

        missing = SCHEMAS[tipo] - set(reader.fieldnames)

        if missing:
            raise ValueError(
                f"Faltan columnas obligatorias: {sorted(missing)}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError("El CSV no contiene registros")

    for line, row in enumerate(rows, start=2):
        if any(
            value is None or not isinstance(value, str)
            or not value.strip()
            for value in row.values()
        ):
            raise ValueError(
                f"Registro vacío o incompleto en la línea {line}"
            )

    return rows


def number(row, column, line, integer=False, positive=False):
    """Comprueba que un valor numérico sea válido."""

    try:
        value = (
            int(row[column])
            if integer
            else float(row[column])
        )

    except (ValueError, TypeError, OverflowError, KeyError):
        raise ValueError(
            f"Línea {line}: valor numérico inválido en {column}"
        ) from None

    if not math.isfinite(value):
        raise ValueError(
            f"Línea {line}: {column} contiene NaN o Infinity"
        )

    if value < 0:
        raise ValueError(
            f"Línea {line}: {column} no puede ser negativo"
        )

    if positive and value == 0:
        raise ValueError(
            f"Línea {line}: {column} debe ser mayor que cero"
        )

    return value


def validate_latency(rows):
    """Revisa los resultados de latencia."""

    for line, row in enumerate(rows, start=2):

        if not row["mechanism"].strip():
            raise ValueError(
                f"Línea {line}: mecanismo vacío"
            )

        if not row["message_size"].strip():
            raise ValueError(
                f"Línea {line}: tamaño de mensaje vacío"
            )

        number(
            row, "message_bytes", line,
            integer=True, positive=True
        )

        number(
            row, "repetition", line,
            integer=True, positive=True
        )

        number(
            row, "sample", line,
            integer=True, positive=True
        )

        number(row, "latency_ms", line)

        number(
            row, "run_duration_s", line,
            positive=True
        )

        number(row, "throughput_msg_s", line)


def validate_exchanges(rows):
    """Revisa los intercambios y el orden de Lamport."""

    for line, row in enumerate(rows, start=2):

        sender = row["sender"]
        destination = row["destination"]

        if sender not in NODES or destination not in NODES:
            raise ValueError(
                f"Línea {line}: nodo desconocido"
            )

        if sender == destination:
            raise ValueError(
                f"Línea {line}: comunicación al mismo nodo"
            )

        number(
            row, "exchange", line,
            integer=True, positive=True
        )

        timestamps = [
            number(row, column, line, integer=True)
            for column in (
                "sender_timestamp",
                "receiver_timestamp",
                "response_timestamp",
                "client_receive_timestamp"
            )
        ]

        if not all(
            first < second
            for first, second in zip(
                timestamps, timestamps[1:]
            )
        ):
            raise ValueError(
                f"Línea {line}: orden causal incorrecto "
                f"{timestamps}"
            )

        if (
            not row["message"].strip()
            or not row["response"].strip()
        ):
            raise ValueError(
                f"Línea {line}: mensaje o respuesta vacíos"
            )


def validate_concurrency(rows):
    """Comprueba los resultados de concurrencia."""

    for line, row in enumerate(rows, start=2):

        sender = row["sender"]
        destination = row["destination"]

        if sender not in NODES or destination not in NODES:
            raise ValueError(
                f"Línea {line}: nodo desconocido"
            )

        if sender == destination:
            raise ValueError(
                f"Línea {line}: nodos iguales"
            )

        number(row, "latency_ms", line)

        if not row["response"].strip():
            raise ValueError(
                f"Línea {line}: respuesta vacía"
            )


def validate_statistics(rows):
    """Comprueba que las estadísticas tengan valores coherentes."""

    for line, row in enumerate(rows, start=2):

        if not row["mechanism"].strip():
            raise ValueError(
                f"Línea {line}: mecanismo vacío"
            )

        if not row["message_size"].strip():
            raise ValueError(
                f"Línea {line}: tamaño de mensaje vacío"
            )

        number(
            row, "message_bytes", line,
            integer=True, positive=True
        )

        number(
            row, "samples", line,
            integer=True, positive=True
        )

        values = {
            column: number(row, column, line)
            for column in (
                "mean_ms",
                "median_ms",
                "minimum_ms",
                "maximum_ms",
                "std_ms",
                "p95_ms",
                "mean_throughput_msg_s"
            )
        }

        minimum = values["minimum_ms"]
        maximum = values["maximum_ms"]

        if minimum > maximum:
            raise ValueError(
                f"Línea {line}: mínimo mayor que máximo"
            )

        for column in ("mean_ms", "median_ms", "p95_ms"):
            if not minimum <= values[column] <= maximum:
                raise ValueError(
                    f"Línea {line}: {column} fuera del rango"
                )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Valida los archivos CSV de los experimentos "
            "de Sockets TCP y gRPC."
        )
    )

    parser.add_argument(
        "archivo",
        help="Ruta del archivo CSV"
    )

    parser.add_argument(
        "--tipo",
        required=True,
        choices=sorted(SCHEMAS),
        help="Tipo de resultados"
    )

    args = parser.parse_args()

    validators = {
        "latency": validate_latency,
        "exchanges": validate_exchanges,
        "concurrency": validate_concurrency,
        "statistics": validate_statistics
    }

    try:
        rows = load_csv(args.archivo, args.tipo)

        validators[args.tipo](rows)

        print(f"Archivo: {args.archivo}")
        print(f"Tipo: {args.tipo}")
        print(f"Registros verificados: {len(rows)}")
        print("Resultado: validación correcta")

    except (OSError, ValueError, csv.Error) as error:
        parser.exit(
            1,
            f"ERROR: {error}\n"
        )


if __name__ == "__main__":
    main()
