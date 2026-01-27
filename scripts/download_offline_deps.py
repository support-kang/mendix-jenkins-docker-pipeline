#!/usr/bin/env python3
import os
import argparse
import requests
import sqlite3
import shutil
from pathlib import Path

# Default constants
DEFAULT_BUILDPACK_VERSION = "v5.0.26"
DEFAULT_BUILDPACK_URL = f"https://github.com/mendix/cf-mendix-buildpack/releases/download/{DEFAULT_BUILDPACK_VERSION}/cf-mendix-buildpack.zip"
CACHE_DIR = Path(__file__).parent.parent / "docker-buildpack" / "build-cache"

def ensure_cache_dir():
    if not CACHE_DIR.exists():
        print(f"Creating cache directory: {CACHE_DIR}")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Cache directory exists: {CACHE_DIR}")

def download_file(url, dest_name):
    dest_path = CACHE_DIR / dest_name
    if dest_path.exists():
        print(f"File already exists: {dest_name}, skipping download.")
        return

    print(f"Downloading {url} to {dest_name}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded {dest_name}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        if dest_path.exists():
            os.remove(dest_path)

def get_mendix_version(source_dir):
    # Try to find .mpr file
    mpr_files = list(Path(source_dir).rglob("*.mpr"))
    if not mpr_files:
        print("No .mpr file found in source directory. Cannot determine Mendix version.")
        return None
    
    mpr_file = mpr_files[0]
    print(f"Found project file: {mpr_file}")
    
    try:
        cursor = sqlite3.connect(str(mpr_file)).cursor()
        cursor.execute("SELECT _ProductVersion FROM _MetaData LIMIT 1")
        row = cursor.fetchone()
        if row:
            version = row[0]
            print(f"Detected Mendix Version: {version}")
            return version
    except Exception as e:
        print(f"Error reading .mpr file: {e}")
    
    return None

def download_runtime(version):
    if not version:
        print("Skipping runtime download (unknown version).")
        return

    # Construct runtime URL (This logic mimics build.py)
    # Note: Simplified for common cases. 
    # Mendix version format: X.Y.Z.Build
    # For buildpack, we usually need the runtime tarball.
    
    # Logic to determine filename (dotnet vs mono, arm vs x86)
    # Assuming x86_64 and dotnet (for newer versions 9.22+) for simplicity, 
    # but can be extended if needed.
    
    # Parse version tuple
    v_parts = [int(p) for p in version.split('.')]
    is_dotnet = v_parts >= [9, 22, 0, 0]
    
    runtime_type = "mxbuild" # or runtime? buildpack uses mxbuild
    # build.py downloads 'mxbuild' to build the 'builder' image.
    # It also downloads 'runtime' sometimes? No, buildpack usually handles it.
    # Let's look at build.py: build_mpr_builder uses mxbuild-X.Y.Z.tar.gz
    
    prefix = "" # Assume x86_64
    
    filename = f"{prefix}mxbuild-{version}.tar.gz"
    url = f"https://download.mendix.com/runtimes/{filename}"
    
    download_file(url, filename)

def main():
    parser = argparse.ArgumentParser(description="Download Mendix artifacts for offline build.")
    parser.add_argument("--source", default="build-source", help="Path to Mendix project source to detect version")
    parser.add_argument("--buildpack-url", default=DEFAULT_BUILDPACK_URL, help="URL for CF Mendix Buildpack zip")
    
    args = parser.parse_args()
    
    ensure_cache_dir()
    
    # 1. Download Buildpack
    download_file(args.buildpack_url, "cf-mendix-buildpack.zip")
    
    # 2. Detect Version & Download Runtime
    version = get_mendix_version(args.source)
    if version:
        download_runtime(version)
    else:
        print("Warning: Could not detect Mendix version. Runtime tarball will not be downloaded.")
        print("You can manually download mxbuild-X.Y.Z.tar.gz to docker-buildpack/build-cache if needed.")

if __name__ == "__main__":
    main()
