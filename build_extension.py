import json
import os
import zipfile


EXTENSION_FILES = [
    "manifest.json",
    "background.js",
    "content-script.js",
    "google-script.js",
    "popup.html",
    "popup.js",
    "settings.json",
]

FIREFOX_GECKO_SETTINGS = {
    "id": "dyrwtuaftq@aiimportance.dev",
    "strict_min_version": "121.0",
}


def collect_extension_files():
    extension_files = list(EXTENSION_FILES)

    # Also include any icons if they exist in an icons/ directory
    if os.path.exists("icons") and os.path.isdir("icons"):
        for root, _, files in os.walk("icons"):
            for file in files:
                extension_files.append(os.path.join(root, file))

    return extension_files


def load_manifest(path="manifest.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_zip(zip_filename, manifest, extension_files):
    print(f"Creating {zip_filename}...")

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
        print("  [+] Adding manifest.json")

        for file in extension_files:
            if file == "manifest.json":
                continue
            if os.path.exists(file):
                print(f"  [+] Adding {file}")
                zipf.write(file)
            else:
                print(f"  [!] Warning: {file} not found. Skipping.")


def build_extension_zips():
    extension_files = collect_extension_files()
    base_manifest = load_manifest("manifest.json")

    # Chrome/Chromium package
    create_zip("extension_chromium_release.zip", base_manifest, extension_files)

    # Firefox package with gecko metadata
    firefox_manifest = dict(base_manifest)
    firefox_manifest["browser_specific_settings"] = {"gecko": FIREFOX_GECKO_SETTINGS}
    create_zip("extension_firefox_release.zip", firefox_manifest, extension_files)

    print("\nSuccess! Built extension_release.zip (Chrome/Chromium) and extension_firefox_release.zip (Firefox).")

if __name__ == "__main__":
    build_extension_zips()
