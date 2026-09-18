"""
Centralised detection of optional third-party dependencies.

Import the flags/symbols from here instead of repeating try/except
import blocks in every module that might need lxml or Pillow.
"""

try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    etree = None
    HAS_LXML = False

if not HAS_LXML:
    import xml.etree.ElementTree as ET
else:
    ET = None

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except ImportError:
    Image = None
    ImageDraw = None
    ImageTk = None
    HAS_PIL = False
