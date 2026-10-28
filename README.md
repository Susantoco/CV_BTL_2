# CV BTL2 — Gradient Domain Editing & Panoramic Image Stitching

Shared repository for all 3 parts of the assignment (see `docs/CV-project-2.pdf`
and `docs/HD-BTL-CV.pdf` for the original assignment and the course's general
report guidelines).

## Task assignment & ownership

| Part | Content | Main code directory | Owner |
|---|---|---|---|
| 1 | Gradient Domain Editing (Poisson blending) | `src/gradient_domain/` | Tri Pham Thanh |
| 2 | Core stitching pipeline + SIFT | `src/stitching/` | Khiem Ton Vo Hoai |
| 3 | Part 2 pipeline + ORB/SURF + comparison | `src/stitching/` (only changes `--detector`) | Khoa Nguyen Dang |

**Important for Parts 2 & 3:** both share the same pipeline
(`src/stitching/pipeline.py`). Part 2 builds this pipeline and runs it with
SIFT; Part 3 **does not rewrite the pipeline**, it only passes
`--detector orb` (or adds a new detector to `detectors.py`) and reruns. If
Part 3 needs to modify `pipeline.py` for ORB to work correctly, that means
the pipeline is not actually detector-agnostic — this should be reported back
to Part 2 to fix in the shared code rather than forked separately.

> **Note on SURF:** the current OpenCV build (standard `opencv-python`, not
> the `nonfree` build of `opencv-contrib-python`) does not include
> `cv2.xfeatures2d`, so SURF **cannot run** unless OpenCV is built from source
> with the `OPENCV_ENABLE_NONFREE` flag. `detectors.py` still declares
> `SURFDetector` but raises a clear error if called. The assignment only
> requires **at least 2 methods** — SIFT + ORB is sufficient. If SURF is
> still desired, an older `opencv-contrib-python` version (<4.3, before SURF
> was patent-locked out of the free build) needs to be installed, or built
> from source.

## Directory structure

```
BTL2/
├── docs/                          # Original assignment + course guidelines (do not modify)
├── data/
│   ├── gradient_domain/
│   │   ├── raw/                   # Real background/source photos — fish.jpg (source), water.jpg (background)
│   │   ├── mask/                  # Masks matching images in raw/, drawn with mask_tool.py — fish.png
│   │   └── edgecase/              # Synthetic test sets for the Poisson algorithm — already included
│   └── stitching/
│       ├── sample_synthetic/      # Synthetic image set to validate the pipeline before real photos are available
│       ├── member2_set/           # <-- Self-captured photo set for Part 2
│       └── member3_set/           # <-- Self-captured photo set for Part 3
├── src/
│   ├── gradient_domain/           # PART 1 — Poisson blending
│   │   ├── io_utils.py            # Image read/write, float [0,1] <-> uint8 normalization
│   │   ├── mask_tool.py           # Interactive mouse-based mask drawing tool (polygon)
│   │   ├── naive_blend.py         # Direct copy-paste blending — baseline for comparison
│   │   ├── poisson_blend.py       # Poisson/gradient-domain blending algorithm (core)
│   │   ├── generate_synthetic.py  # Generates synthetic background/source/mask images for testing before real photos exist
│   │   └── run_pipeline.py        # CLI: runs naive + poisson, outputs a side-by-side comparison image
│   └── stitching/                 # PARTS 2 + 3 — shared
│       ├── detectors.py           # Detector registry (SIFT/ORB/SURF) — the ONLY place to edit to add/change methods
│       ├── pipeline.py            # Detector-agnostic pipeline: preprocess -> match -> homography -> warp -> blend
│       ├── metrics.py             # Collects comparison metrics (keypoint count, inlier ratio, reprojection error, timing)
│       ├── generate_synthetic_scene.py  # Generates a multi-view synthetic image set to validate the pipeline
│       └── run_stitch.py          # CLI: python -m src.stitching.run_stitch --images ... --detector sift|orb
├── results/                        # Intermediate image/report output (gitignored, reproducible by rerunning)
│   ├── gradient_domain/
│   └── stitching/
├── report/                         # Drafted content for each shared report section (2.1 → 3)
│   ├── section_2_1_gradient_theory.md     # Written by Part 1
│   ├── section_2_2_stitching_theory.md    # Written by Part 2 (pipeline theory)
│   ├── section_2_2_stitching_results.md   # Written by Part 3 (experimental comparison table)
│   ├── section_3_gradient_analysis.md     # Written by Part 1
│   ├── section_3_stitching_analysis.md    # Written jointly by Parts 2+3
│   └── figures/                           # Illustrations inserted into the final LaTeX/PDF report
├── notebooks/                      # (optional) Colab notebook for demo/PDF export
├── requirements.txt
└── .gitignore
```

## Environment setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```

Verified on the shared environment: `opencv-python 4.13`, SIFT and ORB run
out-of-the-box (no `opencv-contrib-python` required).

## Usage — Part 1 (Gradient Domain Editing)

```bash
# 1. (once) generate synthetic edge-case images to test the algorithm before real photos exist
python -m src.gradient_domain.generate_synthetic

# 2. draw an interactive mask on the source image (outlines the object to cut out)
#    left click: add polygon point, right click: undo point, c: close polygon, s: save, q: quit
python -m src.gradient_domain.mask_tool --source data/gradient_domain/raw/fish.jpg --out data/gradient_domain/mask/fish.png

# 3. run blending + compare naive vs Poisson
python -m src.gradient_domain.run_pipeline \
    --background data/gradient_domain/raw/water.jpg \
    --source data/gradient_domain/raw/fish.jpg \
    --mask data/gradient_domain/mask/fish.png \
    --offset 300 100 \
    --out results/gradient_domain/real_compare.png
```

Current real data set: `raw/fish.jpg` is the source (a fish, cut out via
`mask/fish.png`), `raw/water.jpg` is the background it gets pasted into.
`--offset 300 100` places the fish inside the underwater region of
`water.jpg` (image is 436x640, fish crop is 218x129) — adjust the two
numbers (`OY OX`, top-left corner in pixels) if a different position is
wanted. The command above produces `results/gradient_domain/real_compare.png`
(side-by-side background/source/naive/Poisson) plus the two individual
results `real_compare_naive.png` and `real_compare_poisson.png`.

`generate_synthetic.py` produces 3 verified test sets under `edgecase/`,
usable right away for the report regardless of real photos:

| Image set | Purpose |
|---|---|
| `edgecase/{background,source,mask}.png` | Main demo: source/target backgrounds share the same blue tone but differ in brightness → naive paste shows a clear seam, Poisson blending removes the seam while preserving the object's color |
| `edgecase/mask_loose.png` (used in place of `mask.png`) | A mask much larger than the object → illustrates the effect of mask size (section 2.5): the looser the mask, the more flat background gets pulled into the solved region, which can leave a visible edge/halo |
| `edgecase/challenging/{background,source,mask}.png` | Source background has a strongly different color tone (orange/yellow) from the target (blue), close to complementary → the object's color tone shifts noticeably after Poisson blending. Illustrates a **limitation** of the method when the two images have very different lighting/color tones |

Key theoretical observation from testing: Poisson blending only preserves the
*gradient* of the source, not its absolute color — so (a) the object region
must have real internal texture/gradient (a flat, solid-colored fill will
"evaporate" into a boundary interpolation), and (b) if the source background
color around the object differs greatly from the target background color,
the boundary condition will pull the whole region toward the target's tone.

## Usage — Parts 2 / 3 (Stitching)

```bash
# (once) generate a synthetic image set to validate the pipeline
python -m src.stitching.generate_synthetic_scene

# Part 2 — SIFT
python -m src.stitching.run_stitch --images "data/stitching/sample_synthetic/*.png" --detector sift --out results/stitching/sift_synthetic.jpg

# Part 3 — only changes --detector, pipeline stays the same
python -m src.stitching.run_stitch --images "data/stitching/sample_synthetic/*.png" --detector orb --out results/stitching/orb_synthetic.jpg

# Run on each member's self-captured image set the same way, only changing --images
python -m src.stitching.run_stitch --images "data/stitching/member2_set/*.jpg" --detector sift --out results/stitching/sift_member2.jpg
python -m src.stitching.run_stitch --images "data/stitching/member2_set/*.jpg" --detector orb  --out results/stitching/orb_member2.jpg
```

Add `--metrics-out results/stitching/metrics.csv` to record metrics (keypoint
count, match count, inlier ratio, reprojection error, per-step timing) for
the comparison table in report section 2.2 — each run appends a row to that
CSV, so running both detectors on all image sets and then opening the file
gives the full comparison table.

## Shared git workflow

1. The repository maintainer runs `git init` and pushes this base repo to the
   remote first.
2. Each member clones the repo and creates their own branch:
   `part1-gradient`, `part2-sift`, `part3-orb-compare`.
3. Only files/directories within one's own part should be modified (see the
   assignment table above) to avoid conflicts — Parts 2 & 3 in particular both
   touch `src/stitching/`, so coordination is needed before modifying
   `pipeline.py`/`detectors.py`.
4. Code should be cross-reviewed via Pull Request before merging into `main`.
5. The "Discussion" and "Conclusion" sections of the report are written
   jointly once all 3 parts have results — in
   `report/section_4_discussion.md` and `report/section_5_conclusion.md`
   (created when it's time to write them).
