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

def queries(topic, cutoff, since='1900-01-01'):
    mesh, words, _ = TOPICS[topic]
    mesh=re.sub(r'MESH_HEADING:"([^"]+)"',r'"\1"[MeSH Terms]',mesh)
    parts=re.findall(r'"[^"]+"|\(|\)|\bAND\b|\bOR\b|[^\s()]+',words)
    pubmed_words=' '.join(p if p in ('AND','OR','(',')') else p+'[Title/Abstract]' for p in parts)
    suffix = f' AND SRC:MED AND FIRST_PDATE:[{since} TO {cutoff}]'
    return {"mesh":f'({mesh}) AND ({pubmed_words}) AND ("{since.replace(chr(45),chr(47))}"[Date - Publication] : "{cutoff.replace(chr(45),chr(47))}"[Date - Publication])', "title_abstract":f'TITLE_ABS:({words})'+suffix}
