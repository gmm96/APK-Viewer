"""
Thin wrapper around Androguard's APK parser.

Kept as its own class (rather than calling `APK(path)` inline everywhere)
so callers depend on an abstraction, and unit tests can substitute a fake
loader without touching real APK files.
"""
from androguard.core.apk import APK


class ApkLoader:
    def load(self, apk_path: str) -> APK:
        return APK(apk_path)
