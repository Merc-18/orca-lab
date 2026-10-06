"""
Módulo para exportación de tareas a formato CSV.

Permite exportar colecciones de tareas (listas de diccionarios o gestores de tareas)
a archivos CSV utilizando únicamente la librería estándar de Python.
"""

from datetime import date, datetime
import csv
import io
import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional, TextIO, Union


# Columnas base requeridas por defecto
CAMPOS_BASE: list[str] = ["id", "titulo", "completa", "prioridad", "creado"]

# Nombre de la columna de fecha límite en el CSV
CAMPO_FECHA_LIMITE: str = "fecha_limite"

# Posibles claves utilizadas en diccionarios para indicar fecha límite
CLAVES_FECHA_LIMITE: tuple[str, ...] = (
    "fecha_limite",
    "limite",
    "fecha_vencimiento",
    "vencimiento",
    "due_date",
)


def _detectar_campo_fecha_limite(tareas: Iterable[dict]) -> bool:
    """Determinar si alguna de las tareas incluye información de fecha límite."""
    for tarea in tareas:
        if not isinstance(tarea, dict):
            continue
        for clave in CLAVES_FECHA_LIMITE:
            if clave in tarea:
                return True
    return False


def _obtener_valor_fecha_limite(tarea: dict) -> str:
    """Extraer el valor de fecha límite de una tarea considerando distintas claves."""
    for clave in CLAVES_FECHA_LIMITE:
        if clave in tarea:
            val = tarea[clave]
            if val is None:
                return ""
            if isinstance(val, (datetime, date)):
                return val.isoformat()
            return str(val)
    return ""


def _normalizar_valor_campo(tarea: dict, campo: str) -> Any:
    """Normalizar el valor de un campo específico para la fila CSV."""
    if campo == "id":
        val = tarea.get("id")
        return "" if val is None else val

    if campo == "titulo":
        val = tarea.get("titulo")
        return "" if val is None else str(val)

    if campo == "completa":
        val = tarea.get("completa")
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            val_lower = val.strip().lower()
            if val_lower in ("true", "1", "si", "sí", "yes"):
                return True
            if val_lower in ("false", "0", "no"):
                return False
        return bool(val)

    if campo == "prioridad":
        val = tarea.get("prioridad")
        return str(val) if val else "media"

    if campo == "creado":
        val = tarea.get("creado")
        if val is None:
            return ""
        if isinstance(val, (datetime, date)):
            return val.isoformat()
        return str(val)

    if campo == CAMPO_FECHA_LIMITE or campo in CLAVES_FECHA_LIMITE:
        return _obtener_valor_fecha_limite(tarea)

    val = tarea.get(campo)
    if val is None:
        return ""
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return val


def _preparar_tareas(tareas: Any) -> list[dict]:
    """Preparar y validar la lista de tareas recibida."""
    if tareas is None:
        raise ValueError("La lista de tareas no puede ser None.")

    # Si es una ruta a un archivo JSON
    if isinstance(tareas, (str, Path, os.PathLike)):
        ruta_str = os.fspath(tareas)
        if ruta_str.endswith(".json") and os.path.exists(ruta_str):
            with open(ruta_str, "r", encoding="utf-8") as f:
                datos = json.load(f)
                if isinstance(datos, dict):
                    tareas = datos.get("tareas", [])
                elif isinstance(datos, list):
                    tareas = datos
                else:
                    raise ValueError("El archivo JSON no contiene una estructura válida de tareas.")

    # Si tiene atributo tareas (ej. TareaManager.tareas) o método listar_tareas
    if hasattr(tareas, "tareas") and isinstance(getattr(tareas, "tareas"), list):
        tareas = getattr(tareas, "tareas")
    elif hasattr(tareas, "listar_tareas") and callable(tareas.listar_tareas):
        tareas = tareas.listar_tareas()

    if not isinstance(tareas, Iterable):
        raise TypeError("El parámetro tareas debe ser una colección iterable de diccionarios.")

    lista = list(tareas)
    for i, item in enumerate(lista):
        if not isinstance(item, dict):
            raise TypeError(f"El elemento en el índice {i} no es un diccionario válido de tarea.")

    return lista


def exportar_a_csv(
    tareas: Any,
    ruta_archivo: Union[str, Path, os.PathLike, TextIO] = "tareas.csv",
    incluir_fecha_limite: Optional[bool] = None,
    columnas: Optional[list[str]] = None,
    campos: Optional[list[str]] = None,
) -> Union[str, TextIO]:
    """
    Exportar una lista de tareas a un archivo CSV.

    Args:
        tareas: Lista de diccionarios de tareas, instancia de TareaManager o ruta a JSON.
        ruta_archivo: Ruta del archivo destino (str o Path) o archivo ya abierto.
        incluir_fecha_limite: Forzar inclusión (True) o exclusión (False) de la columna
                             fecha_limite. Si es None, se detecta automáticamente.
        columnas: Lista opcional de nombres de columnas a incluir.
        campos: Alias para columnas.

    Returns:
        La ruta del archivo exportado (str) o el objeto de archivo escrito.
    """
    lista_tareas = _preparar_tareas(tareas)

    # Determinar encabezados
    cols = columnas or campos
    if cols is not None:
        encabezados = list(cols)
    else:
        encabezados = list(CAMPOS_BASE)
        if incluir_fecha_limite is True or (
            incluir_fecha_limite is None and _detectar_campo_fecha_limite(lista_tareas)
        ):
            if CAMPO_FECHA_LIMITE not in encabezados:
                encabezados.append(CAMPO_FECHA_LIMITE)

    # Generar contenido en CSV
    filas = [encabezados]
    for tarea in lista_tareas:
        fila = [_normalizar_valor_campo(tarea, campo) for campo in encabezados]
        filas.append(fila)

    # Escribir en destino
    if hasattr(ruta_archivo, "write") and callable(ruta_archivo.write):
        writer = csv.writer(ruta_archivo, lineterminator="\n")
        writer.writerows(filas)
        return ruta_archivo

    ruta_str = os.fspath(ruta_archivo)
    dir_padre = os.path.dirname(ruta_str)
    if dir_padre and not os.path.exists(dir_padre):
        os.makedirs(dir_padre, exist_ok=True)

    with open(ruta_str, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerows(filas)

    return ruta_str


def exportar_a_csv_string(
    tareas: Any,
    incluir_fecha_limite: Optional[bool] = None,
    columnas: Optional[list[str]] = None,
    campos: Optional[list[str]] = None,
) -> str:
    """Exportar tareas a una cadena de texto en formato CSV en memoria."""
    buffer = io.StringIO()
    exportar_a_csv(
        tareas=tareas,
        ruta_archivo=buffer,
        incluir_fecha_limite=incluir_fecha_limite,
        columnas=columnas,
        campos=campos,
    )
    return buffer.getvalue()


# Alias convenientes para la función principal
exportar_csv = exportar_a_csv
exportar_tareas_csv = exportar_a_csv
exportar_tareas_a_csv = exportar_a_csv


class ExportadorCSV:
    """Clase de conveniencia orientada a objetos para exportación de tareas a CSV."""

    def __init__(
        self,
        ruta_archivo: Union[str, Path, os.PathLike] = "tareas.csv",
        incluir_fecha_limite: Optional[bool] = None,
        columnas: Optional[list[str]] = None,
    ):
        self.ruta_archivo = ruta_archivo
        self.incluir_fecha_limite = incluir_fecha_limite
        self.columnas = columnas

    def exportar(
        self,
        tareas: Any,
        ruta_archivo: Optional[Union[str, Path, os.PathLike, TextIO]] = None,
    ) -> Union[str, TextIO]:
        """Ejecutar la exportación de tareas."""
        destino = self.ruta_archivo if ruta_archivo is None else ruta_archivo
        return exportar_a_csv(
            tareas=tareas,
            ruta_archivo=destino,
            incluir_fecha_limite=self.incluir_fecha_limite,
            columnas=self.columnas,
        )


if __name__ == "__main__":
    import sys

    origen = sys.argv[1] if len(sys.argv) > 1 else "tareas.json"
    destino = sys.argv[2] if len(sys.argv) > 2 else "tareas.csv"

    try:
        resultado = exportar_a_csv(origen, destino)
        print(f"Tareas exportadas exitosamente a: {resultado}")
    except Exception as e:
        print(f"Error al exportar tareas: {e}", file=sys.stderr)
        sys.exit(1)
