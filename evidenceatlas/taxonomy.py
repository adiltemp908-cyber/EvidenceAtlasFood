"""Versioned discovery strata. Query conclusions never select records."""
import re
VERSION = "nutrition-taxonomy-2"
TOPICS = {
    "caffeine_sleep": ('MESH_HEADING:"Caffeine" OR MESH_HEADING:"Coffee"', '(caffeine OR coffee OR tea) AND (sleep OR insomnia)', ['caffeine','coffee','tea']),
    "meal_timing": ('MESH_HEADING:"Intermittent Fasting" OR MESH_HEADING:"Meals"', '("meal timing" OR "late eating" OR "time restricted eating" OR "intermittent fasting") AND (weight OR glucose OR metabolic)', ['fasting','meal','eating','feeding']),
    "protein_kidney": ('MESH_HEADING:"Dietary Proteins"', '("dietary protein" OR "high protein" OR "protein intake" OR "protein supplementation") AND (kidney OR renal OR "glomerular filtration")', ['protein']),
    "sweeteners": ('MESH_HEADING:"Sweetening Agents"', '(sweetener OR aspartame OR sucralose OR stevia OR "sugar sweetened") AND (glucose OR weight OR diabetes OR health)', ['sweetener','aspartame','sucralose','stevia','sugar']),
    "dietary_fats": ('MESH_HEADING:"Dietary Fats" OR MESH_HEADING:"Plant Oils"', '("seed oil" OR "vegetable oil" OR "saturated fat" OR "unsaturated fat") AND (cardiovascular OR cholesterol OR inflammation)', ['oil','fat','fatty']),
    "fiber_gut": ('MESH_HEADING:"Dietary Fiber"', '(fiber OR fibre OR "whole grain") AND (gut OR bowel OR constipation OR microbiome)', ['fiber','fibre','grain']),
    "sodium_pressure": ('MESH_HEADING:"Sodium, Dietary"', '("sodium intake" OR "salt intake" OR "salt reduction" OR "dietary sodium" OR "sodium reduction") AND ("blood pressure" OR hypertension)', ['sodium','salt']),
    "preparation_vitamins": ('MESH_HEADING:"Cooking"', '(cooking OR boiling OR steaming OR storage) AND (vegetable OR fruit) AND (vitamin OR nutrient OR bioavailability)', ['cooking','boiling','steaming','vegetable','fruit']),
    "dietary_patterns": ('MESH_HEADING:"Diet, Mediterranean" OR MESH_HEADING:"Diet, Vegetarian"', '("Mediterranean diet" OR "plant based diet" OR "ultra processed") AND (health OR cardiovascular OR diabetes OR mortality)', ['diet','processed']),
    "dairy_bone": ('MESH_HEADING:"Dairy Products" OR MESH_HEADING:"Calcium, Dietary"', '(milk OR dairy OR yogurt OR calcium) AND (bone OR fracture OR osteoporosis)', ['milk','dairy','yogurt','calcium']),
    "micronutrients": ('MESH_HEADING:"Vitamins" OR MESH_HEADING:"Minerals"', '(vitamin OR iron OR zinc) AND (dietary OR supplementation) AND (deficiency OR status OR health)', ['vitamin','iron','zinc','mineral']),
    "food_safety": ('MESH_HEADING:"Food Contamination"', '(food OR dietary OR fish) AND (mercury OR acrylamide OR contaminant) AND (exposure OR health OR risk)', ['food','diet','fish','mercury','acrylamide']),
}

# Coverage additions, 2026-10-13. Existing query hashes remain stable for resumable discovery.
TOPICS.update({'egg_cholesterol': ('MESH_HEADING:"Eggs" OR MESH_HEADING:"Cholesterol, Dietary"', '(egg OR eggs OR "egg consumption") AND (cholesterol OR lipid OR cardiovascular)', ['egg', 'cholesterol']), 'protein_muscle': ('MESH_HEADING:"Dietary Proteins" OR MESH_HEADING:"Resistance Training"', '("protein intake" OR "protein supplementation" OR "dietary protein") AND (muscle OR strength OR hypertrophy)', ['protein']), 'breakfast_cereal': ('MESH_HEADING:"Breakfast" OR MESH_HEADING:"Whole Grains"', '("breakfast cereal" OR "ready to eat cereal" OR oatmeal OR oats) AND (glucose OR satiety OR weight OR cholesterol OR health)', ['cereal', 'oat']), 'yogurt_digestion': ('MESH_HEADING:"Yogurt" OR MESH_HEADING:"Fermented Foods"', '(yogurt OR yoghurt OR kefir) AND (digestion OR constipation OR bowel OR microbiome OR "lactose intolerance")', ['yogurt', 'yoghurt', 'kefir']), 'fruit_juice': ('MESH_HEADING:"Fruit and Vegetable Juices" OR MESH_HEADING:"Fruit"', '("fruit juice" OR "whole fruit") AND (glucose OR diabetes OR weight OR satiety OR glycemic)', ['fruit', 'juice']), 'red_meat_cancer': ('MESH_HEADING:"Red Meat" OR MESH_HEADING:"Meat Products"', '("red meat" OR "processed meat") AND (cancer OR colorectal)', ['meat']), 'wholegrain_metabolic': ('MESH_HEADING:"Whole Grains" OR MESH_HEADING:"Dietary Fiber"', '("whole grain" OR wholegrain OR "whole wheat") AND ("refined grain" OR "white bread" OR glucose OR diabetes OR cardiovascular)', ['grain', 'wheat', 'bread'])})

# Product coverage additions, 2026-10-19.
TOPICS.update({'creatine_supplements': ['MESH_HEADING:"Creatine"', '(creatine AND (supplement OR supplementation OR intake)) AND (muscle OR strength OR exercise OR cognition OR kidney OR safety)', ['creatine']], 'plant_milks': ['MESH_HEADING:"Soy Milk" OR MESH_HEADING:"Milk Substitutes"', '("soy milk" OR soymilk OR "almond milk" OR "oat milk" OR "plant based milk" OR "plant-based milk") AND (nutrition OR protein OR calcium OR glucose OR cholesterol OR health)', ['soy', 'soymilk', 'almond', 'oat', 'plant']], 'nuts_seeds': ['MESH_HEADING:"Nuts" OR MESH_HEADING:"Seeds"', '(walnut OR walnuts OR peanut OR peanuts OR almond OR almonds OR chia OR flaxseed) AND (consumption OR intake OR supplementation OR dietary) AND (cholesterol OR glucose OR weight OR cardiovascular OR health)', ['walnut', 'peanut', 'almond', 'chia', 'flax']], 'omega3_supplements': ['MESH_HEADING:"Fatty Acids, Omega-3" OR MESH_HEADING:"Fish Oils"', '("fish oil" OR "omega-3" OR "omega 3") AND (supplementation OR dietary OR intake) AND (cardiovascular OR triglycerides OR inflammation OR cognition OR health)', ['fish oil', 'omega']], 'magnesium_supplements': ['MESH_HEADING:"Magnesium"', 'magnesium AND (oral OR dietary OR supplementation) AND (sleep OR cramps OR glucose OR migraine OR deficiency OR health)', ['magnesium']], 'collagen_supplements': ['MESH_HEADING:"Collagen"', '("collagen peptides" OR "hydrolyzed collagen" OR "collagen supplementation") AND (oral OR dietary OR ingestion) AND (skin OR joint OR bone OR muscle OR health)', ['collagen']], 'psyllium_products': ['MESH_HEADING:"Psyllium"', '(psyllium OR ispaghula) AND (constipation OR cholesterol OR glucose OR weight OR bowel)', ['psyllium', 'ispaghula']], 'probiotic_supplements': ['MESH_HEADING:"Probiotics"', '(probiotic OR probiotics) AND (supplement OR supplementation OR capsule) AND (gut OR constipation OR diarrhea OR bowel OR digestion)', ['probiotic']], 'sports_drinks': ['MESH_HEADING:"Beverages" OR MESH_HEADING:"Energy Drinks"', '("sports drink" OR "sports drinks" OR "energy drink" OR "energy drinks" OR "electrolyte drink" OR "electrolyte beverage") AND (hydration OR exercise OR performance OR cardiovascular OR sleep OR health)', ['sports drink', 'energy drink', 'electrolyte']], 'whey_products': ['MESH_HEADING:"Whey Proteins"', '("whey protein" OR "protein bar" OR "protein bars" OR "protein shake" OR "protein shakes") AND (muscle OR satiety OR weight OR glucose OR kidney OR health)', ['whey', 'protein']]})

# Targeted food gaps, 2026-10-20.
TOPICS.update({'flax_chia': ['MESH_HEADING:"Seeds" OR MESH_HEADING:"Dietary Fiber"', '(flaxseed OR linseed OR chia) AND (consumption OR dietary OR supplementation OR intake) AND (glucose OR cholesterol OR weight OR cardiovascular OR bowel)', ['flax', 'linseed', 'chia']], 'protein_bars': ['MESH_HEADING:"Dietary Proteins" OR MESH_HEADING:"Dietary Supplements"', '("protein bar" OR "protein bars" OR "high protein snack" OR "high-protein snack" OR "meal replacement bar") AND (protein OR satiety OR glucose OR weight OR muscle OR nutrition)', ['protein', 'meal replacement']], 'electrolyte_hydration': ['MESH_HEADING:"Beverages" OR MESH_HEADING:"Rehydration Solutions"', '("electrolyte drink" OR "electrolyte beverage" OR "sports beverage" OR "sports drink" OR "oral rehydration solution") AND (hydration OR dehydration OR exercise OR sodium OR performance OR health)', ['electrolyte', 'sports', 'rehydration']], 'oat_almond_milk': ['MESH_HEADING:"Milk Substitutes"', '("oat milk" OR "almond milk" OR "oat beverage" OR "almond beverage" OR "oat-based milk" OR "almond-based milk") AND (nutrition OR protein OR calcium OR glucose OR health OR bioavailability)', ['oat', 'almond']], 'green_tea': ['MESH_HEADING:"Tea"', '"green tea" AND (consumption OR supplementation OR dietary OR intake) AND (glucose OR weight OR cholesterol OR liver OR cardiovascular OR health)', ['green tea']], 'legumes_health': ['MESH_HEADING:"Fabaceae" OR MESH_HEADING:"Dietary Fiber"', '(lentil OR lentils OR chickpea OR chickpeas OR legumes OR "dietary pulses") AND (consumption OR intake OR dietary) AND (glucose OR satiety OR cholesterol OR weight OR cardiovascular OR health)', ['lentil', 'chickpea', 'legume', 'pulse']], 'fermented_products': ['MESH_HEADING:"Fermented Foods"', '(kimchi OR kombucha OR sauerkraut OR tempeh) AND (consumption OR intake OR dietary OR supplementation) AND (gut OR glucose OR microbiome OR cholesterol OR health)', ['kimchi', 'kombucha', 'sauerkraut', 'tempeh']]})

# Everyday diet coverage, 2026-11-04. Existing discovery hashes stay stable.
EVERYDAY_TOPICS = {
    'water_requirements': (
        'MESH_HEADING:"Drinking" OR MESH_HEADING:"Water" OR MESH_HEADING:"Water-Electrolyte Balance"',
        '("water intake" OR "water consumption" OR "water requirements" OR "fluid intake" OR "total water") AND (daily OR adequate OR requirement OR recommendation OR hydration)',
        ['water', 'fluid', 'hydration']),
    'plain_water_health': (
        'MESH_HEADING:"Drinking Water" OR MESH_HEADING:"Drinking"',
        '("drinking water" OR "plain water" OR "water intake" OR "water consumption") AND (constipation OR cognition OR headache OR satiety OR weight OR "kidney stones" OR "water balance")',
        ['water', 'fluid']),
    'fruit_vegetable_servings': (
        'MESH_HEADING:"Fruit" OR MESH_HEADING:"Vegetables"',
        '("fruit intake" OR "vegetable intake" OR "fruit and vegetable" OR "fruit consumption" OR "vegetable consumption") AND (servings OR portions OR daily OR "dose response") AND (health OR mortality OR cardiovascular OR diabetes)',
        ['fruit', 'vegetable']),
    'protein_requirements': (
        'MESH_HEADING:"Dietary Proteins" OR MESH_HEADING:"Nutritional Requirements"',
        '("protein requirement" OR "protein requirements" OR "protein intake" OR "recommended dietary allowance") AND (daily OR adequate OR requirement OR recommendation OR "nitrogen balance")',
        ['protein']),
    'breakfast_habits': (
        'MESH_HEADING:"Breakfast" OR MESH_HEADING:"Meals"',
        '(breakfast OR "breakfast skipping" OR "skipping breakfast") AND (weight OR appetite OR satiety OR glucose OR cognition OR health)',
        ['breakfast']),
    'staple_grains': (
        'MESH_HEADING:"Oryza" OR MESH_HEADING:"Bread" OR MESH_HEADING:"Whole Grains"',
        '("white rice" OR "brown rice" OR "white bread" OR "whole wheat bread" OR "whole grain bread" OR chapati) AND (intake OR consumption OR dietary) AND (glucose OR glycemic OR diabetes OR satiety OR weight)',
        ['rice', 'bread', 'chapati', 'grain']),
    'fiber_requirements': (
        'MESH_HEADING:"Dietary Fiber"',
        '("fiber intake" OR "fibre intake" OR "dietary fiber" OR "dietary fibre") AND (daily OR recommendation OR requirement OR "dose response") AND (bowel OR constipation OR health OR cardiovascular OR mortality)',
        ['fiber', 'fibre']),
    'salt_intake': (
        'MESH_HEADING:"Sodium, Dietary" OR MESH_HEADING:"Sodium Chloride, Dietary"',
        '("salt intake" OR "sodium intake" OR "salt reduction" OR "sodium reduction") AND (daily OR recommendation OR requirement OR "dose response") AND (health OR "blood pressure" OR cardiovascular OR mortality)',
        ['salt', 'sodium']),
    'added_sugar_intake': (
        'MESH_HEADING:"Dietary Sugars" OR MESH_HEADING:"Sucrose"',
        '("added sugar" OR "added sugars" OR "free sugars" OR "sugar intake") AND (daily OR recommendation OR intake OR reduction) AND (weight OR diabetes OR dental OR caries OR cardiovascular OR health)',
        ['sugar', 'sucrose']),
    'dairy_tolerance': (
        'MESH_HEADING:"Milk" OR MESH_HEADING:"Lactose Intolerance" OR MESH_HEADING:"Dairy Products"',
        '(milk OR dairy OR lactose) AND (intake OR consumption) AND (tolerance OR intolerance OR digestion OR "lactose malabsorption" OR "calcium intake")',
        ['milk', 'dairy', 'lactose']),
    'coffee_intake': (
        'MESH_HEADING:"Coffee" OR MESH_HEADING:"Caffeine"',
        '("coffee consumption" OR "coffee intake" OR "caffeine intake") AND (daily OR cups OR moderate OR habitual OR safety) AND (sleep OR health OR cardiovascular OR mortality OR anxiety)',
        ['coffee', 'caffeine']),
}
# Both discovery routes require human context; missing MeSH alone does not exclude a study.
for _topic, (_mesh, _words, _terms) in EVERYDAY_TOPICS.items():
    TOPICS[_topic] = (_mesh, _words + ' AND (human OR humans OR adult OR adults OR women OR men OR children OR adolescents OR population OR participants)', _terms)

def queries(topic, cutoff, since='1900-01-01'):
    mesh, words, _ = TOPICS[topic]
    mesh=re.sub(r'MESH_HEADING:"([^"]+)"',r'"\1"[MeSH Terms]',mesh)
    parts=re.findall(r'"[^"]+"|\(|\)|\bAND\b|\bOR\b|[^\s()]+',words)
    pubmed_words=' '.join(p if p in ('AND','OR','(',')') else p+'[Title/Abstract]' for p in parts)
    suffix = f' AND SRC:MED AND FIRST_PDATE:[{since} TO {cutoff}]'
    return {"mesh":f'({mesh}) AND ({pubmed_words}) AND ("{since.replace(chr(45),chr(47))}"[Date - Publication] : "{cutoff.replace(chr(45),chr(47))}"[Date - Publication])', "title_abstract":f'TITLE_ABS:({words})'+suffix}
