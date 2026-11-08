"""Données partagées par les tests."""
from pathlib import Path

import pandas as pd
import pytest

CHEMIN_TEST = Path(__file__).parent / "donnees_test.csv"


@pytest.fixture
def df_test():
    """Les 6 vraies stations figées de tests/donnees_test.csv (format du contrat)."""
    return pd.read_csv(CHEMIN_TEST, dtype={"stationcode": str})
