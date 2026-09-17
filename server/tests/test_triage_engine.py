"""Tests unitarios del TriageEngine.

Estos tests verifican:
 - Normalizacion Unicode (NFD + eliminacion de diacriticos)
 - Los tres operadores: EQUALS, CONTAINS, STARTSWITH
 - El case _ default (retorna False para operador desconocido) — regresion del bug critico
 - Clasificacion en las cuatro prioridades con scores conocidos
 - Reproduccion de casos del experimento de calibracion (Fase 4, Capitulo 6):
     ACV + CT + Box Rojo + Guardia + urgente -> Critico (RF-02)
 - Regla deshabilitada no suma score
 - Campo ausente en la orden es ignorado sin excepcion
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock

from app.modules.triage.triage import TriageEngine
from app.modules.triage.model import TriageOperator
from app.modules.medical_order.model import MedicalPriority, Modality

from tests.conftest import make_settings, make_rule, make_order


# ── Normalizacion Unicode ─────────────────────────────────────────────────────

class TestNormalizacion:
    def test_minusculas(self):
        assert TriageEngine._norm("ACV") == "acv"

    def test_tilde_vocal(self):
        assert TriageEngine._norm("Urgente") == "urgente"

    def test_tilde_acv_isquemico(self):
        assert TriageEngine._norm("ACV Isquémico") == "acv isquemico"

    def test_tilde_evolucion(self):
        assert TriageEngine._norm("Evolución crónica") == "evolucion cronica"

    def test_tilde_colecistitis(self):
        assert "colecistitis" in TriageEngine._norm("Colecistitis aguda litiásica")


# ── Operadores ────────────────────────────────────────────────────────────────

class TestOperadores:
    def test_equals_exacto(self):
        assert TriageEngine._matches("CT", TriageOperator.EQUALS, "CT") is True

    def test_equals_no_coincide(self):
        assert TriageEngine._matches("MR", TriageOperator.EQUALS, "CT") is False

    def test_equals_case_insensitive(self):
        assert TriageEngine._matches("ct", TriageOperator.EQUALS, "CT") is True

    def test_contains_presente(self):
        assert TriageEngine._matches("ACV isquémico agudo", TriageOperator.CONTAINS, "ACV") is True

    def test_contains_ausente(self):
        assert TriageEngine._matches("Fractura de radio", TriageOperator.CONTAINS, "ACV") is False

    def test_contains_con_tilde_en_texto(self):
        # El patron sin tilde debe coincidir con texto que la tiene
        assert TriageEngine._matches("Colecistitis aguda litiásica", TriageOperator.CONTAINS, "colecistitis") is True

    def test_startswith_correcto(self):
        assert TriageEngine._matches("Guardia General", TriageOperator.STARTSWITH, "guardia") is True

    def test_startswith_no_coincide_si_no_al_inicio(self):
        assert TriageEngine._matches("UTI Guardia", TriageOperator.STARTSWITH, "guardia") is False

    def test_default_case_operador_desconocido_retorna_false(self):
        """Regresion: antes de la correccion, _matches retornaba None para operadores no cubiertos."""
        resultado = TriageEngine._matches("cualquier valor", MagicMock(), "patron")
        assert resultado is False, "El case default debe retornar False, nunca None"
        assert isinstance(resultado, bool), "El tipo de retorno debe ser bool, no None"


# ── Map de prioridades ────────────────────────────────────────────────────────

class TestMapPrioridad:
    def test_critico_en_umbral(self):
        s = make_settings(critical=25, urgent=12, priority=10)
        assert TriageEngine._map_priority(25, s) == MedicalPriority.CRITICAL

    def test_critico_sobre_umbral(self):
        s = make_settings(critical=25, urgent=12, priority=10)
        assert TriageEngine._map_priority(50, s) == MedicalPriority.CRITICAL

    def test_urgente_en_umbral(self):
        s = make_settings(critical=25, urgent=12, priority=10)
        assert TriageEngine._map_priority(12, s) == MedicalPriority.URGENT

    def test_urgente_bajo_critico(self):
        s = make_settings(critical=25, urgent=12, priority=10)
        assert TriageEngine._map_priority(24, s) == MedicalPriority.URGENT

    def test_prioritario_en_umbral(self):
        s = make_settings(critical=25, urgent=12, priority=10)
        assert TriageEngine._map_priority(10, s) == MedicalPriority.PRIORITY

    def test_rutina_bajo_umbral(self):
        s = make_settings(critical=25, urgent=12, priority=10)
        assert TriageEngine._map_priority(9, s) == MedicalPriority.ROUTINE

    def test_rutina_score_cero(self):
        s = make_settings(critical=25, urgent=12, priority=10)
        assert TriageEngine._map_priority(0, s) == MedicalPriority.ROUTINE

    def test_rutina_score_negativo(self):
        s = make_settings(critical=25, urgent=12, priority=10)
        assert TriageEngine._map_priority(-50, s) == MedicalPriority.ROUTINE


# ── Evaluacion completa ───────────────────────────────────────────────────────

class TestEvaluate:
    def test_caso_critico_acv_ct_box_rojo_guardia(self, calibrated_rules, default_settings):
        """Reproduccion de caso CRITICO del experimento Fase 4 (RF-02):
        ACV(20) + CT(6) + Box Rojo(6) + Guardia(4) + urgente(4) = 40 -> Critico."""
        order = make_order(
            modality=Modality.CT,
            diagnosis="ACV isquémico agudo",
            patient_location="Box Rojo",
            origin_service="Guardia",
            is_urgent=True,
        )
        priority, criterios = TriageEngine.evaluate(order, calibrated_rules, default_settings)
        assert priority == MedicalPriority.CRITICAL
        assert criterios["total_score"] >= 25
        campos_activados = {r["field"] for r in criterios["rules_matched"]}
        assert "diagnosis" in campos_activados   # ACV activo
        assert "modality" in campos_activados    # CT activo

    def test_caso_urgente_hemorragia_us_guardia(self, calibrated_rules, default_settings):
        """hemorragia(12) + US(2) + Guardia(4) = 18 -> Urgente."""
        order = make_order(
            modality=Modality.US,
            diagnosis="Hemorragia digestiva baja leve",
            patient_location="Box Comun",
            origin_service="Guardia",
            is_urgent=False,
        )
        priority, criterios = TriageEngine.evaluate(order, calibrated_rules, default_settings)
        assert priority == MedicalPriority.URGENT
        assert 12 <= criterios["total_score"] < 25

    def test_caso_rutina_ambulatorio_control(self, calibrated_rules, default_settings):
        """control(-5) + DX(1) + Ambulatorio(-50) -> Rutina (score muy negativo)."""
        order = make_order(
            modality=Modality.DX,
            diagnosis="Control anual de rutina",
            patient_location="Consultorio",
            origin_service="Ambulatorio",
            is_urgent=False,
        )
        priority, criterios = TriageEngine.evaluate(order, calibrated_rules, default_settings)
        assert priority == MedicalPriority.ROUTINE
        assert criterios["total_score"] < 10

    def test_regla_deshabilitada_no_suma(self, default_settings):
        """Una regla con enabled=False no debe sumar su peso al score."""
        rules = [
            make_rule("diagnosis", TriageOperator.CONTAINS, "ACV", 20, enabled=False),
            make_rule("modality",  TriageOperator.EQUALS,   "CT",   6, enabled=True),
        ]
        order = make_order(
            modality=Modality.CT,
            diagnosis="ACV isquémico",
        )
        priority, criterios = TriageEngine.evaluate(order, rules, default_settings)
        # Solo CT(6) suma, ACV deshabilitado no suma -> score = 6 -> Rutina
        assert criterios["total_score"] == 6
        assert priority == MedicalPriority.ROUTINE

    def test_campo_inexistente_ignorado_sin_excepcion(self, default_settings):
        """Un campo que no existe en la orden debe ignorarse sin lanzar excepcion."""
        rules = [
            make_rule("campo_que_no_existe_en_model", TriageOperator.CONTAINS, "valor", 20),
            make_rule("modality", TriageOperator.EQUALS, "CT", 6),
        ]
        order = make_order(modality=Modality.CT)
        # No debe lanzar AttributeError ni KeyError
        priority, criterios = TriageEngine.evaluate(order, rules, default_settings)
        assert criterios["total_score"] == 6

    def test_criterios_registra_reglas_activadas(self, calibrated_rules, default_settings):
        """criterios_evaluados debe registrar cada regla que activo con su campo y peso."""
        order = make_order(
            modality=Modality.CT,
            diagnosis="Politraumatismo grave",
            patient_location="Shock Room",
            origin_service="Guardia",
            is_urgent=True,
        )
        _, criterios = TriageEngine.evaluate(order, calibrated_rules, default_settings)
        assert "rules_matched" in criterios
        assert "total_score" in criterios
        # politrauma(18) + CT(6) + Shock Room(8) + Guardia(4) + urgente(4) = 40
        assert len(criterios["rules_matched"]) >= 4

    def test_score_es_suma_exacta_de_pesos(self, default_settings):
        """total_score debe ser exactamente la suma de los pesos de las reglas activadas."""
        rules = [
            make_rule("diagnosis", TriageOperator.CONTAINS, "ACV", 20),
            make_rule("modality",  TriageOperator.EQUALS,   "CT",   6),
            make_rule("modality",  TriageOperator.EQUALS,   "MR",   5),  # no activa con CT
        ]
        order = make_order(
            modality=Modality.CT,
            diagnosis="ACV isquémico",
        )
        _, criterios = TriageEngine.evaluate(order, rules, default_settings)
        assert criterios["total_score"] == 26  # ACV(20) + CT(6) = 26

    def test_pesos_negativos_reducen_score(self, default_settings):
        """Los pesos negativos (ambulatorio) deben reducir el score correctamente."""
        rules = [
            make_rule("origin_service", TriageOperator.CONTAINS, "ambulatorio", -50),
            make_rule("modality",       TriageOperator.EQUALS,   "DX",           1),
        ]
        order = make_order(
            modality=Modality.DX,
            origin_service="Ambulatorio",
        )
        _, criterios = TriageEngine.evaluate(order, rules, default_settings)
        assert criterios["total_score"] == -49  # -50 + 1


# ── Reproduccion del experimento de calibracion (Fase 4) ─────────────────────

class TestReproduccionFase4:
    """Reproduce escenarios representativos del Capitulo 6 con scores exactos conocidos.

    El experimento original uso el mismo conjunto de 50 ordenes para calibrar y
    evaluar (hallazgo A-01 del dictamen). Estos tests verifican que la logica del
    motor produce los resultados correctos para casos con scores documentados.
    """

    def test_acv_ct_box_rojo_guardia_urgente_score_40(self, calibrated_rules, default_settings):
        """ACV(20) + CT(6) + Box Rojo(6) + Guardia(4) + urgente(4) = 40 -> Critico."""
        order = make_order(
            modality=Modality.CT,
            diagnosis="ACV",
            patient_location="Box Rojo",
            origin_service="Guardia",
            is_urgent=True,
        )
        priority, criterios = TriageEngine.evaluate(order, calibrated_rules, default_settings)
        assert criterios["total_score"] == 40
        assert priority == MedicalPriority.CRITICAL

    def test_rutina_ambulatorio_control_seguimiento_score_negativo(self, calibrated_rules, default_settings):
        """control(-5) + seguimiento(-5) + DX(1) + Ambulatorio(-50) = -59 -> Rutina."""
        order = make_order(
            modality=Modality.DX,
            diagnosis="Control de seguimiento",
            patient_location="Consultorio",
            origin_service="Ambulatorio",
            is_urgent=False,
        )
        priority, criterios = TriageEngine.evaluate(order, calibrated_rules, default_settings)
        assert criterios["total_score"] < 0
        assert priority == MedicalPriority.ROUTINE

    def test_tep_ct_internacion_score_20_urgente(self, calibrated_rules, default_settings):
        """TEP(10) + CT(6) + Internacion(4) = 20 -> Urgente."""
        order = make_order(
            modality=Modality.CT,
            diagnosis="TEP masivo",
            patient_location="Sala General",
            origin_service="Internacion",
            is_urgent=False,
        )
        priority, criterios = TriageEngine.evaluate(order, calibrated_rules, default_settings)
        assert criterios["total_score"] == 20
        assert priority == MedicalPriority.URGENT

    def test_normalizacion_nfd_activa_regla_evolucion_con_tilde(self, calibrated_rules, default_settings):
        """La normalizacion NFD permite que texto con tilde active la regla sin tilde."""
        order = make_order(
            modality=Modality.DX,
            diagnosis="Evolución post-quirúrgica",
            patient_location="Sala",
            origin_service="Internacion",
            is_urgent=False,
        )
        _, criterios = TriageEngine.evaluate(order, calibrated_rules, default_settings)
        pesos_negativos = [r["weight"] for r in criterios["rules_matched"] if r["weight"] < 0]
        assert any(p == -5 for p in pesos_negativos), (
            "La regla de evolucion (-5) debe activarse con texto con tilde gracias a NFD"
        )
