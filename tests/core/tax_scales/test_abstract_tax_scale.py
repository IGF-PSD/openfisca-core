import pytest

from openfisca_core import taxscales


def test_abstract_tax_scale():
    with pytest.warns(DeprecationWarning):
        result = taxscales.AbstractTaxScale()
        assert isinstance(result, taxscales.AbstractTaxScale)
