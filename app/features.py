"""
Diagnostic-feature knowledge base + consistency checks. No model needed.

IMPORTANT: BioCLIP matches overall appearance; it does not count legs. This module
is an independent check: given features observed in the photo (by you, or read by
the optional vision step), it says whether they fit the taxa BioCLIP proposed.

To extend: add entries to KB (any rank; key is the taxon name). Only include
facts you've verified in a reference such as BugGuide or a taxonomic key.
Optional keys: legs, antennae (tuples of acceptable counts), regions, wings,
leg_pairs (tuples of acceptable codes), notes (list of text lines).
"""

REGION_LABELS = {
    "unclear": "unclear",
    "3": "three distinct regions (head, thorax, abdomen)",
    "2": "two regions (head + thorax fused, then abdomen)",
    "many": "long body of many similar segments",
}
WING_LABELS = {
    "unclear": "unclear",
    "none": "no wings visible",
    "membranous": "thin, transparent, veined wings",
    "elytra": "hardened wing covers (elytra)",
    "hemelytra": "leathery / half-hardened front wings",
    "scaly": "wings covered in scales",
}
PAIR_LABELS = {
    "unclear": "unclear",
    "na": "not applicable (few legs)",
    "one": "one pair of legs per body segment",
    "two": "two pairs of legs per body segment",
}

KB = {
    # ---------------- classes ----------------
    "Insecta": dict(
        legs=(6,), antennae=(2,), regions=("3",),
        notes=["Body in three regions: head, thorax, abdomen.",
               "Six legs, all attached to the thorax.",
               "One pair of antennae on the head.",
               "Most adults have wings."]),
    "Arachnida": dict(
        legs=(8,), antennae=(0,), regions=("2",), wings=("none",),
        notes=["Eight legs (four pairs). Spiders also have two short leg-like pedipalps near the mouth.",
               "No antennae and no wings.",
               "Usually two body regions: cephalothorax (head + thorax fused) and abdomen."]),
    "Chilopoda": dict(
        antennae=(2,), regions=("many",), leg_pairs=("one",),
        notes=["Flattened body of many segments.",
               "One pair of legs per body segment.",
               "First pair of legs is a pair of venomous fangs (forcipules).",
               "One pair of antennae."]),
    "Diplopoda": dict(
        antennae=(2,), regions=("many",), leg_pairs=("two",),
        notes=["Rounded or cylindrical body of many segments.",
               "Two pairs of legs per body segment on most segments.",
               "One pair of short antennae."]),
    # ---------------- insect orders ----------------
    "Coleoptera": dict(
        wings=("elytra",),
        notes=["Front wings are hardened into wing covers (elytra) that meet in a straight line down the back.",
               "Hind wings, if present, fold beneath the elytra.",
               "Chewing mouthparts."]),
    "Lepidoptera": dict(
        wings=("scaly",),
        notes=["Wings covered in tiny overlapping scales.",
               "Coiled proboscis for drinking nectar.",
               "Butterflies: club-tipped antennae. Moths: usually feathery or threadlike."]),
    "Diptera": dict(
        wings=("membranous",),
        notes=["Only one pair of functional wings; the hind pair is reduced to tiny knobs (halteres).",
               "Usually large compound eyes."]),
    "Hymenoptera": dict(
        wings=("membranous", "none"),
        notes=["Two pairs of membranous wings hooked together (often absent in worker ants).",
               "Most have a narrow 'waist' between thorax and abdomen (sawflies do not).",
               "Ants have elbowed antennae."]),
    "Hemiptera": dict(
        wings=("hemelytra", "membranous", "none"),
        notes=["Piercing-sucking mouthparts forming a beak folded under the body.",
               "True bugs: front wings half-leathery, half-membranous, forming an X or triangle on the back.",
               "Cicadas, aphids and hoppers have membranous wings."]),
    "Orthoptera": dict(
        wings=("hemelytra", "none"),
        notes=["Hind legs enlarged for jumping.",
               "Narrow leathery front wings (tegmina) cover the hind wings.",
               "Grasshoppers: short antennae. Crickets and katydids: long thread-like antennae."]),
    "Odonata": dict(
        wings=("membranous",),
        notes=["Two pairs of long, net-veined wings of similar size.",
               "Very large eyes and tiny bristle-like antennae.",
               "Long slender abdomen."]),
    "Blattodea": dict(
        wings=("hemelytra", "none"),
        notes=["Cockroaches: flattened oval body, head tucked under a shield-like pronotum, long thread-like antennae.",
               "Termites are also in this order: soft pale body, straight bead-like antennae, no narrow waist."]),
    "Mantodea": dict(
        wings=("hemelytra", "none"),
        notes=["Large spiny grasping front legs, usually held folded.",
               "Triangular head that can turn.", "Elongated thorax."]),
    "Neuroptera": dict(
        wings=("membranous",),
        notes=["Four net-veined lacy wings, often held roof-like over the body.",
               "Soft body, long antennae."]),
    "Dermaptera": dict(
        notes=["Pincer-like cerci at the tip of the abdomen.",
               "Very short front wings leave most of the abdomen exposed."]),
    # ---------------- families ----------------
    "Chrysomelidae": dict(
        notes=["Leaf beetles: small to medium, often bright or metallic, usually on the plants they eat.",
               "Includes tortoise beetles (subfamily Cassidinae): body and wing covers flare into a flat, "
               "shield-like rim that often hides the head and legs from above. Many are gold, metallic or "
               "translucent, and many feed on morning glories and relatives."]),
    "Coccinellidae": dict(
        notes=["Lady beetles: domed, round to oval body, often spotted.",
               "Short, clubbed antennae; head partly tucked under the pronotum."]),
    "Cerambycidae": dict(
        notes=["Longhorn beetles: elongated body.",
               "Antennae often as long as the body or longer."]),
    "Scarabaeidae": dict(
        notes=["Stout bodies.",
               "Antennae end in a fan-like club of flat plates.",
               "Front legs often broad for digging."]),
    "Curculionidae": dict(
        notes=["Weevils: head drawn out into a snout (rostrum).",
               "Elbowed antennae attached on the snout."]),
    "Formicidae": dict(
        antennae=(2,), wings=("none", "membranous"),
        notes=["Ants: elbowed antennae.",
               "Narrow waist with one or two nodes.",
               "Workers are wingless; winged reproductives are seasonal."]),
    "Apidae": dict(
        notes=["Bees: hairy bodies that carry pollen.", "Two pairs of membranous wings."]),
    "Nymphalidae": dict(
        legs=(4, 6), wings=("scaly",),
        notes=["Brush-footed butterflies: the front legs are tiny, so only four walking legs may be visible."]),
}


def _compare_count(label, n, expected, clarity):
    exp_txt = " or ".join(str(e) for e in expected)
    if n in expected:
        return ("match", f"{label}: {n} seen (expected {exp_txt}).")
    if n < min(expected):
        return ("unknown", f"{label}: only {n} seen (expected {exp_txt}); some may be hidden, "
                           f"out of frame, or broken off.")
    if n > max(expected):
        status = "unknown" if clarity == "low" else "conflict"
        return (status, f"{label}: {n} seen but expected {exp_txt}.")
    return ("unknown", f"{label}: {n} seen (expected {exp_txt}).")


def _compare_cat(label, value, expected, labels, clarity):
    exp_txt = " or ".join(labels[e] for e in expected)
    if value in expected:
        return ("match", f"{label}: {labels[value]} (expected {exp_txt}).")
    status = "unknown" if clarity == "low" else "conflict"
    return (status, f"{label}: {labels[value]}, unusual for this group (expected {exp_txt}).")


def check_taxon(name: str, obs: dict) -> list:
    """Compare observed features against what is expected for `name`.
    Returns a list of (status, text); status is match / conflict / unknown."""
    kb = KB.get(name)
    if not kb:
        return []
    clarity = obs.get("clarity", "medium")
    out = []
    if "legs" in kb and obs.get("legs") is not None:
        out.append(_compare_count("Legs", obs["legs"], kb["legs"], clarity))
    if "antennae" in kb and obs.get("antennae") is not None:
        out.append(_compare_count("Antennae", obs["antennae"], kb["antennae"], clarity))
    for key, label, labels in (("regions", "Body regions", REGION_LABELS),
                               ("wings", "Wings", WING_LABELS),
                               ("leg_pairs", "Legs per segment", PAIR_LABELS)):
        v = obs.get(key, "unclear")
        if key in kb and v not in (None, "unclear", "na"):
            out.append(_compare_cat(label, v, kb[key], labels, clarity))
    return out


def suggest_other_groups(obs: dict):
    """
    If the observed features fit another class (spider, centipede, millipede)
    better than Insecta, return a warning string; otherwise None.
    """
    scores = {}
    for cls in ("Insecta", "Arachnida", "Chilopoda", "Diplopoda"):
        results = check_taxon(cls, obs)
        scores[cls] = (sum(s == "match" for s, _ in results),
                       sum(s == "conflict" for s, _ in results))
    ins_match, ins_conf = scores["Insecta"]
    best = max((c for c in scores if c != "Insecta"), key=lambda c: scores[c][0] - 3 * scores[c][1])
    b_match, b_conf = scores[best]
    if ins_conf >= 1 and b_conf == 0 and b_match >= 2 and b_match > ins_match:
        names = {"Arachnida": "an arachnid (spider, mite, scorpion, harvestman)",
                 "Chilopoda": "a centipede", "Diplopoda": "a millipede"}
        return (f"The features you entered fit {names[best]} better than an insect. "
                f"This app's label set only contains insects, so the taxonomy above is probably wrong. "
                f"To identify other animals, set the environment variable INSECTS_ONLY=0 and restart.")
    return None
