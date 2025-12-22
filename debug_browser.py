#!/usr/bin/env python
"""Debug script to check Playwright browser detection on current platform."""
import os
import sys
import glob

print("=" * 60)
print("Playwright Browser Detection Debug")
print("=" * 60)

# Platform info
print(f"\nPlatform: {sys.platform}")
print(f"Python: {sys.executable}")

# Environment variables
print(f"\nEnvironment:")
print(f"  LOCALAPPDATA: {os.environ.get('LOCALAPPDATA', 'NOT SET')}")
print(f"  USERPROFILE: {os.environ.get('USERPROFILE', 'NOT SET')}")
print(f"  HOME: {os.environ.get('HOME', 'NOT SET')}")

# Check cache locations (priority: root first for containers)
cache_paths = [
    "/root/.cache/ms-playwright",  # Linux root (check first for containers)
    os.path.expanduser("~/.cache/ms-playwright"),  # Linux user
    os.path.expanduser("~/Library/Caches/ms-playwright"),  # macOS
]

# Windows paths
if sys.platform == "win32":
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        cache_paths.insert(0, os.path.join(local_app_data, "ms-playwright"))
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        cache_paths.insert(0, os.path.join(user_profile, "AppData", "Local", "ms-playwright"))

print(f"\nChecking cache paths:")
for path in cache_paths:
    exists = os.path.exists(path)
    print(f"  {path}: {'EXISTS' if exists else 'not found'}")
    if exists:
        print(f"    Contents: {os.listdir(path)}")

# Look for browser executables
print(f"\nSearching for browser executables...")
found_browsers = []

for cache_path in cache_paths:
    if not os.path.exists(cache_path):
        continue

    # Windows patterns
    if sys.platform == "win32":
        patterns = [
            os.path.join(cache_path, "chromium-*", "chrome-win", "chrome.exe"),
            os.path.join(cache_path, "chromium-*", "chrome-win64", "chrome.exe"),
        ]
    else:
        patterns = [
            os.path.join(cache_path, "chromium-*", "chrome-linux", "chrome"),
            os.path.join(cache_path, "chromium-*", "chrome-mac", "Chromium.app", "Contents", "MacOS", "Chromium"),
        ]

    for pattern in patterns:
        matches = glob.glob(pattern)
        for match in matches:
            if os.path.isfile(match):
                found_browsers.append(match)
                print(f"  FOUND: {match}")

if not found_browsers:
    print("  No browser executables found!")
    print("\n  Try running: playwright install chromium")

# Test Playwright import
print(f"\nTesting Playwright...")
try:
    from playwright.sync_api import sync_playwright
    print("  Playwright imported successfully!")

    if found_browsers:
        print(f"\nTrying to launch browser with: {found_browsers[0]}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    executable_path=found_browsers[0]
                )
                print("  Browser launched successfully!")
                page = browser.new_page()
                page.set_content("<html><body><h1>Test Page</h1></body></html>")
                print(f"  Page title: {page.title()}")
                browser.close()
                print("  Browser closed successfully!")
                print("\n✓ Playwright is working correctly!")
        except Exception as e:
            print(f"  Browser launch failed: {e}")
    else:
        print("\nTrying default Playwright browser detection...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                print("  Default browser launch succeeded!")
                browser.close()
                print("\n✓ Playwright is working with default browser!")
        except Exception as e:
            print(f"  Default browser launch failed: {e}")
            print("\n  You may need to install browsers: playwright install chromium")

except ImportError as e:
    print(f"  Playwright import failed: {e}")
    print("  Install with: pip install playwright")

print("\n" + "=" * 60)
