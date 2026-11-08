# Experimental protocol

## Datasets

| Dataset | Use | Subjects | Notes |
|---|---|---|---|
| Sleep-EDF-20 (SC400-SC419) | main | 20 | 39 recordings, 42,368 epochs, 42,307 labelled |
| Sleep-EDF-78 (SC400-SC482) | extended cohort | 78 | 153 recordings, 195,767 epochs, 195,469 labelled |
| Sleep-EDF telemetry (ST700-ST721) | cross-cohort shift | 22 | 44 recordings, different hardware and cohort |
| Corrupted Sleep-EDF-20 | robustness ablation | 20 | noise, gain, baseline drift, clock shift, dropout |

Preprocessing: Fpz-Cz, bandpass 0.5-30 Hz, 30 s epochs, per-recording z-score,
epoch label assigned by >=50% overlap with the scored annotation. R&K stage 4
is merged into N3 (AASM). Each recording is cropped to the scored sleep period
plus 30 minutes of wake on either side: keeping every annotated epoch instead
yields a 65%-wake cohort of 112k annotated epochs, which matches no published result and
distorts the class priors. The crop reproduces the canonical Sleep-EDF-20
cohort: 42,307 labelled epochs, 19.6% W, 6.6% N1, 42.1% N2, 13.5% N3, 18.2% REM.

## Splits

- **Subject-wise 5-fold.** The 20 subjects are shuffled once into 5 blocks of
  4. Fold `f` tests on block `f`, calibrates on 4 of the remaining 16, and
  trains on the other 12. Test blocks partition the cohort, so every subject
  contributes exactly one test set across the five folds. Calibration
  subjects rotate across folds.
- **Random-epoch split** (diagnostic only): 60/20/20 train/cal/test epochs at
  random. Leaks subject identity; used to show why the common protocol hides
  the problem.
- **Cross-cohort**: train+calibrate on SC subjects, test on ST subjects, and
  vice versa. No subject overlap in either direction.

## Models

- `eegnet`: EEGNet-style depthwise-separable CNN, 1,445 parameters.
- `sleepcnn`: four-block VGG-style 1D CNN with global average pooling, 224,069
  parameters.

Trained with AdamW (lr 1e-3, wd 1e-4), cosine schedule, batch 128, 40 epochs,
early stopping on held-out training subjects, plain cross-entropy without
class weights in every run. Class weighting trades N1 recall against the
calibration of the output distribution, so one setting is used throughout and
recorded in each run's JSON.

3 seeds (0, 1, 2) x 5 folds x 2 models = 30 runs for the main table. The
3-seed spread is reported as the uncertainty on every headline number.

## Conformal methods

All calibrated on calibration subjects only, at alpha = 0.1 unless stated.

| Name | Score | Threshold | Guarantee |
|---|---|---|---|
| `global` | APS | pooled split CP | marginal |
| `class_conditional` | APS | Mondrian per class | class-conditional |
| `sacp_m*` | APS | per-subject warm-up, shrink | percept-subject under A1 |
| `smooth_sacp_m*` | APS of forward-backward posterior | per-subject warm-up, shrink | per-subject under A1 |
| `nbr_k*_shrink*` | APS | kNN subject pool, shrink | approximate |
| `aci` | APS | online update | long-run |
| `seqcp_epoch` | APS of posterior | pooled split CP | marginal |
| `per_epoch_deficit_mondrian` | deficit of posterior | Mondrian per stage | class-conditional |
| `seqcp_margin_L*_beta*` | DP margin, deficit score | pooled split CP | marginal |
| `seqcp_block_L*_beta*` | block mean APS + beta * transition | block split CP | simultaneous over block |
| `oracle_subject` | APS | per-subject on test labels | not deployable |

## Metrics

- **Coverage**: marginal, per-class, mean/worst/p10 subject, fraction of
  subjects below `1 - alpha`.
- **Efficiency**: mean set size, singleton rate, empty rate, review workload
  (fraction of epochs with |C| > 1).
- **Temporal**: mean adjacent-set Jaccard within a recording, sequence
  coverage (all epochs of a block covered).
- **Classification**: accuracy, Cohen's kappa, macro-F1, per-class F1, ECE.

Headline numbers are computed by merging per-subject coverage across all five
folds (20 subjects) and then averaging each subject's value over the seeds and
backbones that re-run the same partition, not by averaging fold-level
statistics. `scripts/paired_tests.py`
runs the paired per-patient comparison the paper quotes: within each seed the
folds are merged, the per-seed values are averaged per subject, and a two-sided
Wilcoxon signed-rank test is applied to coverage (and to the absolute
deviation from nominal, which is the statistic that matters for spread reduction).

## Analyses

1. **The coverage gap.** Random-epoch vs subject-wise; per-class and
   per-subject coverage distributions. (Sec. 5.1)
2. **Coverage vs label budget.** SACP for m in {0,10,20,40,80,160,320}, with
   lambda selected by LOSO. The selection is unstable at four calibration
   subjects (all five grid values are selected in different runs, and lambda
   is 0 at every budget up to m = 80 in most runs); the fixed-lambda sweep in
   `scripts/sacp_fixed_lambda.py` shows that the failure is not only the
   selection: at m = 20 every positive weight lowers the worst patient sharply,
   at m = 160 the best weight gains at most two and a half points over the
   pooled threshold, and at m = 320 the ordering reverses. Reported as a
   negative result, not a contribution. (Sec. 5.3, Figs. 2-3)
3. **Coverage vs calibration cohort size.** `scripts/run_cohort_size.py`:
   subsample k calibration subjects, refit the pooled threshold, repeat 50
   times per run, for the APS and deficit scores. 20-subject cohort gives
   k in {1,2,3,4} (the script accepts any k up to the number of calibration
   subjects, which is 16 in the 78-subject cohort; only the 20-subject sweep
   is reported). (Sec. 5.3,
   Table `tab:cohort-size`)
4. **Efficiency-reliability plane.** Worst-patient coverage against mean set
   size along the warm-up budget, with the pooled and oracle anchors. (Sec.
   5.3, Fig. 2)
5. **Temporal.** L in {10,20,30}, beta in {0,0.5,1,2}; consistency,
   sequence coverage, and the block-guarantee check. Includes the
   stage-conditional (Mondrian) threshold on the deficit score, which restores
   every stage to nominal coverage at 1.74 labels per epoch. (Sec. 5.5,
   Fig. 5; per-stage table `tab:perclass`)
6. **Ablations.** beta, L, transition source (cal labels vs uniform),
   score family (APS vs deficit), smoothing on/off. (Sec. 5.5)
7. **Robustness.** Cross-cohort SC<->ST (`scripts/train_cross_cohort.py`
   then `scripts/run_cross_matrix.sh`), the ACI step-schedule check
   (`scripts/run_aci_schedule_check.sh`), and corrupted inputs
   (`scripts/run_shift.py`). The schedule check re-runs per-patient ACI on the
   fitted models with the theory-compliant power schedule
   `gamma_t = gamma0/(t+2)^0.6` (which satisfies both sum gamma = infinity and
   sum gamma^2 < infinity) instead of the default `gamma0/sqrt(t+2)`, so that
   the reported improvement cannot be attributed to a schedule outside the
   condition the long-run bound assumes. Its summary is written to
   `results/schedule/main/summary`, next to the main summary rather than
   inside it, because it re-analyses the same fitted models under a second
   schedule; the cross-cohort summaries likewise live under
   `results/cross/*/summary`. Corruption families applied to the *test*
   signals with a clean calibration set: additive white noise (SNR
   30/20/10/5/0 dB), gain (0.5/0.75/1.25/1.5), baseline wander (amplitude
   0.25/0.5/1/2 SD), circular time shift (0.5/1/2/5 s), and epoch dropout
   (2/5/10/20%). Each level reports three thresholds: the clean one, one
   refitted on identically corrupted calibration signals, and per-patient ACI
   adapted on the corrupted stream. Accuracy is recorded alongside, and set
   sizes for the recalibrated threshold and for ACI, so that restored coverage
   on a broken model is not read as a restored model. (Sec. 5.6, Tables
   `tab:shift` and `tab:corruption`)
8. **Extended cohort.** The same subject-wise 5-fold matrix on Sleep-EDF-78
   (78 subjects, 153 recordings, 195,469 labelled epochs), seed 0 only, two
   backbones, ten runs. The test block is 15 or 16 subjects and the
   calibration block 16, so every per-patient statistic is estimated on four
   times the main cohort. `DATA=data/processed/sleep-edf-78 ROOT=results/se78
   bash scripts/run_matrix.sh "eegnet sleepcnn" "0"`. Ordering of methods is
   unchanged; the pooled-to-per-patient gap is larger, and the per-patient SD
   is larger too, which does not depend on taking a minimum over more
   patients. (Sec. 5.7, Table `tab:extended`)
