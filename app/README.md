# 🐞 Insect Identifier

A free web app that identifies insects from a photo or short video. It reports the taxonomy (kingdom → phylum → class → order → family → genus → species) **down to the deepest rank it is confident about**, and stops there instead of guessing. If it can't tell the species but is sure of the genus, you get the genus.

It also shows common names (for example, *Leptinotarsa* → Colorado potato beetle and relatives) and a "Why this result?" section that explains which physical features define each group.

> **Best guess, not a verdict.** Results can be wrong, especially at genus and species level. Always verify against reference photos (links are provided in the app) before relying on an identification, particularly for anything safety-related such as venomous species or pest decisions.

## Features

- Upload a **photo or video** (video frames are sampled and combined)
- **Stops at the last confident rank**, with an adjustable confidence threshold
- **Common (lay) names** next to scientific names
- **Closest candidates** when it isn't confident enough to commit
- **"Why this result?"**: what defines each group (leg count, antennae, body regions, wings) and how the features you see in your photo compare, with a warning if they fit a spider, centipede or millipede better than an insect
- **Multi-view analysis**: also examines zoomed-in and mirrored versions of your photo, which helps with small insects in wide shots
- **Label lookup** (Debug panel): check whether a genus exists in the model's label set at all
- Quick links to **BugGuide** (North America only), **iNaturalist** and **GBIF**
- Runs entirely on your own computer. No photos are sent to any third party and no API keys are needed.

## How it works

The identification uses [BioCLIP](https://github.com/Imageomics/bioclip), an open vision model trained on millions of labeled photos of living things, through the [pybioclip](https://github.com/imageomics/pybioclip) library. By default this is BioCLIP 2.

1. The app limits the model's label set to class Insecta, so it can only choose among insects.
2. The photo is analyzed in several views (full image, zoomed crops, mirrored).
3. The model predicts species; probabilities are then added up into each genus, family, order and so on.
4. The app walks down the ranks and stops at the first one that falls below your confidence threshold.

**Important:** BioCLIP matches the overall *appearance* of your photo to labeled photos. It does not count legs or antennae. The "Why this result?" section is a separate check based on a small knowledge base of diagnostic features (`features.py`) and the features you enter.

## Setup (macOS / Linux)

Python 3.10 to 3.12 is recommended.

```bash
git clone https://github.com/YOUR_USERNAME/insect-id.git
cd insect-id
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app.py
```

Use `python -m streamlit` rather than plain `streamlit`. If you have Anaconda installed, plain `streamlit` can pick up the wrong copy.

The **first launch takes several minutes**: it downloads the model and builds the insect label set (internet required). Later launches are faster.

### Memory

BioCLIP 2 holds a large label table in memory; plan for roughly 6 GB of free RAM or more (this is an estimate). On smaller machines use the lighter original model:

```bash
BIOCLIP_MODEL=v1 python -m streamlit run app.py
```

### Options (environment variables)

| Variable | Effect |
|---|---|
| `BIOCLIP_MODEL=v1` | Use the smaller original BioCLIP (less memory, lower accuracy) |
| `INSECTS_ONLY=0` | Don't restrict labels to insects (identify any organism) |

## Using it on your phone

The app is a web page, so any phone browser can use it. Choose one:

- **Same Wi-Fi:** run `python -m streamlit run app.py --server.address 0.0.0.0` and open the "Network URL" it prints on your phone. Anyone on that network can reach it.
- **Anywhere, privately (free):** install [Tailscale](https://tailscale.com) on your computer and phone, sign in to the same account, then run
  `python -m streamlit run app.py --server.address YOUR_TAILSCALE_IP` and open `http://YOUR_TAILSCALE_IP:8501` on your phone. Your computer must stay on and awake (`caffeinate -i` helps on a Mac).
- Then use your browser's **Add to Home Screen** for an app-like icon.

Hosting notes for other options are in `DEPLOY.md`.

## Project layout

| File | Purpose |
|---|---|
| `app.py` | The Streamlit user interface |
| `core.py` | Image preparation and the "stop at the last confident rank" logic |
| `features.py` | Diagnostic-feature knowledge base and consistency checks |
| `common_names.py` | Common-name list |
| `test_core.py`, `test_features.py` | Tests for the logic that doesn't need the model |
| `DEPLOY.md` | Hosting notes |

Run the tests with `python test_core.py` and `python test_features.py`.

## Extending it

- **Add common names:** add a line to `COMMON` in `common_names.py`, such as `"Genusname": "lay name"`.
- **Add diagnostic features:** add an entry to `KB` in `features.py`. Only include facts you've verified in a reference such as [BugGuide](https://bugguide.net) or a taxonomic key.

## Known limitations

- **The model can only name taxa in its label set.** If a genus isn't in the label set, it can never be the answer. Use the Debug panel's lookup to check.
- Some groups (for example tortoise beetles) look very similar across genera, so the correct genus may appear as a runner-up rather than the top result.
- Confidence percentages are a guide, not calibrated probabilities.
- Photo quality matters: a sharp, close, well-lit image with the insect filling much of the frame works best.
- Counting legs and antennae from a photo is hard; the feature section relies on what you can see, and hidden legs show as "can't tell" rather than as a conflict.
- Videos are sampled at about one frame per second (up to 8 frames).

## Ideas for future work

Regional label filtering (for example, species recorded in your country), few-shot reference photos for groups the model doesn't know, a field log with location, and an accuracy benchmark on photos with confirmed IDs.

## Credits

- [BioCLIP](https://github.com/Imageomics/bioclip) and [pybioclip](https://github.com/imageomics/pybioclip) by the Imageomics Institute. Please see their repositories for licenses and how to cite them.
- Reference sites used for checking results: [BugGuide](https://bugguide.net), [iNaturalist](https://www.inaturalist.org), [GBIF](https://www.gbif.org).

## License

No license has been chosen yet. Add a `LICENSE` file to say how others may use this code (GitHub's "Add file → Create new file → LICENSE" offers templates, such as MIT).
