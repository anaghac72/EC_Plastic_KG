"""Domain lexicon, cue words and regexes used by the rule-based extractor.

Everything domain-specific lives here so it can be extended without touching
extraction logic. Each entity: (canonical name, entity type, regex pattern).
"""
import re

ENTITY_PATTERNS = [
    # Materials / polymers
    ("PET", "Polymer", r"\bPET\b|polyethylene terephthalate"),
    ("HDPE", "Polymer", r"\bHDPE\b|high-density polyethylene"),
    ("LDPE", "Polymer", r"\bLDPE\b|low-density polyethylene"),
    ("Polypropylene (PP)", "Polymer", r"\bpolypropylene\b|\bPP\b"),
    ("PVC", "Polymer", r"\bPVC\b|polyvinyl chloride"),
    ("Polystyrene", "Polymer", r"\bpolystyrene\b"),
    ("Polyolefin", "Polymer", r"\bpolyolefins?\b"),
    ("Microplastics", "Polymer", r"\bmicroplastics?\b"),
    ("Nanoplastics", "Polymer", r"\bnanoplastics?\b"),
    # Processes
    ("Catalysed Cracking", "Process", r"catalys?ed cracking|catalytic cracking"),
    ("Pyrolysis", "Process", r"\bpyrolysis\b|\bpyrolytic\b"),
    ("Chemical Recycling", "Process", r"chemical recycling"),
    ("Mechanical Recycling", "Process", r"mechanical recycling"),
    ("Biodegradation", "Process", r"\bbiodegradation\b|enzymatic degradation"),
    ("Photodegradation", "Process", r"\bphotodegradation\b"),
    ("Depolymerization", "Process", r"depolymeri[sz]ation|\bglycolysis\b"),
    ("Gasification", "Process", r"\bgasification\b"),
    ("Incineration", "Process", r"\bincineration\b"),
    ("Landfilling", "Process", r"\blandfilling\b"),
    ("Thermal Cracking", "Process", r"thermal cracking"),
    # Catalysts / enzymes
    ("ZSM-5", "Catalyst", r"\bZSM-5\b"),
    ("Zinc Acetate", "Catalyst", r"zinc acetate"),
    ("Nickel Catalyst", "Catalyst", r"nickel catalyst"),
    ("Y-Zeolite", "Catalyst", r"\bY-zeolite\b"),
    ("PETase", "Catalyst", r"\bPETase\b"),
    ("Catalyst", "Catalyst", r"\bcatalysts?\b"),
    # Products / monomers
    ("Pyrolysis Oil", "Product", r"pyrolysis oil|liquid oil|\boil\b"),
    ("Syngas", "Product", r"\bsyngas\b"),
    ("Hydrogen", "Product", r"\bhydrogen\b|\bH2\b"),
    ("BHET (Monomer)", "Monomer", r"\bBHET\b|\bmonomers?\b"),
    ("Gasoline-range Hydrocarbons", "Product", r"gasoline-range hydrocarbons"),
    ("Aromatic Hydrocarbons", "Product", r"aromatic hydrocarbons"),
    ("Wax", "Product", r"\bwax\b"),
    ("Tar", "Product", r"\btar\b"),
    ("HCl", "Product", r"\bHCl\b"),
    ("Diesel", "Product", r"\bdiesel\b"),
    # Outcomes / measured properties
    ("Yield", "Outcome", r"\byield\b"),
    ("Conversion", "Outcome", r"\bconversion\b"),
    ("Energy Recovery", "Outcome", r"energy recovery|calorific value"),
    ("Emissions", "Outcome", r"greenhouse gas emissions|\bemissions\b"),
    ("Recycling Efficiency", "Outcome", r"recycling efficiency|material recovery"),
    ("Mechanical Strength", "Outcome", r"mechanical strength|intrinsic viscosity"),
    ("Catalyst Activity", "Outcome", r"catalyst activity|catalyst deactivation"),
    ("Environmental Impact", "Outcome", r"environmental impact"),
    ("Toxicity", "Outcome", r"\btoxicity\b"),
    ("Monomer Purity", "Outcome", r"monomer purity"),
    ("Degradation Extent", "Outcome", r"\bdegraded\b"),
    # Research concepts
    ("Waste-to-Energy", "Concept", r"waste-to-energy"),
    ("Circular Economy", "Concept", r"circular economy"),
    ("Plastic Waste Management", "Concept", r"plastic waste management"),
    ("Sustainable Recycling", "Concept", r"sustainable recycling"),
]
_CASE_SENSITIVE = {"PET", "Polypropylene (PP)", "HCl"}
ENTITY_REGEX = [(n, t, re.compile(p, 0 if n in _CASE_SENSITIVE else re.I))
                for n, t, p in ENTITY_PATTERNS]

SUBJECT_TYPES = ["Process", "Catalyst", "Polymer", "Concept", "Product", "Monomer"]

FINDING_CUES = re.compile(
    r"\b(achiev\w+|produc\w+|increas\w+|decreas\w+|reduc\w+|improv\w+|enhanc\w+|degrad\w+|"
    r"generat\w+|demonstrat\w+|found|reported|limit\w+|releas\w+|reached|dominated|observed|"
    r"comparable|higher|lower|inefficient|indicat\w+|suggest\w+|supporting|complement|"
    r"compared|may|might|could|remains?|unclear|uncertain)\b", re.I)
DESCRIPTIVE_ONLY = re.compile(
    r"\b(was|were) (investigated|studied|examined|evaluated|assessed|quantified)\b|^A review of", re.I)

POSITIVE = re.compile(r"\b(achiev\w+|increas\w+|improv\w+|enhanc\w+|produc\w+|generat\w+|"
                      r"promising|higher|comparable|supporting|demonstrat\w+)\b", re.I)
NEGATIVE = re.compile(r"\b(reduc\w+|decreas\w+|limit\w+|inefficient|lower|deactivation|"
                      r"released|dominated)\b", re.I)

U3_CUES = re.compile(r"inconclusive|unclear|not fully understood|uncertain|"
                     r"further (pilot-scale )?(studies|investigation|research)|"
                     r"field data are limited|requires? further", re.I)
U2_CUES = re.compile(r"\b(may|might|could|suggest\w*|potential|possibly|likely|indicating)\b", re.I)
UNCERTAINTY_LEVELS = {
    "U1": "Low uncertainty: direct, quantified or explicitly demonstrated result",
    "U2": "Moderate uncertainty: hedged or suggestive statement",
    "U3": "High uncertainty: inconclusive, unclear or needs further study",
}

TEMP_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[°º]\s*C", re.I)
TIME_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(min|minutes|h|hr|hours)\b", re.I)
NO_CATALYST_RE = re.compile(r"without a catalyst|non-catalytic|no catalyst", re.I)
MEDIUM_RE = re.compile(r"\bwith (steam)\b|\bunder (UV irradiation)\b|\b(aqueous suspension)\b", re.I)
