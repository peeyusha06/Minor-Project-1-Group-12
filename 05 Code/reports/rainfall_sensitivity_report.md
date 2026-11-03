# Rainfall Sensitivity Report — flagged Pune (and other) IMD values

Script: `src/s14_rainfall_sensitivity.py`. Primary outputs and `config/project_decisions.yaml` are **unchanged**
(`rainfall_extreme_values.active` is still `keep`). Everything here is a sensitivity check.

Outputs:
- `data/interim/sensitivity/climate_features_<scenario>.csv`: rainfall features recomputed after removing flagged years
- `data/interim/sensitivity/pca_input_<scenario>.csv`: Set A input (same layout as `pca_input_primary.csv`)
- `data/processed/sensitivity/<scenario>/pca_*.csv`: PCA and leave-one-district-out, same layout as step 13
- `data/processed/sensitivity/rainfall_sensitivity_comparison.csv`: primary vs sensitivity, item by item
- `data/processed/sensitivity/rainfall_sensitivity_dropped_district_years.csv`: which district-years were removed

## 1. What was done

The pipeline already flags a district-year as "implausibly high" when June–September rainfall is more than 2 × the
district's 1971–2020 baseline. Pune has two such years: **2005 (4.87 × baseline) and 2009 (2.03 ×)**.

Main scenario, `pune_excluded`: Pune's 2005 and 2009 values are removed from Pune's rainfall calculations. The
following are then recomputed from the remaining 73 years:
- the 1971–2020 baseline
- every year's departure
- the deficient flag (departure ≤ −20%, unrounded)
- SPI
- the El Niño deficient frequency, worst El Niño deficit and ENSO–rainfall slope

The published IMD values are not edited, and no other district changes.

Broader scenario, `all_flagged_excluded`: the same treatment for all 10 flagged high district-years in Maharashtra.
These are Pune 2005 and 2009, Jalgaon, Buldhana, Jalna, Chhatrapati Sambhajinagar and Solapur 1962, Nanded 1988, and
Ahilyanagar and Satara 2005.

Neither Pune year is a RONI El Niño monsoon year. The effect therefore comes from **the baseline**: the two very wet
years inflate Pune's "normal" rainfall, so ordinary years look like deficits.

## 2. What changed for Pune

| Pune | Published data (primary) | Flagged years removed |
|---|---|---|
| Years used | 75 | 73 |
| 1971–2020 baseline (mm) | 867.5 | 778.9 (−10.2%) |
| Monsoon CV (%) | 59.1 (next highest district ≈ 33) | 33.7 |
| El Niño deficient frequency | 0.722 (13 of 18 El Niño years) | 0.611 (11 of 18) |
| Mean deficit in El Niño years (%) | 21.0 | 12.0 |
| Non-El Niño deficient frequency | 0.368 | 0.291 |
| ENSO–rainfall slope (% per °C) | −7.89 | −8.75 |
| Rank of Pune on deficient frequency (34 districts) | 1st (z = 3.62) | **still 1st** (z = 2.98; next district 0.444) |

## 3. What changed in the PCA

| Check | Primary | `pune_excluded` | `all_flagged_excluded` |
|---|---|---|---|
| Explained variance PC1 / PC2 / PC3 | 34.3 / 20.8 / 19.4% | 34.7 / 20.8 / 19.4% | 34.5 / 21.0 / 19.4% |
| Same-component cosine PC1 / PC2 / PC3 | — | 0.995 / 0.994 / 0.999 | 0.994 / 0.993 / 0.999 |
| District-score correlation PC1 / PC2 / PC3 | — | 0.997 / 0.992 / 0.998 | 0.995 / 0.990 / 0.999 |
| Deficient-frequency loading on PC1 | 0.19 | 0.32 | 0.34 |
| Pune score on PC2 | 3.57 | 3.15 | 3.21 |
| Largest score change for any other district | — | 0.25 | 0.43 |
| LOO: minimum PC1 cosine (always when Pune is omitted) | 0.948 | 0.974 | 0.974 |
| LOO: runs in which PC2/PC3 swap order | 2 (Pune, Ratnagiri) | 1 (Pune) | 1 (Pune) |
| LOO: minimum projection of PC2 on the PC2–PC3 plane | 0.926 | 0.959 | 0.958 |

The component order, the major loadings and their signs are all unchanged. The only visible shift is that deficient
frequency moves a little towards PC1 (0.19 → 0.32). This is the same direction as when Pune is left out altogether,
but much smaller.

## 4. Conclusion

1. **The flagged Pune values do not materially change the PCA structure.** The same three components come out, in
   the same order, with the same meaning, and they are as stable as before (slightly more stable, in fact).
2. **They do change Pune's own inputs moderately.** Pune's deficient frequency falls from 0.72 to 0.61 and its
   baseline by 10%.
3. **Pune remains an outlier after the correction.** It is still first on deficient frequency by a wide margin
   (0.61 vs 0.44), still dominates PC2, and is still the most influential district in the leave-one-out check. So the
   two flagged years explain only part of Pune's unusual position.
4. **Possible reason (NOT VERIFIED):** Pune's series has a run of wet years, 2004–2009, at 1.58, 4.87, 1.97, 1.58,
   1.32 and 2.03 × baseline. Only 2005 and 2009 cross the 2 × flag; 2006 is just below it. Whether this run is real
   (the district includes very wet Western Ghats talukas) or an artefact of the gridded product could not be checked.
   IMD's district rainfall statistics site (hydro.imd.gov.in) returned 404 during data acquisition, so no independent
   published district series is available in this project.
5. The broader `all_flagged_excluded` scenario gives the same picture. Its largest effect on a non-Pune district is a
   score change of 0.43 on PC1.

**Implication for the index work:** keep the published values as the primary treatment (the config is unchanged).
Report `pune_excluded` as a sensitivity result, and repeat every candidate index with and without the Pune
correction (done in `reports/pca_weighting_methods_report.md`, section 7). Whether to adopt a different rule, such as
a lower flag ratio or a median-based baseline, is a team/guide decision. It must not be chosen according to which
district ordering it produces.
