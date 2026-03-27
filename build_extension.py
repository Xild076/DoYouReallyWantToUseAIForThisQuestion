import zipfile
import os

def build_extension_zip():
    # List of files required for the Chrome/browser extension
    extension_files = [
        "manifest.json",
        "background.js",
        "content-script.js",
        "google-script.js",
        "popup.html",
        "popup.js",
        "settings.json"
    ]
    
    # Also include any icons if they exist in an icons/ directory
    if os.path.exists("icons") and os.path.isdir("icons"):
        for root, _, files in os.walk("icons"):
            for file in files:
                extension_files.append(os.path.join(root, file))

    zip_filename = "extension_release.zip"
    
    print(f"Creating {zip_filename}...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in extension_files:
            if os.path.exists(file):
                print(f"  [+] Adding {file}")
                zipf.write(file)
            else:
                print(f"  [!] Warning: {file} not found. Skipping.")
                
    print(f"\nSuccess! You can now upload '{zip_filename}' to the Chrome Web Store or other add-on platforms.")

if __name__ == "__main__":
    build_extension_zip()
