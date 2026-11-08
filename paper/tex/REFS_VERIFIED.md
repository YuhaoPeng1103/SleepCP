# Bibliography verification log

Checked 2026-11-08. Sources used: Crossref REST API (`api.crossref.org/works`),
DataCite API for arXiv DOIs, the arXiv Atom API, PMLR article pages, Europe PMC,
and publisher landing pages. Every DOI listed below was resolved through
Crossref (HTTP 200) or DataCite; no DOI was inferred from memory.

Counts: **26 keys checked — 20 VERIFIED, 6 CORRECTED, 0 NOT FOUND.** Two
entries that no longer support a sentence of the manuscript (`berry2012aasm`,
`mcaqn2025`) were removed from `refs.bib` after this check, which now holds the
25 entries the manuscript cites. Three time-series conformal-prediction
entries (`stankeviciute2021`, `xu2021`, `zaffran2022`) were added during the
2026-11-08 revision and are logged as VERIFIED (added) in the table, bringing
the bibliography to 28 entries.

| key | status | evidence | note |
|---|---|---|---|
| angelopoulos2021raps | VERIFIED | arXiv:2009.14193, author comment: "ICLR 2021 Spotlight, https://openreview.net/forum?id=eNdiU_DbM9" | ICLR has no DOI. OpenReview ID taken from the authors' own arXiv comment (openreview.net itself returned a bot challenge). |
| angelopoulos2023gentle | VERIFIED | https://doi.org/10.1561/2200000101 | Found. Trends Mach. Learn. 16(4):494–591, 2023. |
| barber2023 | VERIFIED | https://doi.org/10.1214/23-AOS2276 | Ann. Statist. 51(2):816–845, 2023. |
| bastani2022 | **CORRECTED** | https://proceedings.mlr.press/v235/ (PMLR 235:1616–1630); arXiv:2402.01139 | No Bastani et al. paper with this title exists. The paper described is by **Angelopoulos, Barber & Bates**, ICML **2024**, not ICML 2022. Key should be renamed. |
| berry2012aasm | VERIFIED | https://doi.org/10.5664/jcsm.2172 | J. Clin. Sleep Med. 8(5):597–619. **Scope caveat:** this is the *respiratory-event* rules update, not the sleep-stage rules. See action item 3. |
| chatterjee2026 | VERIFIED | https://doi.org/10.1007/978-3-032-30710-1_6 | Published: AIME 2026, LNCS, pp. 49–53. arXiv:2602.19483. **Number caveat:** abstract says "over 20 percentage points", the manuscript says "roughly 30". |
| conmil2025 | VERIFIED | https://doi.org/10.1007/s41666-025-00207-7 | J. Healthc. Inform. Res. 9(4):656–685, 2025. ConMIL = conformalized multiple-instance learning; sleep staging is one of two evaluation tasks, not a dedicated sleep pipeline. |
| cover2026 | VERIFIED | https://doi.org/10.48550/arXiv.2610.03911 | arXiv:2610.03911 (2 Oct 2026), 5 authors (Song, Deng, Yin, Mao, Hu). Preprint only — not peer reviewed. |
| gibbs2021 | VERIFIED | arXiv:2106.00170; NeurIPS 2021, vol. 34 | NeurIPS proceedings carry no DOI. |
| goldberger2000 | VERIFIED | https://doi.org/10.1161/01.CIR.101.23.e215 ; Europe PMC pageInfo `E215-20` | Circulation 101(23):e215–e220. |
| guo2017 | VERIFIED | https://proceedings.mlr.press/v70/guo17a.html | ICML 2017, PMLR 70:1321–1330. |
| kemp2000 | **CORRECTED** | https://doi.org/10.1109/10.867928 | The title "Analysis of a sleep dataset…" is not the published title. Correct title: "Analysis of a sleep-dependent neuronal feedback loop: the slow-wave microcontinuity of the EEG". IEEE TBME 47(9):1185–1194. |
| lawhern2018 | VERIFIED | https://doi.org/10.1088/1741-2552/aace8c | J. Neural Eng. 15(5):056013. |
| lei2018 | VERIFIED | https://doi.org/10.1080/01621459.2017.1307116 | JASA 113(523):1094–1111. |
| mcaqn2025 | **CORRECTED** | https://doi.org/10.1016/j.neucom.2025.132342 | Vol. 667, article 132342, issue dated **Feb 2026** (online 2025). Paper is about epileptiform-activity quantification; sleep staging is only an auxiliary sub-task. Weak support for the "sleep staging continues this line" sentence. |
| mfcr2025 | **CORRECTED** | https://doi.org/10.1016/j.neucom.2025.132399 | Vol. 668, article 132399, issue dated **Mar 2026** (online 2025). Genuine sleep-staging paper. |
| nettasinghe2023 | VERIFIED | https://proceedings.mlr.press/v202/nettasinghe23a.html | ICML 2023, PMLR 202:25890–25903. Matches the Markov-chain/de Finetti description in §2.4. |
| perslev2021 | **CORRECTED** | https://doi.org/10.1038/s41746-021-00440-5 | **No U-Time paper in Medical Image Analysis 2021 exists.** The 2021 fully-convolutional whole-night paper from this group is U-Sleep, npj Digit. Med. 4:72. If the original U-Time architecture was meant, cite NeurIPS 2019 (arXiv:1910.11162). |
| phan2019seqsleepnet | VERIFIED | https://doi.org/10.1109/TNSRE.2019.2896659 | IEEE TNSRE 27(3):400–410. |
| phan2022sleepformer | **CORRECTED** | https://doi.org/10.1109/TBME.2022.3147187 | Venue is **IEEE Trans. Biomedical Engineering**, not TNSRE. 69(8):2456–2467. |
| romano2020 | VERIFIED | arXiv:2006.02544; NeurIPS 2020, vol. 33 | NeurIPS proceedings carry no DOI. |
| rosenberg2013 | VERIFIED | https://doi.org/10.5664/jcsm.2350 | J. Clin. Sleep Med. 9(1):81–87. |
| stankeviciute2021 | VERIFIED (added 2026-11-08) | NeurIPS 2021, vol. 34, pp. 6216–6228; proceedings.neurips.cc paper hash 312f1ba2… | CopulaCPTS. NeurIPS proceedings carry no DOI. Checked against the DBLP record and the NeurIPS proceedings page. |
| supratak2017 | VERIFIED | https://doi.org/10.1109/TNSRE.2017.2721116 | Official title is "DeepSleepNet: A Model for Automatic Sleep Stage Scoring Based on Raw Single-Channel EEG"; IEEE TNSRE 25(11):1998–2008. |
| tibshirani2019 | VERIFIED | arXiv:1904.06019; NeurIPS 2019, vol. 32 | NeurIPS proceedings carry no DOI. |
| vovk2005 | VERIFIED | https://doi.org/10.1007/b106715 | Springer, Boston, MA, 2005 (monograph). |
| vovk2012 | VERIFIED | https://proceedings.mlr.press/v25/vovk12.html | ACML 2012, PMLR 25:475–490. |
| xu2021 | VERIFIED (added 2026-11-08) | https://proceedings.mlr.press/v139/xu21h.html | EnbPI; ICML 2021, PMLR 139:11559–11569. Pages confirmed against the PMLR page and DBLP. |
| zaffran2022 | VERIFIED (added 2026-11-08) | https://proceedings.mlr.press/v162/zaffran22a.html | ICML 2022, PMLR 162:25834–25866. |

## Action items for the author

**Status 2026-11-08: all six items are applied in the current manuscript**
(the key is `angelopoulos2024`; `perslev2021` cites U-Sleep; the AASM manual
entry `berry2012manual` is used for the stage rules; `mcaqn2025` was dropped;
the text says "over 20 coverage points"; `cover2026` is cited as a preprint).
The items are kept below as the record of what was wrong and why.

1. **`bastani2022` is misattributed.** The title "Online conformal prediction with
   decaying step sizes" belongs to Angelopoulos, Barber & Bates (ICML 2024,
   PMLR 235:1616–1630). There is no Bastani et al. paper by that title, and the
   paper was not at ICML 2022. The `refs_verified.bib` entry keeps the key but
   carries the correct authors/year, so the PDF will now read correctly; still,
   rename the key to `angelopoulos2024` and update the three call sites
   (`02_related.tex` §2.3, `03_background.tex` eq. region, `04_method.tex`).
   If a genuine Bastani citation was intended, the closest real work is
   Bastani et al., "Practical Adversarial Multivalid Conformal Prediction",
   NeurIPS 2022 — but it does not analyse step-size schedules.

2. **`perslev2021` points at a paper that does not exist** as described
   (U-Time, Medical Image Analysis 2021). Corrected to U-Sleep (npj Digital
   Medicine 4:72, 2021), which is fully convolutional and operates on the whole
   night, matching the sentence in §2.1. If the *architecture* U-Time is meant,
   use: Perslev, Jensen, Darkner, Jennum, Igel, "U-Time: A Fully Convolutional
   Network for Time Series Segmentation Applied to Sleep Staging", NeurIPS 2019
   (arXiv:1910.11162).

3. **`berry2012aasm` does not support the claim it is attached to.** In
   `05_setup.tex` it justifies merging R&K stage 4 into N3. The JCSM 2012 paper
   is the *respiratory event* rules update. For the stage rules use the manual
   itself: Berry, R. B., et al. (2012), *The AASM Manual for the Scoring of
   Sleep and Associated Events: Rules, Terminology and Technical
   Specifications*, Version 2.0, American Academy of Sleep Medicine, Darien, IL
   (no DOI), or Iber et al. (2007), Version 1.0.

4. **`mcaqn2025` is only tangentially a sleep-staging paper** (epileptiform
   activity quantification with a sleep-staging head). Consider dropping it
   from the "recent Neurocomputing work continues this line" sentence and
   keeping `mfcr2025`, which is a genuine sleep-staging model.

5. **`chatterjee2026` is now formally published** (AIME 2026, LNCS, pp. 49–53,
   DOI above), so it is no longer only an arXiv preprint. Check the "roughly 30
   coverage points" number against the paper: the abstract claims "over 20
   percentage points".

6. **`cover2026` is an arXiv preprint** (Oct 2026) with no peer-reviewed venue
   yet; cite it as such.

## Notes on what was deliberately left out

- `pages` is omitted for all NeurIPS entries (`gibbs2021`, `romano2020`,
  `tibshirani2019`). NeurIPS proceedings do not print authoritative page
  ranges; OpenAlex reports 33:3581–3591 for Romano and 32:2526–2536 for
  Tibshirani, but this could not be confirmed against the proceedings site,
  which blocked automated access. No page numbers were guessed.
- `pages` for journal articles is given only where Crossref/Europe PMC
  supplied it. Article-number venues (Neurocomputing, npj Digital Medicine,
  J. Neural Eng.) use the article number in `pages`.
- All 26 keys resolved to a real record; there are no NOT FOUND entries, so no
  substitute references are needed.

## Out-of-scope observation (resolved)

`04_method.tex` states that the schedule `$\gamma_t=\gamma_0/\sqrt{t+2}$`
violates the sufficient condition of \citet{angelopoulos2024} because
`$\sum_t\gamma_t=\infty$` and `$\sum_t\gamma_t^2=\infty$`. Both relations are
correct as written: `$\gamma_t^2=\gamma_0^2/(t+2)$`, whose sum diverges. An
earlier note in this log suggested the second should read `< \infty`; that
suggestion was wrong and has been removed. The manuscript and the corollary
below it are consistent: the corollary assumes the square-summable regime
(`$\sum_t\gamma_t^2<\infty$`), which the deployed schedule does not satisfy,
and the text says explicitly that no long-run guarantee is claimed for it.

## Added during the 2026-11-08 Neurocomputing-fit revision

| key | status | evidence | note |
|---|---|---|---|
| zhao2025pruning | VERIFIED | https://doi.org/10.1016/j.neucom.2024.128704 ; Crossref `api.crossref.org/works/10.1016/j.neucom.2024.128704` | Neurocomputing 611:128704, Jan 2025. Authors Xindi Zhao, Amin Farjudian, Anthony Bellotti; metadata read from the Crossref record, not from memory. |
| li2026mfcr | VERIFIED | https://doi.org/10.1016/j.neucom.2025.132399 ; Crossref `api.crossref.org/works/10.1016/j.neucom.2025.132399` | Neurocomputing 668:132399, Mar 2026. Authors Bohan Li, Songyun Xie, Xinzhou Xie, Hao Tang, Michael Scholz, Zhili Zhang, Zhongyu Tian; metadata read from Crossref. |

## Added during the 2026-11-08 Biomedical Signal Processing and Control retarget

The two Neurocomputing entries above remain in `refs.bib`; `zhao2025pruning` is
still cited (CP as a design target), `li2026mfcr` is no longer cited and is
therefore not printed in the bibliography. The staging literature is now cited
from the target journal.

| key | status | evidence | note |
|---|---|---|---|
| zhou2026bspc | VERIFIED | https://doi.org/10.1016/j.bspc.2025.108623 ; Crossref `api.crossref.org/works/10.1016/j.bspc.2025.108623` | BSPC 112:108623, Feb 2026. Authors Huihui Zhou, Aiping Liu, Heng Cui, Feng Wan, Yanyan Wang, Xun Chen; metadata read from the Crossref record. |
| fan2025bspc | VERIFIED | https://doi.org/10.1016/j.bspc.2025.108084 ; Crossref `api.crossref.org/works/10.1016/j.bspc.2025.108084` | BSPC 110:108084, Dec 2025. Authors Jingxin Fan, Mingfu Zhao, Lurui Wang, Bin Tang, Jingchuan Lu, Zhong He, Li Huang; metadata read from Crossref. |
| hatamoto2025 | VERIFIED | https://doi.org/10.1016/j.bspc.2025.107947 ; Crossref `api.crossref.org/works/10.1016/j.bspc.2025.107947` | BSPC 109:107947, Nov 2025. Authors Miyari Hatamoto, Akira Furui, Keiko Ogawa, Toshio Tsuji; metadata read from Crossref. |

## Added during the final 2026-11-08 journal-format revision

The final manuscript cites **36 unique references**. The five additions below
were resolved through the Crossref REST API before insertion.

| key | status | DOI and Crossref metadata |
|---|---|---|
| li2021endtoend | VERIFIED | https://doi.org/10.1016/j.bspc.2020.102203 ; BSPC 63:102203, 2021. Authors Fan Li, Rui Yan, Reza Mahini, Lai Wei, Zhiqiang Wang, Klaus Mathiak, Rong Liu, Fengyu Cong. |
| yang2021hmm | VERIFIED | https://doi.org/10.1016/j.bspc.2021.102581 ; BSPC 68:102581, 2021. Authors Bufang Yang, Xilin Zhu, Yitian Liu, Hongxing Liu. |
| sarkar2022evaluation | VERIFIED | https://doi.org/10.1016/j.bspc.2022.103819 ; BSPC 77:103819, 2022. Authors Debanjan Sarkar, Dwaipayan Guha, Puspal Tarafdar, Shusovan Sarkar, Antara Ghosh, Debangshu Dey. |
| heremans2024upass | VERIFIED | https://doi.org/10.1016/j.compbiomed.2024.108205 ; Computers in Biology and Medicine 171:108205, 2024. Authors Elisabeth R. M. Heremans, Nabeel Seedat, Bertien Buyse, Dries Testelmans, Mihaela van der Schaar, Maarten De Vos. |
| vangorp2022certainty | VERIFIED | https://doi.org/10.1093/sleep/zsac134 ; Sleep 45(8):zsac134, 2022. Authors Hans van Gorp, Iris A. M. Huijben, Pedro Fonseca, Ruud J. G. van Sloun, Sebastiaan Overeem, Merel M. van Gilst. |
