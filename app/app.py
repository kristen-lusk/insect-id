"""
Insect Identifier: upload a photo or video and get the taxonomy down to the
deepest rank the model is confident about, with a feature-based explanation.

Run:  python -m streamlit run app.py

Environment variables (all optional):
  BIOCLIP_MODEL=v1     use the smaller original BioCLIP (less memory)
  INSECTS_ONLY=0       don't restrict labels to insects (identify any organism)
"""
import io
import os
import tempfile
from urllib.parse import quote

import cv2
import streamlit as st
from PIL import Image

from common_names import lay_name
from core import RANKS, derive_common, make_views, rollup, walk
from features import KB, PAIR_LABELS, REGION_LABELS, WING_LABELS, check_taxon, suggest_other_groups

try:
    from bioclip import Rank, TreeOfLifeClassifier
except ImportError:
    st.error("pybioclip is not installed. Run: pip install -r requirements.txt")
    st.stop()

MODEL_CHOICE = os.environ.get("BIOCLIP_MODEL", "v2").lower()
INSECTS_ONLY = os.environ.get("INSECTS_ONLY", "1") != "0"


@st.cache_resource(show_spinner="Loading model and label set (first run takes a few minutes)...")
def load_classifier():
    if MODEL_CHOICE == "v1":
        try:
            from bioclip import BIOCLIP_V1_MODEL_STR
        except ImportError:
            raise RuntimeError("Old pybioclip installed. Run: pip install -U pybioclip")
        clf = TreeOfLifeClassifier(model_str=BIOCLIP_V1_MODEL_STR)
    else:
        clf = TreeOfLifeClassifier()  # BioCLIP 2 by default in current pybioclip

    n_labels = len(clf.txt_names)
    if INSECTS_ONLY:
        # The model can then only choose between insects, which removes a lot
        # of look-alike confusion.
        keep = clf.create_taxa_filter(Rank.CLASS, ["Insecta"])
        clf.apply_filter(keep)
        n_labels = int(sum(keep))
    return clf, n_labels


@st.cache_resource(show_spinner="Reading the model's label list...")
def label_table(_clf):
    return _clf.get_label_data()


def video_frames(data: bytes, suffix: str, every_n_seconds=1.0, max_frames=8):
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(data)
    tmp.close()
    cap = cv2.VideoCapture(tmp.name)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(int(fps * every_n_seconds), 1)
    frames, i = [], 0
    while len(frames) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        i += 1
    cap.release()
    os.unlink(tmp.name)
    return frames


def opt_index(options, value):
    return options.index(value) if value in options else 0


# ------------------------------- UI -------------------------------
st.set_page_config(page_title="Insect Identifier", page_icon="🐞")
st.title("🐞 Insect Identifier")
st.caption("Upload a photo or short video. Results go as deep as the model is confident.")

with st.sidebar:
    st.header("Settings")
    threshold = st.slider("Confidence threshold", 0.10, 0.95, 0.40, 0.05,
                          help="Lower goes deeper but is less reliable.")
    multi = st.checkbox("Multi-view analysis (slower, usually better)", value=True,
                        help="Also analyzes zoomed-in and mirrored versions of the photo.")
    st.caption(f"Model: {'BioCLIP (v1)' if MODEL_CHOICE == 'v1' else 'BioCLIP 2'}")
    st.caption("Label set: insects only." if INSECTS_ONLY else "Label set: all organisms.")

uploaded = st.file_uploader("Image or video",
                            type=["jpg", "jpeg", "png", "webp", "mp4", "mov", "avi", "mkv"])

if uploaded:
    data = uploaded.getvalue()
    upload_id = f"{uploaded.name}-{len(data)}"
    is_video = uploaded.name.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))

    # New upload -> reset per-upload state
    if st.session_state.get("upload_id") != upload_id:
        st.session_state.update(upload_id=upload_id, pred_key=None)

    if is_video:
        st.video(data)
    else:
        st.image(Image.open(io.BytesIO(data)), use_container_width=True)

    clf, n_labels = load_classifier()

    # Run the model only when the upload or the multi-view setting changes
    pred_key = (upload_id, multi)
    if st.session_state.get("pred_key") != pred_key:
        if is_video:
            frames = video_frames(data, os.path.splitext(uploaded.name)[1])
            if not frames:
                st.error("Couldn't read any frames from that video.")
                st.stop()
            views = [v for f in frames for _, v in make_views(f, multi=False)]
        else:
            views = [v for _, v in make_views(Image.open(io.BytesIO(data)), multi=multi)]
        with st.spinner("Identifying..."):
            species_preds = clf.predict(views, Rank.SPECIES, k=200)
        st.session_state.update(pred_key=pred_key, n_views=len(views),
                                totals=rollup(species_preds, n_views=len(views)),
                                common=derive_common(species_preds))

    totals = st.session_state.totals
    common = st.session_state.get("common", {})

    def pretty(rank, name):
        text, _ = lay_name(name, common.get(rank, {}).get(name), exact=(rank == "species"))
        return f"{name} ({text})" if text else name
    accepted, tentative, alternatives = walk(totals, threshold)

    # ---------------------------- result ----------------------------
    if not accepted:
        st.warning("Not confident about anything. Try a sharper, closer photo with the insect "
                   "filling more of the frame.")
    else:
        st.subheader("Result")
        top_rank, top_name, top_conf = accepted[-1]
        st.success(f"Best match: **{pretty(top_rank, top_name)}**  \n"
                   f"Identified to {top_rank} ({top_conf:.0%} confident)")
        if RANKS.index(top_rank) >= 3:
            q = quote(top_name)
            st.markdown(f"Look it up: [BugGuide](https://bugguide.net/index.php?q=search&keys={q}) "
                        f"(North America only) · [iNaturalist](https://www.inaturalist.org/taxa/search?q={q}) "
                        f"· [GBIF](https://www.gbif.org/species/search?q={q})")
        for rank, name, conf in accepted:
            st.markdown(f"**{rank.capitalize()}:** {pretty(rank, name)}  \n"
                        f"<small>confidence {conf:.0%}</small>", unsafe_allow_html=True)
            st.progress(min(conf, 1.0))
        if len(accepted) < len(RANKS):
            st.info(f"Stopped at **{accepted[-1][0]}**: not confident enough to name the "
                    f"{RANKS[len(accepted)]}.")

    if alternatives:
        st.subheader(f"Closest candidates ({alternatives[0][0]})")
        for _, name, conf in alternatives:
            st.write(f"- {pretty(alternatives[0][0], name)}: {conf:.0%}")
        st.caption("These are possibilities, not identifications. Compare them with photos on "
                   "iNaturalist, BugGuide, or GBIF.")

    # ------------------------- why this result -------------------------
    st.divider()
    st.subheader("Why this result?")
    st.caption("BioCLIP matches the overall look of your photo against millions of labeled photos. "
               "It does not count legs or antennae, so it cannot explain itself in anatomical terms. "
               "This section is a separate check: it compares features visible in the photo with what is "
               "typical for each group BioCLIP proposed.")

    o, oid = {}, 0  # manual entry: everything starts as 'unknown'
    leg_opts = ["unknown"] + [str(i) for i in range(0, 13)] + ["many (13+)"]
    ant_opts = ["unknown", "0", "1", "2", "4"]

    def to_int(s):
        return None if s == "unknown" else 13 if s.startswith("many") else int(s)

    st.markdown("**What can you see in the photo?** Fill in what you can; leave the rest as unknown. "
                "(Insects: 6 legs, 2 antennae, 3 body regions. Spiders: 8 legs, no antennae, 2 body regions.)")
    c1, c2 = st.columns(2)
    legs_s = c1.selectbox("Legs visible", leg_opts, key=f"legs{oid}",
                          index=opt_index(leg_opts, str(o.get("legs")) if o.get("legs") is not None else "unknown"))
    ant_s = c2.selectbox("Antennae visible", ant_opts, key=f"ant{oid}",
                         index=opt_index(ant_opts, str(o.get("antennae")) if o.get("antennae") is not None else "unknown"))
    regions = c1.selectbox("Body regions", list(REGION_LABELS), key=f"reg{oid}",
                           format_func=REGION_LABELS.get, index=opt_index(list(REGION_LABELS), o.get("regions", "unclear")))
    wings = c2.selectbox("Wings", list(WING_LABELS), key=f"wing{oid}",
                         format_func=WING_LABELS.get, index=opt_index(list(WING_LABELS), o.get("wings", "unclear")))
    pairs = c1.selectbox("Legs per body segment", list(PAIR_LABELS), key=f"pair{oid}",
                         format_func=PAIR_LABELS.get, index=opt_index(list(PAIR_LABELS), o.get("leg_pairs", "unclear")))
    clarity = c2.selectbox("Photo clarity for counting", ["high", "medium", "low"], key=f"clar{oid}",
                           index=opt_index(["high", "medium", "low"], o.get("clarity", "medium")))

    obs_now = dict(legs=to_int(legs_s), antennae=to_int(ant_s), regions=regions, wings=wings,
                   leg_pairs=pairs, clarity=clarity)

    warning = suggest_other_groups(obs_now)
    if warning:
        st.warning(warning)

    shown = [(r, n, c, False) for r, n, c in accepted] + [(r, n, c, True) for r, n, c in tentative[:1]]
    icons = {"match": "✅", "conflict": "⚠️", "unknown": "❔"}
    for i, (rank, name, conf, is_tentative) in enumerate(shown):
        label = f"{rank.capitalize()}: {pretty(rank, name)} [{conf:.0%}{', tentative' if is_tentative else ''}]"
        with st.expander(label, expanded=(i == len(accepted) - 1)):
            kb = KB.get(name)
            if not kb:
                st.caption(f"No stored feature notes for {name} yet. You can add them to KB in features.py.")
                continue
            if kb.get("notes"):
                st.markdown("**What defines this group**")
                st.markdown("\n".join(f"- {n}" for n in kb["notes"]))
            checks = check_taxon(name, obs_now)
            if checks:
                st.markdown("**How your photo compares**")
                st.markdown("\n".join(f"- {icons[s]} {t}" for s, t in checks))
            else:
                st.caption("Enter some features above to compare them with this group.")
    st.caption("✅ fits · ⚠️ unusual for this group · ❔ can't tell (often hidden legs or antennae)")

    # ------------------------------ debug ------------------------------
    with st.expander("Debug: model details"):
        st.caption(f"{n_labels:,} species in the active label set · {st.session_state.n_views} view(s) analyzed")
        for rank in RANKS:
            top = sorted(totals[rank].items(), key=lambda kv: -kv[1])[:3]
            st.write(f"**{rank}**: " + ", ".join(f"{lin[-1]} ({s:.0%})" for lin, s in top))
        st.markdown("**Is a genus in the model's label set at all?** If it isn't, the model can never "
                    "output it, no matter how good the photo is.")
        genus_q = st.text_input("Genus to look up", placeholder="Microctenochira")
        if genus_q:
            try:
                df = label_table(clf)
                hit = df[df["genus"].str.lower() == genus_q.strip().lower()]
                if hit.empty:
                    st.error(f"'{genus_q}' is NOT in the model's label set.")
                else:
                    st.success(f"Found {len(hit)} species labeled in genus {genus_q}.")
                    st.write(", ".join(hit["species"].head(15)))
            except Exception as e:
                st.error(f"Lookup failed: {e}")

