"""Deterministic generator for the M9 W9B recipe KG fixture.

Outputs to stdout a Cypher MERGE script that builds:
  - 16 :Cuisine nodes (per §2.3 hierarchy)
  - 40 :Ingredient nodes (incl. ambiguity seeds)
  - 12 :Author nodes
  - 12 :Technique nodes
  - 120 :Recipe nodes
  - 15 cuisine :SUBCLASS_OF edges
  -  8 ingredient :SUBCLASS_OF edges
  - 120 :OF_CUISINE edges (1/recipe)
  - 120 :BY_AUTHOR edges (1/recipe)
  - ~360 :USES_INGREDIENT edges (3/recipe)
  - ~180 :REQUIRES_TECHNIQUE edges (~1.5/recipe)

Identity Discipline: every node carries :Entity + id. Idempotent MERGE.
Deterministic — pinned random seed so byte-identical reruns.
"""

import random

random.seed(42)

print("// Module 9 Week B — Integration 9B — Recipe KG fixture")
print("// 200 nodes, ~803 relationships. Identity Discipline: :Entity + id.")
print("// Generated deterministically; do not edit by hand — re-run the generator.\n")

# ----- Cuisines (16) per §2.3 hierarchy --------------------------------------
CUISINES = [
    # (name, parent_name_or_None)
    ("World",         None),
    ("Asian",         "World"),
    ("European",      "World"),
    ("Americas",      "World"),
    ("Chinese",       "Asian"),
    ("Japanese",      "Asian"),
    ("Indian",        "Asian"),
    ("Thai",          "Asian"),
    ("Sichuan",       "Chinese"),
    ("Cantonese",     "Chinese"),
    ("Hunan",         "Chinese"),
    ("Italian",       "European"),
    ("French",        "European"),
    ("Spanish",       "European"),
    ("Tuscan",        "Italian"),
    ("Sicilian",      "Italian"),
    ("Mexican",       "Americas"),
    ("NorthAmerican", "Americas"),
]
# Note: 18 entries here; but contract §2.4 specifies 16. We drop Cantonese + Hunan to land at 16.
CUISINES = [c for c in CUISINES if c[0] not in ("Cantonese", "Hunan")]
assert len(CUISINES) == 16, len(CUISINES)

# slug helper
def slug(s):
    return s.lower().replace(" ", "-")

print("// ---------- Cuisines (16) ----------")
for name, _parent in CUISINES:
    print(f"MERGE (:Cuisine:Entity {{id: 'cuisine:{slug(name)}', name: '{name}'}});")

print("\n// ---------- Cuisine SUBCLASS_OF edges (15 — every non-root) ----------")
sub_count = 0
for name, parent in CUISINES:
    if parent is None:
        continue
    print(
        f"MATCH (c1:Cuisine {{id: 'cuisine:{slug(name)}'}}), "
        f"(c2:Cuisine {{id: 'cuisine:{slug(parent)}'}}) "
        f"MERGE (c1)-[:SUBCLASS_OF]->(c2);"
    )
    sub_count += 1
assert sub_count == 15, sub_count

# ----- Ingredients (40) -------------------------------------------------------
# Includes the ambiguity-seeding ingredients per §2.5 and a peppercorn hierarchy
# of 4 levels: szechuanPeppercorn -> peppercorn -> spice (rooted).
INGREDIENTS = [
    # (name, category)
    ("ginger", "spice"),
    ("garlic", "vegetable"),
    ("basil", "herb"),            # ambiguous with author "Basil"
    ("orange", "fruit"),          # ambiguous with cuisine "Orange" — TODO: drop or keep cuisine?
    ("turkey", "poultry"),        # ambiguous with cuisine "Turkish"
    ("sage", "herb"),             # ambiguous with author "Sage"
    ("salt", "seasoning"),
    ("pepper", "spice"),          # parent in pepper subhierarchy
    ("peppercorn", "spice"),
    ("szechuan-peppercorn", "spice"),
    ("chili", "spice"),
    ("tomato", "vegetable"),
    ("onion", "vegetable"),
    ("scallion", "vegetable"),
    ("soy-sauce", "condiment"),
    ("rice", "grain"),
    ("rice-noodles", "grain"),
    ("wheat-noodles", "grain"),
    ("egg", "protein"),
    ("chicken", "poultry"),
    ("beef", "protein"),
    ("pork", "protein"),
    ("tofu", "protein"),
    ("shrimp", "seafood"),
    ("fish", "seafood"),
    ("lemon", "fruit"),
    ("lime", "fruit"),
    ("cilantro", "herb"),
    ("parsley", "herb"),
    ("thyme", "herb"),
    ("rosemary", "herb"),
    ("oregano", "herb"),
    ("flour", "grain"),
    ("butter", "dairy"),
    ("cheese", "dairy"),
    ("cream", "dairy"),
    ("milk", "dairy"),
    ("olive-oil", "oil"),
    ("sesame-oil", "oil"),
    ("vinegar", "condiment"),
]
assert len(INGREDIENTS) == 40, len(INGREDIENTS)

print("\n// ---------- Ingredients (40) ----------")
for name, category in INGREDIENTS:
    display = name.replace("-", " ")
    print(
        f"MERGE (n:Ingredient:Entity {{id: 'ingredient:{name}'}}) "
        f"SET n.name = '{display}', n.category = '{category}';"
    )

# Ingredient SUBCLASS_OF edges (8):
# szechuan-peppercorn -> peppercorn -> pepper
# scallion -> onion
# rice-noodles -> rice
# wheat-noodles -> flour
# shrimp -> fish
# (and a couple of fruit subclasses)
# lime -> lemon (citrus chain; symbolic — both citrus)
# parsley -> cilantro (herb chain)
ING_SUBS = [
    ("szechuan-peppercorn", "peppercorn"),
    ("peppercorn",          "pepper"),
    ("scallion",            "onion"),
    ("rice-noodles",        "rice"),
    ("wheat-noodles",       "flour"),
    ("shrimp",              "fish"),
    ("lime",                "lemon"),
    ("parsley",             "cilantro"),
]
assert len(ING_SUBS) == 8
print("\n// ---------- Ingredient SUBCLASS_OF edges (8) ----------")
for child, parent in ING_SUBS:
    print(
        f"MATCH (a:Ingredient {{id: 'ingredient:{child}'}}), "
        f"(b:Ingredient {{id: 'ingredient:{parent}'}}) "
        f"MERGE (a)-[:SUBCLASS_OF]->(b);"
    )

# ----- Authors (12) -----------------------------------------------------------
AUTHORS = [
    ("Maria Rossi",       "Italy"),
    ("Giovanni Ferri",    "Italy"),
    ("Chen Wei",          "China"),
    ("Li Mei",            "China"),
    ("Hiro Tanaka",       "Japan"),
    ("Priya Sharma",      "India"),
    ("Somchai Phan",      "Thailand"),
    ("Pierre Dubois",     "France"),
    ("Carmen Lopez",      "Spain"),
    ("Diego Hernandez",   "Mexico"),
    ("Basil Roy",         "United States"),   # ambiguous with ingredient "basil"
    ("Sage Lindholm",     "United States"),   # ambiguous with ingredient "sage"
]
assert len(AUTHORS) == 12
print("\n// ---------- Authors (12) ----------")
for name, country in AUTHORS:
    aid = slug(name)
    print(
        f"MERGE (n:Author:Entity {{id: 'author:{aid}'}}) "
        f"SET n.name = '{name}', n.country = '{country}';"
    )

# ----- Techniques (12) --------------------------------------------------------
TECHNIQUES = [
    "wok", "braise", "saute", "roast", "grill", "steam",
    "fry", "bake", "boil", "simmer", "smoke", "poach",
]
assert len(TECHNIQUES) == 12
print("\n// ---------- Techniques (12) ----------")
for name in TECHNIQUES:
    print(
        f"MERGE (n:Technique:Entity {{id: 'technique:{name}'}}) "
        f"SET n.name = '{name}';"
    )

# ----- Recipes (120) ----------------------------------------------------------
# Assign each recipe a single cuisine (round-robin biased so each leaf has
# coverage), a single author, ~3 ingredients, and ~1.5 techniques.

# Leaf cuisines we want recipes to actually live on (drives subclass traversal tests):
LEAF_CUISINES = [
    "Sichuan",        # 12 recipes
    "Japanese",       # 10
    "Indian",         # 10
    "Thai",           #  8
    "Chinese",        #  4 (non-Sichuan Chinese)
    "Italian",        #  8 (generic Italian)
    "Tuscan",         #  8
    "Sicilian",       #  6
    "French",         # 10
    "Spanish",        #  8
    "Mexican",        # 10
    "NorthAmerican",  # 14
    "Asian",          #  6 (generic Asian)
    "European",       #  4 (generic European)
    "Americas",       #  2 (generic Americas)
]
COUNTS = [12, 10, 10, 8, 4, 8, 8, 6, 10, 8, 10, 14, 6, 4, 2]
assert sum(COUNTS) == 120

recipe_cuisine_pairs = []
for cuisine, count in zip(LEAF_CUISINES, COUNTS):
    for _ in range(count):
        recipe_cuisine_pairs.append(cuisine)

print("\n// ---------- Recipes (120) ----------")
recipe_names_used = set()
def make_recipe_name(idx, cuisine):
    base_pool = {
        "Sichuan":       ["Mapo Tofu", "Kung Pao Chicken", "Dan Dan Noodles", "Twice-Cooked Pork", "Sichuan Hotpot", "Fish Fragrant Eggplant"],
        "Japanese":      ["Tonkatsu", "Ramen", "Sushi Roll", "Tempura", "Onigiri", "Yakitori"],
        "Indian":        ["Butter Chicken", "Palak Paneer", "Biryani", "Samosa", "Dosa", "Vindaloo"],
        "Thai":          ["Pad Thai", "Green Curry", "Tom Yum", "Som Tum", "Massaman Curry"],
        "Chinese":       ["Char Siu", "Wonton Soup", "Egg Drop Soup"],
        "Italian":       ["Margherita Pizza", "Carbonara", "Lasagna", "Risotto", "Tiramisu"],
        "Tuscan":        ["Ribollita", "Bistecca", "Pappa al Pomodoro", "Panzanella"],
        "Sicilian":      ["Caponata", "Arancini", "Pasta alla Norma"],
        "French":        ["Coq au Vin", "Ratatouille", "Bouillabaisse", "Quiche Lorraine", "Cassoulet"],
        "Spanish":       ["Paella", "Gazpacho", "Tortilla Espanola", "Patatas Bravas"],
        "Mexican":       ["Tacos al Pastor", "Mole Poblano", "Pozole", "Enchiladas", "Chiles en Nogada"],
        "NorthAmerican": ["Cheeseburger", "Mac and Cheese", "BBQ Ribs", "Clam Chowder", "Cornbread", "Buffalo Wings", "Apple Pie"],
        "Asian":         ["Bibimbap", "Bao Buns", "Pho"],
        "European":      ["Goulash", "Pierogi"],
        "Americas":      ["Feijoada", "Ceviche"],
    }
    pool = base_pool.get(cuisine, [cuisine + " Dish"])
    name = pool[idx % len(pool)]
    # disambiguate duplicates by appending a numeric suffix
    final = name
    n = 2
    while final in recipe_names_used:
        final = f"{name} #{n}"
        n += 1
    recipe_names_used.add(final)
    return final

recipes = []  # list of (recipe_id, name, cuisine, prepMinutes, popularityScore)
for i, cuisine in enumerate(recipe_cuisine_pairs, start=1):
    name = make_recipe_name(i, cuisine)
    prep = random.choice([10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 75, 90])
    pop = random.randint(1, 100)
    rid = f"recipe:{i}"
    recipes.append((rid, name, cuisine, prep, pop))
    safe_name = name.replace("'", "\\'")
    print(
        f"MERGE (r:Recipe:Entity {{id: '{rid}'}}) "
        f"SET r.name = '{safe_name}', r.description = 'A {cuisine} recipe.', "
        f"r.prepMinutes = {prep}, r.popularityScore = {pop};"
    )

# ----- OF_CUISINE (120) -------------------------------------------------------
print("\n// ---------- OF_CUISINE edges (120) ----------")
for rid, _name, cuisine, _prep, _pop in recipes:
    print(
        f"MATCH (r:Recipe {{id: '{rid}'}}), (c:Cuisine {{id: 'cuisine:{slug(cuisine)}'}}) "
        f"MERGE (r)-[:OF_CUISINE]->(c);"
    )

# ----- BY_AUTHOR (120) --------------------------------------------------------
print("\n// ---------- BY_AUTHOR edges (120) ----------")
for rid, _name, cuisine, _prep, _pop in recipes:
    # Pick author by cuisine affinity for realism; everything deterministic.
    affinity = {
        "Italian": "Maria Rossi", "Tuscan": "Maria Rossi", "Sicilian": "Giovanni Ferri",
        "Chinese": "Chen Wei", "Sichuan": "Chen Wei", "Japanese": "Hiro Tanaka",
        "Indian": "Priya Sharma", "Thai": "Somchai Phan", "French": "Pierre Dubois",
        "Spanish": "Carmen Lopez", "Mexican": "Diego Hernandez",
        "NorthAmerican": "Basil Roy", "Asian": "Li Mei", "European": "Sage Lindholm",
        "Americas": "Diego Hernandez",
    }
    aname = affinity.get(cuisine, "Basil Roy")
    aid = slug(aname)
    print(
        f"MATCH (r:Recipe {{id: '{rid}'}}), (a:Author {{id: 'author:{aid}'}}) "
        f"MERGE (r)-[:BY_AUTHOR]->(a);"
    )

# ----- USES_INGREDIENT (~360) -------------------------------------------------
# 3 ingredients per recipe deterministically, biased so ginger/garlic/basil
# appear with high frequency in matching cuisines.
print("\n// ---------- USES_INGREDIENT edges (~360) ----------")
ingredient_names = [name for name, _cat in INGREDIENTS]

# Cuisine-flavored ingredient pools
CUISINE_INGREDIENTS = {
    "Sichuan":       ["ginger", "garlic", "szechuan-peppercorn", "chili", "soy-sauce", "tofu", "scallion"],
    "Japanese":      ["soy-sauce", "rice", "fish", "egg", "scallion", "sesame-oil"],
    "Indian":        ["ginger", "garlic", "chili", "cilantro", "onion", "tomato"],
    "Thai":          ["ginger", "garlic", "lime", "chili", "rice-noodles", "cilantro"],
    "Chinese":       ["ginger", "garlic", "soy-sauce", "scallion", "rice"],
    "Italian":       ["basil", "tomato", "olive-oil", "cheese", "wheat-noodles", "garlic"],
    "Tuscan":        ["olive-oil", "tomato", "basil", "garlic", "rosemary"],
    "Sicilian":      ["tomato", "olive-oil", "basil", "oregano", "garlic"],
    "French":        ["butter", "cream", "thyme", "garlic", "onion", "parsley"],
    "Spanish":       ["olive-oil", "garlic", "tomato", "onion", "shrimp"],
    "Mexican":       ["chili", "lime", "cilantro", "onion", "tomato", "chicken"],
    "NorthAmerican": ["butter", "cheese", "flour", "egg", "milk", "beef"],
    "Asian":         ["ginger", "garlic", "soy-sauce", "rice"],
    "European":      ["butter", "flour", "onion", "thyme"],
    "Americas":      ["chili", "lime", "tomato", "cilantro"],
}

ui_count = 0
for rid, _name, cuisine, _prep, _pop in recipes:
    pool = CUISINE_INGREDIENTS.get(cuisine, ingredient_names)
    chosen = random.sample(pool, k=3) if len(pool) >= 3 else pool[:3]
    for ing in chosen:
        print(
            f"MATCH (r:Recipe {{id: '{rid}'}}), (i:Ingredient {{id: 'ingredient:{ing}'}}) "
            f"MERGE (r)-[:USES_INGREDIENT]->(i);"
        )
        ui_count += 1

# ----- REQUIRES_TECHNIQUE (~180) ---------------------------------------------
print(f"\n// ---------- REQUIRES_TECHNIQUE edges (~180) ----------")
CUISINE_TECHNIQUES = {
    "Sichuan":       ["wok", "fry"],
    "Japanese":      ["steam", "grill"],
    "Indian":        ["simmer", "fry"],
    "Thai":          ["wok", "boil"],
    "Chinese":       ["wok", "steam"],
    "Italian":       ["bake", "boil"],
    "Tuscan":        ["braise", "roast"],
    "Sicilian":      ["bake", "fry"],
    "French":        ["braise", "saute"],
    "Spanish":       ["saute", "grill"],
    "Mexican":       ["grill", "saute"],
    "NorthAmerican": ["bake", "smoke"],
    "Asian":         ["wok", "steam"],
    "European":      ["braise", "saute"],
    "Americas":      ["grill", "smoke"],
}

rt_count = 0
for rid, _name, cuisine, _prep, _pop in recipes:
    techs = CUISINE_TECHNIQUES.get(cuisine, ["bake"])
    # Half the recipes get 2 techniques, half get 1, deterministically.
    # Bias to 2 techniques where pool allows so total lands near 180.
    if int(rid.split(":")[1]) % 2 != 0 and len(techs) >= 2:
        chosen = techs[:2]
    else:
        chosen = techs[:1]
    for t in chosen:
        print(
            f"MATCH (r:Recipe {{id: '{rid}'}}), (t:Technique {{id: 'technique:{t}'}}) "
            f"MERGE (r)-[:REQUIRES_TECHNIQUE]->(t);"
        )
        rt_count += 1

# Final counts go to stderr so the cypher file stays clean
import sys
print(f"// Generated counts: USES_INGREDIENT={ui_count}, REQUIRES_TECHNIQUE={rt_count}", file=sys.stderr)
