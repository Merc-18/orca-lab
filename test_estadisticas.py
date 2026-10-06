"""Pruebas automatizadas para las estadísticas de tareas."""

from copy import deepcopy
import unittest

from estadisticas import calcular_estadisticas


class TestEstadisticas(unittest.TestCase):
    def test_lista_vacia(self):
        self.assertEqual(calcular_estadisticas([]), {
            "total": 0,
            "pendientes": 0,
            "completadas": 0,
            "por_prioridad": {"alta": 0, "media": 0, "baja": 0},
        })

    def test_estados_y_prioridades_mixtos(self):
        tareas = [
            {"completa": False, "prioridad": "alta"},
            {"completa": True, "prioridad": "alta"},
            {"completa": False, "prioridad": "media"},
            {"completa": True, "prioridad": "baja"},
            {"completa": False, "prioridad": "baja"},
            {"completa": False, "prioridad": "baja"},
        ]
        self.assertEqual(calcular_estadisticas(tareas), {
            "total": 6,
            "pendientes": 4,
            "completadas": 2,
            "por_prioridad": {"alta": 2, "media": 1, "baja": 3},
        })

    def test_todas_pendientes_o_completadas(self):
        for completa in (False, True):
            with self.subTest(completa=completa):
                tareas = [{"completa": completa, "prioridad": "media"}] * 3
                self.assertEqual(calcular_estadisticas(tareas), {
                    "total": 3,
                    "pendientes": 0 if completa else 3,
                    "completadas": 3 if completa else 0,
                    "por_prioridad": {"alta": 0, "media": 3, "baja": 0},
                })

    def test_tareas_antiguas_sin_prioridad(self):
        tareas = [{"completa": False}, {"completa": True}]
        self.assertEqual(calcular_estadisticas(tareas), {
            "total": 2,
            "pendientes": 1,
            "completadas": 1,
            "por_prioridad": {"alta": 0, "media": 2, "baja": 0},
        })

    def test_no_modifica_las_tareas(self):
        tareas = [{
            "id": 1, "titulo": "Comprar leche", "completa": False,
            "prioridad": "alta", "metadata": {"etiquetas": ["compras"]},
        }]
        original = deepcopy(tareas)
        calcular_estadisticas(tareas)
        self.assertEqual(tareas, original)

    def test_resultados_independientes_entre_llamadas(self):
        resultado = calcular_estadisticas([
            {"completa": True, "prioridad": "alta"},
        ])
        resultado["por_prioridad"]["alta"] = 99
        self.assertEqual(calcular_estadisticas([])["por_prioridad"], {
            "alta": 0, "media": 0, "baja": 0,
        })


if __name__ == "__main__":
    unittest.main()
