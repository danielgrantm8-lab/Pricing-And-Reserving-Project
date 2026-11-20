"""Transparent frequency-severity GLM pricing on the freMTPL2 dataset."""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

FEATURES = 'VehAge + DrivAge + BonusMalus + C(VehBrand) + C(Area)'


def prepare_data(freq: pd.DataFrame, sev: pd.DataFrame) -> pd.DataFrame:
    """Aggregate individual claim amounts to the policy level, then join exposure."""
    required_f = {'IDpol', 'Exposure', 'ClaimNb', 'VehAge', 'DrivAge', 'BonusMalus', 'VehBrand', 'Area'}
    required_s = {'IDpol', 'ClaimAmount'}
    if not required_f.issubset(freq) or not required_s.issubset(sev):
        raise ValueError('Missing required dataset columns')
    if freq.IDpol.duplicated().any():
        raise ValueError('Policy IDs must be unique in frequency data')
    if (freq.Exposure <= 0).any() or (freq.ClaimNb < 0).any() or (sev.ClaimAmount < 0).any():
        raise ValueError('Invalid exposure, count or claim amount')
    amounts = sev.groupby('IDpol', as_index=False)['ClaimAmount'].sum()
    if not set(amounts.IDpol).issubset(set(freq.IDpol)):
        raise ValueError('Severity data contains unknown policy IDs')
    df = freq.merge(amounts, on='IDpol', how='left', validate='one_to_one')
    df['ClaimAmount'] = df.ClaimAmount.fillna(0)
    df['observed_frequency'] = df.ClaimNb / df.Exposure
    df['observed_pure_premium'] = df.ClaimAmount / df.Exposure
    return df


def fit_models(df: pd.DataFrame):
    """Poisson count model with log exposure offset; Gamma cost per claim model."""
    if (df.Exposure <= 0).any():
        raise ValueError('Exposure must be positive')
    frequency = smf.glm('ClaimNb ~ ' + FEATURES, data=df,
                        family=sm.families.Poisson(),
                        offset=np.log(df.Exposure)).fit()
    positive = df.loc[(df.ClaimNb > 0) & (df.ClaimAmount > 0)].copy()
    if len(positive) < 10:
        raise ValueError('At least ten positive-claim policies are required')
    positive['average_claim'] = positive.ClaimAmount / positive.ClaimNb
    severity = smf.glm('average_claim ~ ' + FEATURES, data=positive,
                       family=sm.families.Gamma(sm.families.links.Log()),
                       freq_weights=positive.ClaimNb).fit()
    return frequency, severity


def predict_prices(df: pd.DataFrame, frequency, severity, expense_ratio=0.25):
    """Predict annual frequency, severity, pure premium and illustrative loaded premium."""
    if not 0 <= expense_ratio < 1:
        raise ValueError('Expense ratio must be between 0 and 1')
    result = df.copy()
    # Predict at unit exposure to obtain annual claim frequency.
    result['expected_frequency'] = frequency.predict(df, offset=np.zeros(len(df)))
    result['expected_severity'] = severity.predict(df)
    result['pure_premium'] = result.expected_frequency * result.expected_severity
    result['illustrative_premium'] = result.pure_premium / (1 - expense_ratio)
    return result


def run(freq_path, sev_path, output_dir='outputs'):
    freq = pd.read_csv(freq_path)
    sev = pd.read_csv(sev_path)
    df = prepare_data(freq, sev)
    frequency, severity = fit_models(df)
    prices = predict_prices(df, frequency, severity)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    prices[['IDpol', 'expected_frequency', 'expected_severity', 'pure_premium',
            'illustrative_premium']].to_csv(out / 'policy_prices.csv', index=False)
    summary = pd.DataFrame([{
        'policies': len(df), 'exposure_years': df.Exposure.sum(),
        'observed_claims': df.ClaimNb.sum(), 'observed_paid_amount': df.ClaimAmount.sum(),
        'observed_frequency': df.ClaimNb.sum() / df.Exposure.sum(),
        'observed_severity': df.ClaimAmount.sum() / df.ClaimNb.sum(),
        'modelled_total_pure_premium': (prices.pure_premium * prices.Exposure).sum()
    }])
    summary.to_csv(out / 'pricing_summary.csv', index=False)
    (out / 'frequency_model.txt').write_text(str(frequency.summary()))
    (out / 'severity_model.txt').write_text(str(severity.summary()))
    print(summary.to_string(index=False))
    return prices


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--frequency', default='data/freMTPL2freq.csv')
    parser.add_argument('--severity', default='data/freMTPL2sev.csv')
    parser.add_argument('--output', default='outputs')
    args = parser.parse_args()
    run(args.frequency, args.severity, args.output)
