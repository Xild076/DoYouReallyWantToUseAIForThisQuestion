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


def build_firefox_manifest(base_manifest):
    # Deep-copy via JSON to avoid mutating the source manifest.
    firefox_manifest = json.loads(json.dumps(base_manifest))

    browser_settings = firefox_manifest.get("browser_specific_settings", {})
    gecko_settings = browser_settings.get("gecko", {})
    browser_settings["gecko"] = {**FIREFOX_GECKO_SETTINGS, **gecko_settings}
    firefox_manifest["browser_specific_settings"] = browser_settings

    # Firefox uses background scripts for compatibility.
    background = firefox_manifest.get("background", {})
    service_worker = background.get("service_worker")
    if service_worker:
        if "scripts" not in background:
            background["scripts"] = [service_worker]
        background.pop("service_worker", None)
        firefox_manifest["background"] = background

    return firefox_manifest


def build_extension_zips():
    for legacy_file in ("extension_release.zip", "extension_firefox_release.zip"):
        if os.path.exists(legacy_file):
            os.remove(legacy_file)
            print(f"Removed legacy artifact {legacy_file}")

    extension_files = collect_extension_files()
    base_manifest = load_manifest("manifest.json")

    # Chrome/Chromium package
    create_zip("extension_chromium_release.zip", base_manifest, extension_files)

    # Firefox package with gecko metadata and background fallback.
    firefox_manifest = build_firefox_manifest(base_manifest)
    create_zip("extension_firefox_release.xpi", firefox_manifest, extension_files)

    print("\nSuccess! Built extension_chromium_release.zip (Chrome/Chromium) and extension_firefox_release.xpi (Firefox).")

if __name__ == "__main__":
    build_extension_zips()
