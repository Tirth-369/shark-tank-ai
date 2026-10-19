# Shark Tank AI — Dark UI update

## Visual updates
- Dark charcoal/navy theme with cyan glow accents and dark chart styling.
- Vertical icon-labelled navigation for Home, Companies, Analytics, Pitch Analyzer, Compare Sharks, Scenario Simulator, Dataset Insights, and Model Card.
- Seven original Season 1 shark cards with circular local image slots.
- Initial-based circular PNG placeholders ensure the interface works offline even when photos are unavailable.

## Optional real shark portraits
The execution environment used to prepare this ZIP could verify online image source pages but could not connect to download image files. To populate the local photo slots, run this once on a computer with internet access:

```bash
python download_shark_photos.py
```

Successful downloads are saved under `assets/sharks/` and are used offline by the app. If a download fails, the local placeholder remains in use. Image URLs point to third-party publishers; check source terms and image rights before public deployment or redistribution. Source URLs are listed in `download_shark_photos.py`.

## Run
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The original model files, dataset, prediction functions, and pitch extractor are retained. Individual shark prediction models still cover only the five sharks included in the trained model metadata; Ashneer and Ghazal are shown as Season 1 profiles, not given fabricated model predictions.
