"""
Bayesian Project Estimation
============================
Uses historical project duration data to form conjugate Normal-Inverse-Gamma
priors for each project size category (small / medium / large). As we
"observe" the PERT likely-estimate for each new project, the posterior
distribution updates and sharpens.

Key outputs:
- Posterior mean and credible intervals for each project's duration
- How the posterior evolves as more data is incorporated
- Violin / box-plot-ready samples from the posterior predictive distribution
- Monthly utilisation derived from posterior mean durations
"""

import numpy as np
from scipy import stats

# ── Bayesian engine (Normal-Inverse-Gamma conjugate model) ────────────────

class NormalInverseGamma:
    """
    Conjugate prior for unknown mean and variance of a Normal distribution.

    Parameterised by (mu_0, nu, alpha, beta) where:
        mu_0  = prior mean
        nu    = pseudo-observation count for the mean
        alpha = shape  (precision prior)
        beta  = scale  (precision prior)

    After observing data x_1..x_n with sample mean x_bar and sum-of-squares S:
        mu_0  -> (nu * mu_0 + n * x_bar) / (nu + n)
        nu    -> nu + n
        alpha -> alpha + n/2
        beta  -> beta + S/2 + (n * nu * (x_bar - mu_0)^2) / (2*(nu + n))
    """

    def __init__(self, mu_0, nu, alpha, beta):
        self.mu_0 = mu_0
        self.nu = nu
        self.alpha = alpha
        self.beta = beta

    def update(self, data):
        """Return a new NIG posterior given observed data."""
        data = np.asarray(data, dtype=float)
        n = len(data)
        if n == 0:
            return NormalInverseGamma(self.mu_0, self.nu, self.alpha, self.beta)

        x_bar = data.mean()
        S = np.sum((data - x_bar) ** 2)

        nu_n = self.nu + n
        mu_n = (self.nu * self.mu_0 + n * x_bar) / nu_n
        alpha_n = self.alpha + n / 2.0
        beta_n = (
            self.beta
            + S / 2.0
            + (n * self.nu * (x_bar - self.mu_0) ** 2) / (2.0 * nu_n)
        )
        return NormalInverseGamma(mu_n, nu_n, alpha_n, beta_n)

    def posterior_predictive_samples(self, size=5000):
        """
        Draw from the posterior predictive (a Student-t distribution).
        """
        df = 2 * self.alpha
        loc = self.mu_0
        scale = np.sqrt(self.beta * (self.nu + 1) / (self.alpha * self.nu))
        return stats.t.rvs(df=df, loc=loc, scale=scale, size=size)

    def credible_interval(self, level=0.9):
        """Return (lower, upper) symmetric credible interval."""
        df = 2 * self.alpha
        loc = self.mu_0
        scale = np.sqrt(self.beta * (self.nu + 1) / (self.alpha * self.nu))
        tail = (1 - level) / 2
        lower = stats.t.ppf(tail, df=df, loc=loc, scale=scale)
        upper = stats.t.ppf(1 - tail, df=df, loc=loc, scale=scale)
        return float(lower), float(upper)


def _build_prior(historical_data):
    """
    Build a weakly-informative NIG prior from historical durations.
    Uses the empirical mean/variance as starting points with moderate
    pseudo-counts so the prior is influential but not dominant.
    """
    data = np.asarray(historical_data, dtype=float)
    mu_0 = data.mean()
    nu = 2.0  # weak: equivalent to 2 prior observations
    alpha = 2.0
    beta = data.var() * alpha  # sets prior expected variance ≈ sample variance
    return NormalInverseGamma(mu_0, nu, alpha, beta)


# ── adapter / public API ──────────────────────────────────────────────────

def run(projects, resource_capacities, historical_durations,
        planning_horizon_months=12, n_samples=5000):
    """
    Run Bayesian estimation on the shared dataset.

    Steps:
    1. Build NIG priors from historical_durations for each size category.
    2. For each project, update the prior with the project's PERT likely
       estimate (treated as a single new observation).
    3. Draw posterior predictive samples → credible intervals.

    Returns
    -------
    dict with keys:
        project_results : list of per-project dicts
            name, posterior_mean, ci_90 (tuple), ci_50, samples
        timeline : list of (name, start_month, duration_months, ci_low, ci_high)
        monthly_utilisation / monthly_utilisation_pct
    """
    weeks_per_month = 4.33

    # Step 1: build priors per size category
    priors = {}
    for size, data in historical_durations.items():
        priors[size] = _build_prior(data)

    project_results = []
    timeline = []

    for proj in projects:
        size = proj["type"]
        prior = priors[size]

        # Step 2: update with this project's likely estimate as a single observation
        # In practice you'd update with actual completed project data over time;
        # here we simulate "having seen" the likely estimate.
        observation = [proj["duration_likely_weeks"]]
        posterior = prior.update(observation)

        # Step 3: posterior predictive
        samples = posterior.posterior_predictive_samples(size=n_samples)
        # Clip negative durations (rare but possible with wide priors)
        samples = np.clip(samples, 1.0, None)

        ci_90 = posterior.credible_interval(0.90)
        ci_50 = posterior.credible_interval(0.50)
        post_mean = posterior.mu_0

        project_results.append({
            "name": proj["name"],
            "posterior_mean": float(post_mean),
            "ci_90": (max(1.0, ci_90[0]), ci_90[1]),
            "ci_50": (max(1.0, ci_50[0]), ci_50[1]),
            "samples": samples,
        })

        # Timeline entry
        start = proj["earliest_start_month"]
        dur_m = post_mean / weeks_per_month
        ci_lo = max(1.0, ci_90[0]) / weeks_per_month
        ci_hi = ci_90[1] / weeks_per_month
        timeline.append((proj["name"], start, dur_m, ci_lo, ci_hi))

    # Monthly utilisation (use posterior mean durations, spread resource_profile)
    monthly_util = {r: [0.0] * planning_horizon_months for r in resource_capacities}
    for proj, res in zip(projects, project_results):
        start = proj["earliest_start_month"]
        profile = proj["resource_profile"]
        # Scale the profile to the posterior mean duration
        original_months = max(len(v) for v in profile.values())
        posterior_months = max(1, round(res["posterior_mean"] / weeks_per_month))
        scale = posterior_months / original_months if original_months > 0 else 1

        for resource, monthly_needs in profile.items():
            for offset, need in enumerate(monthly_needs):
                # Scale the offset by the duration ratio
                scaled_offset = round(offset * scale)
                month = start + scaled_offset
                if 0 <= month < planning_horizon_months:
                    monthly_util[resource][month] += need

    monthly_util_pct = {}
    for resource, months in monthly_util.items():
        cap = resource_capacities[resource]
        monthly_util_pct[resource] = [m / cap * 100 for m in months]

    return {
        "project_results": project_results,
        "timeline": timeline,
        "monthly_utilisation": monthly_util,
        "monthly_utilisation_pct": monthly_util_pct,
    }
