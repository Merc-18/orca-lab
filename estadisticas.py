"""Estadísticas de tareas sin modificar los datos ni acceder a archivos."""


def calcular_estadisticas(tareas: list[dict]) -> dict:
    """Contar tareas por estado y prioridad usando el formato de TareaManager.

    Cada tarea debe tener el campo ``completa``. Las tareas antiguas sin
    ``prioridad`` se cuentan como media, el valor predeterminado de la app.
    El resultado incluye total, pendientes, completadas y por_prioridad,
    con las prioridades alta, media y baja incluso cuando su conteo es cero.
    """
    completadas = sum(bool(tarea["completa"]) for tarea in tareas)
    por_prioridad = {"alta": 0, "media": 0, "baja": 0}
    for tarea in tareas:
        por_prioridad[tarea.get("prioridad", "media")] += 1

    return {
        "total": len(tareas),
        "pendientes": len(tareas) - completadas,
        "completadas": completadas,
        "por_prioridad": por_prioridad,
    }
