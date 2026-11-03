# PCA Stability Report — leave-one-district-out

Script: `src/s13_pca_primary.py`. Output: `data/processed/pca_leave_one_out.csv` (one row per omitted district).

## 1. What was done

The primary PCA (34 districts, 6 direction-aligned variables) was repeated 34 times, each time leaving out one district. In each run the standardisation (StandardScaler) was also refitted, so each run is a complete re-analysis of 33 districts. Each run was compared with the full 34-district PCA:

- **Explained variance ratios** of PC1–PC6.
- **Loading similarity:** |cosine| between the full component's weights and the same-numbered component in the leave-one-out run (1 = identical direction; the sign is ignored because signs are arbitrary).
- **Order change:** whether the full component matched a *different*-numbered component better (e.g. full PC2 most similar to leave-one-out PC3).
- **Major-loading pattern:** "major" means |weight| ≥ 0.4, which is about the size an equal share would have (1/√6 = 0.41). For each run the script checks whether any major variable flips sign, and whether the set of major variables changes.
- **PC2–PC3 plane:** PC2 and PC3 have close eigenvalues (1.25 vs 1.17), so the check also asks whether the *plane* they span stays the same even if their order changes. This is measured as the length of the projection of full PC2 (and PC3) onto the leave-one-out PC2–PC3 plane; 1 means the component lies entirely in that plane.

## 2. Results

### Explained variance

| Component | Full PCA | Range across the 34 runs |
|---|---|---|
| PC1 | 34.3% | 33.1% – 36.8% |
| PC2 | 20.8% | 20.1% – 22.8% |
| PC3 | 19.4% | 17.5% – 20.3% |

The share of variance explained barely changes.

### Component directions

| | PC1 | PC2 | PC3 |
|---|---|---|---|
| Median \|cosine\| with full PCA | 0.999 | 0.994 | 0.992 |
| Minimum \|cosine\| | 0.948 (Pune omitted) | 0.426 (Pune omitted) | 0.418 (Pune omitted) |
| Runs where the order changed | 0 | 2 (Pune, Ratnagiri) | 2 (Pune, Ratnagiri) |
| Runs where a major loading flipped sign | 0 | 2 (Ratnagiri, Sindhudurg) | 1 (Pune) |
| Runs where the set of major loadings changed | 1 (Pune) | 10 | 18 |
| Projection onto the leave-one-out PC2–PC3 plane (min / median) | — | 0.926 / 0.999 | 0.978 / 0.999 |

### Influential districts

- **Pune** has the largest effect. Without it, PC2 and PC3 swap and their compositions change. PC1 stays very similar (cosine 0.95), but El Niño deficient frequency moves into PC1: its weight rises from 0.13 to 0.43, while literacy's weight falls just below 0.4. So Pune's unusual combination is what keeps deficient frequency off the main PC1 axis: a very high deficient frequency, without the other dry-interior characteristics. That high frequency is partly linked to the suspect IMD rainfall values.
- **Ratnagiri** (and, to a lesser extent, **Sindhudurg** and **Ahilyanagar**) mainly change how the variance is split between PC2 and PC3 (cosines 0.70–0.83).

## 3. Interpretation (without over-reading the numbers)

- **PC1 is stable.** It keeps its direction (median cosine 0.999), its order and the signs of its major loadings when any single district is removed. Its description in the PCA report ("dryland agrarian interior vs coastal/eastern smallholder districts", with small-holding share loading opposite to the other strong variables) does not depend on one district.
- **PC2 and PC3 are not separately stable, but the plane they span is.** Their eigenvalues are close, so removing Pune or Ratnagiri reorders or mixes them. Even then, both full components still lie almost entirely within the new PC2–PC3 plane (projection ≥ 0.93). They should be read together as a pair, and the exact wording of each one individually should be treated as provisional.
- **Many "major set" changes are threshold effects.** Several PC2 and PC3 weights sit near the 0.4 cut-off (e.g. PC3 small holding −0.39, PC2 ENSO slope 0.30), so small shifts move them across the line. They should not be read as real changes in meaning.
- **Small-sample caution.** With 34 districts, this check shows how much the result depends on single districts. It cannot show whether the pattern would hold for a different set of regions, or with better rainfall data.

## 4. What this means for the next stage

- Any use of PC1 is on reasonably firm ground as far as sensitivity to single districts goes. Its mixed vulnerability directions remain a *conceptual* issue (PCA report, section 9).
- Any use of PC2 or PC3 should treat them as a pair, and should be checked with and without Pune. The Pune rainfall question (IMD values kept as published in the primary analysis) directly affects this part of the structure.
- No index, ranking or clustering has been produced.
