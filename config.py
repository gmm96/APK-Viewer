"""
Global configuration and constants used across the application.
"""

# --- UI sizing ---
ICON_SIZE = (96, 96)
MIN_LIST_LINES = 3
LABEL_WIDTH = 25

# --- Fonts ---
FONT_TITLE = ("Helvetica", 20, "bold")
FONT_SUBTITLE = ("Helvetica", 12)
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)
FONT_MONO_SMALL_ITALIC = FONT_MONO_SMALL + ("italic",)

# --- Colors ---
COLOR_PLACEHOLDER_BG = "#e0e0e0"
COLOR_PLACEHOLDER_BORDER = "#cccccc"
COLOR_TEXT_BG = "#fcfcfc"
COLOR_MARK_BG = "#cfe3fc"
COLOR_FOLDER_BG = "#eef3f8"

# XML syntax highlight colors
COLOR_XML_TAG = "#800000"
COLOR_XML_ATTR = "#FF0000"
COLOR_XML_VALUE = "#0000FF"
COLOR_XML_COMMENT = "#008000"

# Tag name shared between the line-marker and the copy context menu
MARKED_LINE_TAG = "marked_line"

# --- Android manifest namespace ---
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

# --- DPI priority used when picking the best app icon resource ---
DPI_SCORES = {
    "xxxhdpi": 5,
    "xxhdpi": 4,
    "xhdpi": 3,
    "hdpi": 2,
    "mdpi": 1,
}

# --- Known trackers / SDK package signatures ---
KNOWN_TRACKERS = {
    "google.android.gms.measurement": "Google Analytics / Firebase",
    "facebook.appevents": "Facebook Analytics",
    "appsflyer": "AppsFlyer",
    "mixpanel": "Mixpanel",
    "flurry": "Flurry",
    "adjust": "Adjust",
    "amplitude": "Amplitude",
    "kochava": "Kochava",
    "branch.io": "Branch",
    "segment.analytics": "Segment",
    "yandex.metrica": "Yandex Metrica",
    "clevertap": "CleverTap",
    "moengage": "MoEngage",
    "localytics": "Localytics",
    "tenjin": "Tenjin",
    "snowplow": "Snowplow Analytics",
    "crashlytics": "Crashlytics (Google)",
    "bugsnag": "Bugsnag",
    "sentry": "Sentry",
    "newrelic": "New Relic",
    "datadog": "Datadog",
    "instabug": "Instabug",
    "appdynamics": "AppDynamics",
    "google.android.gms.ads": "Google AdMob",
    "facebook.ads": "Facebook Audience Network",
    "unity3d.ads": "Unity Ads",
    "applovin": "AppLovin",
    "vungle": "Vungle",
    "ironsource": "ironSource",
    "chartboost": "Chartboost",
    "inmobi": "InMobi",
    "bytedance": "TikTok / Pangle Ads",
    "amazon.device.ads": "Amazon Ads",
    "mopub": "MoPub (Twitter)",
    "tapjoy": "Tapjoy",
    "adcolony": "AdColony",
    "onesignal": "OneSignal",
    "urbanairship": "Airship",
    "braze": "Braze",
    "pushwoosh": "Pushwoosh",
    "batch": "Batch",
    "leanplum": "Leanplum",
}
