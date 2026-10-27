"""
Pure helper logic (no model, no Streamlit) so it can be tested on its own.
"""
from collections import defaultdict

from PIL import Image, ImageOps

RANKS = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]


# ----------------------------- images -----------------------------
def pad_square(img: Image.Image, fill=(128, 128, 128)) -> Image.Image:
    """Pad to a square so the model's center-crop never cuts off the insect."""
    w, h = img.size
    s = max(w, h)
    canvas = Image.new("RGB", (s, s), fill)
    canvas.paste(img, ((s - w) // 2, (s - h) // 2))
    return canvas


def center_crop(img: Image.Image, frac: float) -> Image.Image:
    w, h = img.size
    cw, ch = int(w * frac), int(h * frac)
    left, top = (w - cw) // 2, (h - ch) // 2
    return img.crop((left, top, left + cw, top + ch))


def make_views(img: Image.Image, multi: bool = True, max_side: int = 1280):
    """
    Returns a list of (name, PIL image). Phone photos are rotated upright using
    EXIF, shrunk for speed, and (optionally) zoomed in a few ways, because a
    small beetle on a leaf may fill only a fraction of a wide photo.
    """
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((max_side, max_side))
    views = [("full image", pad_square(img))]
    if multi:
        views += [
            ("center 70%", pad_square(center_crop(img, 0.70))),
            ("center 45%", pad_square(center_crop(img, 0.45))),
            ("mirrored", ImageOps.mirror(pad_square(img))),
        ]
    return views


# --------------------------- taxonomy -----------------------------
def lineage_of(pred: dict, rank: str) -> tuple:
    return tuple(pred[r] for r in RANKS[: RANKS.index(rank) + 1])


def rollup(species_preds: list, n_views: int) -> dict:
    """
    species_preds: list of dicts from classifier.predict(..., Rank.SPECIES).
    Adds up each species' probability into its genus, family, order, ...
    Returns {rank: {lineage_tuple: avg_probability}}.
    """
    totals = {r: defaultdict(float) for r in RANKS}
    for p in species_preds:
        for rank in RANKS:
            totals[rank][lineage_of(p, rank)] += p["score"] / n_views
    return totals


def walk(totals: dict, threshold: float):
    """
    Walk down the ranks following the best lineage that agrees with the
    ranks above it.
      accepted  : ranks with confidence >= threshold (contiguous from the top)
      tentative : deeper best guesses below the threshold
      alternatives : top candidates at the first rank that was NOT accepted
    Each item is (rank, name, confidence).
    """
    accepted, tentative, prefix = [], [], ()
    alternatives = []
    confident = True
    for rank in RANKS:
        cands = {
            lin: s for lin, s in totals[rank].items() if lin[: len(prefix)] == prefix
        }
        if not cands:
            break
        ranked = sorted(cands.items(), key=lambda kv: -kv[1])
        best_lin, conf = ranked[0]
        if confident and conf >= threshold:
            accepted.append((rank, best_lin[-1], conf))
        else:
            if confident:  # first rank that failed: keep runners-up
                alternatives = [(rank, lin[-1], s) for lin, s in ranked[:5]]
            confident = False
            tentative.append((rank, best_lin[-1], conf))
        prefix = best_lin
    return accepted, tentative, alternatives
