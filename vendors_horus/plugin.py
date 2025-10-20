"""
Plugin definition
"""

from Blocks.vendors import extract_vendors_block
from HorusAPI import Plugin

plugin = Plugin()

plugin.addBlock(extract_vendors_block)
