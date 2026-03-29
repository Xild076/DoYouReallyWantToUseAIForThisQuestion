---
title: DYRWTUAFTQ Backend
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Do You Really Want to Use AI For This Question? (AIImportance)

Using AI to make AI unemployed!!!!!!

Basically, the question is: do you really need to use AI for this question? the answer: probably no!!!! So, we categorize a task on three things:
- A task
- A high-complexity question (that MIGHT need AI)
- A low-complexity question (that could easily be googled or does not need AI)

## Features
- **Browser Extension**: Seamlessly inspects your prompts before you send them to an AI (like ChatGPT), intercepting and warning you if it's a simple search query instead.
- **PyTorch Backend**: A custom `app.py` API serving the `ib_classifier.pth` and `ic_classifier.pth` machine learning models.
- **Custom Dataset Builder**: Python scripts for generating massive synthetic training data (`generate_massive_data.py`, `expand_dataset_massive.py`).

## Project Structure
- `backend/` - The Python API (app.py) that loads the PyTorch models and serves predictions.
- `src/` - The machine learning pipeline, including model architecture (`model.py`) and dataset generation scripts.
- `model/` - Contains the trained weights for the classifiers.
- `background.js`, `content-script.js`, `popup.js`, `manifest.json` - The core browser extension files.

## Getting Started

### 1. Run the Backend
You can run the backend server natively or via Docker.
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python backend/app.py
```
*(Alternatively, you can build and run using the included `dockerfile`)*

### 2. Install the Browser Extension
1. Open Google Chrome (or any Chromium browser).
2. Go to `chrome://extensions/`.
3. Enable **Developer mode** in the top right.
4. Click **Load unpacked** and select the root directory of this repository.

### 3. Add / Replace Extension Icons
The extension now reads icons from `icons/` via `manifest.json`.

1. Generate baseline icon files (16, 32, 48, 96, 128):
```bash
python scripts/generate_extension_icons.py
```
2. Replace the generated files in `icons/` with your branded PNGs using the same names:
	- `icon16.png`
	- `icon32.png`
	- `icon48.png`
	- `icon96.png`
	- `icon128.png`
3. Reload the unpacked extension in your browser to see the new icon.
4. Rebuild release artifacts:
```bash
python build_extension.py
```

### 4. Firefox Support
This project can also be packaged for Firefox.

1. Build both extension zips:
```bash
python build_extension.py
```
2. Use `extension_firefox_release.zip` for Firefox.
3. For local testing in Firefox, open `about:debugging#/runtime/this-firefox`, click **Load Temporary Add-on**, and choose the project's `manifest.json` file (or the `manifest.json` from an extracted Firefox package).
4. For permanent distribution, submit `extension_firefox_release.zip` to AMO (addons.mozilla.org).

## Da Goal
Save energy and compute power by questioning whether we really need to fire up massive LLMs just to do basic arithmetic or ask standard search-engine questions so that we don't kill our planet.

btw: i'm kind of hosting this entire thing on hf spaces... which means the system isn't scalable even though, by my own standards, its pretty efficient... so... i'd be grateful for any possible donation which i can use to scale this up? lemme publish the extension first so that ppl can use it...