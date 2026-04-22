# Static surf spot metadata used by the browse and favorites views.
spots = {
    "The Spit": {"id": "5d81295f9f26b100014e2eee", "image": "images/spots/the-spit.png"},
    "Main Beach": {"id": "584204204e65fad6a77092ce", "image": "images/spots/main-beach.jpg"},
    "Surfers Paradise": {"id": "584204204e65fad6a77092d0", "image": "images/spots/surfers-paradise.jpg"},
    "Broadbeach": {"id": "584204204e65fad6a77092d3", "image": "images/spots/broadbeach.webp"},
    "Mermaid Beach": {"id": "584204204e65fad6a77092d5", "image": "images/spots/mermaid-beach.jpg"},
    "Miami": {"id": "5d7c127712781b00019f8799", "image": "images/spots/miami.jpg"},
    "Burleigh Heads": {"id": "5842041f4e65fad6a7708be8", "image": "images/spots/burleigh.jpg"},
    "Palm Beach": {"id": "584204204e65fad6a77092d6", "image": "images/spots/palm-beach.jpg"},
    "Currumbin Alley": {"id": "5842041f4e65fad6a7708c2e", "image": "images/spots/currumbin.jpg"},
    "Tugun": {"id": "584204204e65fad6a77092da", "image": "images/spots/tugun.jpg"},
    "Bilinga": {"id": "640b8f57606c451c6df13338", "image": "images/spots/bilinga.jpg"},
    "Kirra": {"id": "5842041f4e65fad6a7708be9", "image": "images/spots/kirra.jpg"},
    "Greenmount": {"id": "5aea4194cd9646001ab81b0f", "image": "images/spots/greenmount.webp"},
    "Snapper Rocks": {"id": "5842041f4e65fad6a7708be5", "image": "images/spots/snappers.jpg"},
    "Duranbah": {"id": "5842041f4e65fad6a7708c11", "image": "images/spots/dbah.jpg"},
}

# Slugs and ordering are derived once so routes/templates can reuse them consistently.
spot_slugs = {spot_name.lower().replace(" ", "_"): spot_name for spot_name in spots}
spot_order = {spot_name: index for index, spot_name in enumerate(spots)}
