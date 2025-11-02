"""
Examples of how to create products with JSON deliverables

This shows the new, better format for deliverables using JSON.
You can use this when adding new products with /addproduct command.
"""

import json

# Simple format - just list of items
simple_deliverables = json.dumps([
    "Discord Nitro Gift Link",
    "Activation instructions",
    "24/7 Support"
])

# Advanced format - with types and emojis
advanced_deliverables = json.dumps([
    {"item": "Discord Nitro Gift Link", "type": "code"},
    {"item": "Activation instructions", "type": "guide"},
    {"item": "24/7 Support", "type": "support"}
])

# Available types and their emojis:
# 'code' -> 🔑
# 'account' -> 👤
# 'file' -> 📁
# 'link' -> 🔗
# 'guide' -> 📖
# 'support' -> 💬
# 'service' -> ⚡
# 'warranty' -> 🛡️
# 'key' -> 🔐

# Example products with new format:

NITRO_DELIVERABLES = json.dumps([
    {"item": "Discord Nitro Gift Link", "type": "code"},
    {"item": "Activation instructions", "type": "guide"},
    {"item": "24/7 Support", "type": "support"}
])

SPOTIFY_DELIVERABLES = json.dumps([
    {"item": "Account credentials", "type": "account"},
    {"item": "Activation guide", "type": "guide"},
    {"item": "6 months support", "type": "support"}
])

INSTAGRAM_DELIVERABLES = json.dumps([
    {"item": "5000 Real Followers", "type": "service"},
    {"item": "10000 Likes", "type": "service"},
    {"item": "100 Comments", "type": "service"},
    {"item": "Progress tracking link", "type": "link"}
])

CUSTOM_BOT_DELIVERABLES = json.dumps([
    {"item": "Source code (Full access)", "type": "file"},
    {"item": "Setup guide", "type": "guide"},
    {"item": "1 month support", "type": "support"},
    {"item": "Free updates for 30 days", "type": "support"}
])

NETFLIX_DELIVERABLES = json.dumps([
    {"item": "Account credentials", "type": "account"},
    {"item": "1 year warranty", "type": "warranty"},
    {"item": "Replacement guarantee", "type": "support"}
])

# When using /addproduct command, paste the JSON string as deliverables parameter
# Example:
# /addproduct category:best_sold product:"Premium Service" price:49.99 
# description:"Amazing service" deliverables:'[{"item":"Service key","type":"code"}]'
# image_url:"https://..." stock:10

print("Product Examples with JSON Deliverables")
print("="*50)
print("\nNitro deliverables:", NITRO_DELIVERABLES)
print("\nSpotify deliverables:", SPOTIFY_DELIVERABLES)
print("\nInstagram deliverables:", INSTAGRAM_DELIVERABLES)
