
import csv
from datetime import datetime
from pathlib import Path


NODES = ("nodo-A", "nodo-B", "nodo-C")


def verify_events(file_path, expected_node):
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    required = {"node", "event_type", "lamport_time", "real_time"}

    total = 0
    sessions = 0
    previous = None
    previous_date = None

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Columnas incompletas en {path}")

        for line_number, row in enumerate(reader, start=2):
            if row["node"] != expected_node:
                raise ValueError(
                    f"{path}:{line_number}: nodo incorrecto"
                )

            if row["event_type"] not in ("send", "receive"):
                raise ValueError(
                    f"{path}:{line_number}: evento desconocido"
                )

            try:
                current = int(row["lamport_time"])
            except (TypeError, ValueError):
                raise ValueError(
                    f"{path}:{line_number}: timestamp inválido"
                ) from None

            if current < 1:
                raise ValueError(
                    f"{path}:{line_number}: timestamp no positivo"
                )

            try:
                event_date = datetime.fromisoformat(row["real_time"])
            except (TypeError, ValueError):
                raise ValueError(
                    f"{path}:{line_number}: fecha inválida"
                ) from None

            if previous is None:
                sessions = 1

            elif current <= previous:
                # Un reinicio es posible si el reloj vuelve a un
                # valor inicial y existe una separación temporal.
                elapsed = (
                    (event_date - previous_date).total_seconds()
                    if previous_date is not None
                    else 0
                )

                if (
                    current in (1,2)
                    and elapsed >=60
                ):
                    sessions += 1
                else:
                    raise ValueError(
                        f"{path}:{line_number}: regresión inesperada "
                        f"({previous} -> {current})"
                    )

            previous = current
            previous_date = event_date
            total += 1

    if total == 0:
        raise ValueError(f"El archivo no contiene eventos: {path}")

    print(
        f"{expected_node}: {total} eventos verificados, "
        f"{sessions} sesión(es) probable(s)"
    )

    return total


def verify_exchanges(file_path):
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    required = {
        "exchange",
        "sender",
        "destination",
        "sender_timestamp",
        "receiver_timestamp",
        "response_timestamp",
        "client_receive_timestamp",
    }

    total = 0

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                f"Faltan columnas en el archivo: {path}"
            )

        for line_number, row in enumerate(reader, start=2):
            if (
                row["sender"] not in NODES
                or row["destination"] not in NODES
                or row["sender"] == row["destination"]
            ):
                raise ValueError(
                    f"{path}:{line_number}: nodos inválidos"
                )

            try:
                timestamps = [
                    int(row["sender_timestamp"]),
                    int(row["receiver_timestamp"]),
                    int(row["response_timestamp"]),
                    int(row["client_receive_timestamp"]),
                ]
            except (TypeError, ValueError):
                raise ValueError(
                    f"{path}:{line_number}: timestamp inválido"
                ) from None

            if not all(value >= 1 for value in timestamps):
                raise ValueError(
                    f"{path}:{line_number}: timestamp no positivo"
                )

            if not all(
                earlier < later
                for earlier, later in zip(timestamps, timestamps[1:])
            ):
                raise ValueError(
                    f"{path}:{line_number}: orden causal incorrecto "
                    f"{timestamps}"
                )

            total += 1

    if total == 0:
        raise ValueError(
            f"El archivo no contiene intercambios: {path}"
        )

    return total


def main():
    print("=== VERIFICACIÓN DE RELOJES DE LAMPORT ===")

    try:
        for node in NODES:
            path = f"data/tcp_events_{node}.csv"
            verify_events(path, node)

        total = verify_exchanges("data/tcp_exchanges.csv")

        print(f"Intercambios con orden causal válido: {total}")
        print("Resultado: validación completada")

    except (OSError, ValueError) as error:
        print(f"Error de validación: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
