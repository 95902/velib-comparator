"""Tests de la météo, sans appel réel à l'API (réponse simulée)."""
import pandas as pd
import pytest

from src import meteo

# Réponse réelle de station/infrahoraire-6m (8 novembre 2026), raccourcie
REPONSE = [{
    "geo_id_insee": "75114001", "validity_time": "2026-11-08T09:36:00Z",
    "t": 277.35, "ff": 1.6, "rr_per": 0.0, "u": 98,
}]


class FausseReponse:
    def raise_for_status(self):
        pass

    def json(self):
        return REPONSE


def test_conversions():
    assert meteo.kelvin_vers_celsius(273.15) == 0.0
    assert meteo.kelvin_vers_celsius(None) is None
    assert meteo.ms_vers_kmh(10) == 36.0


def test_meteo_actuelle(monkeypatch):
    monkeypatch.setenv("METEO_FRANCE_API_KEY", "cle-de-test")
    monkeypatch.setattr(meteo.requests, "get", lambda *args, **kwargs: FausseReponse())
    assert meteo.meteo_actuelle() == {
        "temperature_c": 4.2,
        "vent_kmh": 5.8,
        "pluie_mm": 0.0,
        "heure_releve": pd.Timestamp("2026-11-08T09:36:00Z"),
    }


def test_cle_absente(monkeypatch):
    monkeypatch.setattr(meteo, "load_dotenv", lambda chemin: None)
    monkeypatch.delenv("METEO_FRANCE_API_KEY", raising=False)
    with pytest.raises(meteo.CleMeteoAbsente):
        meteo.meteo_actuelle()
