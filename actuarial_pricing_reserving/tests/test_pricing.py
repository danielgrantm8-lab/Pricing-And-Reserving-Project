import numpy as np
import pandas as pd
import pytest
from python.pricing import prepare_data, fit_models, predict_prices


def sample_data(n=160):
    rng = np.random.default_rng(2026)
    exposure = rng.uniform(.4, 1, n)
    counts = rng.poisson(.4 * exposure)
    counts[:20] = 1
    freq = pd.DataFrame({'IDpol': range(n), 'Exposure': exposure,
                         'ClaimNb': counts, 'VehAge': rng.integers(1, 12, n),
                         'DrivAge': rng.integers(20, 70, n),
                         'BonusMalus': rng.integers(50, 120, n),
                         'VehBrand': rng.choice(['B1', 'B2'], n),
                         'Area': rng.choice(['A', 'B'], n)})
    sev = pd.DataFrame([(i, float(rng.gamma(2, 1000)))
                        for i, count in enumerate(counts) for _ in range(count)],
                       columns=['IDpol', 'ClaimAmount'])
    return freq, sev


def test_aggregation_and_exposure():
    freq, sev = sample_data()
    result = prepare_data(freq, sev)
    assert len(result) == len(freq)
    assert np.isclose(result.ClaimAmount.sum(), sev.ClaimAmount.sum())
    assert np.isclose(result.observed_frequency.sum(), (result.ClaimNb / result.Exposure).sum())


def test_model_outputs_are_positive_and_premium_identity():
    freq, sev = sample_data()
    df = prepare_data(freq, sev)
    models = fit_models(df)
    result = predict_prices(df, *models)
    assert np.isfinite(result.pure_premium).all()
    assert (result.pure_premium > 0).all()
    np.testing.assert_allclose(result.pure_premium,
                               result.expected_frequency * result.expected_severity)
    np.testing.assert_allclose(result.illustrative_premium, result.pure_premium / .75)


def test_bad_exposure_rejected():
    freq, sev = sample_data()
    freq.loc[0, 'Exposure'] = 0
    with pytest.raises(ValueError, match='Invalid exposure'):
        prepare_data(freq, sev)


def test_invalid_expense_ratio_rejected():
    freq, sev = sample_data()
    df = prepare_data(freq, sev)
    models = fit_models(df)
    with pytest.raises(ValueError, match='Expense ratio'):
        predict_prices(df, *models, expense_ratio=1)


def test_unknown_claim_policy_rejected():
    freq, sev = sample_data()
    sev.loc[0, 'IDpol'] = 999999
    with pytest.raises(ValueError, match='unknown policy'):
        prepare_data(freq, sev)
