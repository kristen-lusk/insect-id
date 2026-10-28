"""
Lay (common) names for taxa. Add your own lines; keys are scientific names.
Only entries I'm confident about are included. Edit freely.
"""

COMMON = {
    # ---- orders ----
    "Coleoptera": "beetles", "Lepidoptera": "butterflies and moths", "Diptera": "true flies",
    "Hymenoptera": "bees, wasps, ants and sawflies", "Hemiptera": "true bugs, cicadas, aphids and hoppers",
    "Orthoptera": "grasshoppers, crickets and katydids", "Odonata": "dragonflies and damselflies",
    "Blattodea": "cockroaches and termites", "Mantodea": "mantises", "Neuroptera": "lacewings, antlions and relatives",
    "Dermaptera": "earwigs", "Phasmatodea": "stick and leaf insects", "Thysanoptera": "thrips",
    "Trichoptera": "caddisflies", "Ephemeroptera": "mayflies", "Plecoptera": "stoneflies",
    "Siphonaptera": "fleas", "Mecoptera": "scorpionflies and relatives",
    # ---- families ----
    "Chrysomelidae": "leaf beetles", "Coccinellidae": "lady beetles (ladybugs)", "Cerambycidae": "longhorn beetles",
    "Scarabaeidae": "scarab beetles", "Curculionidae": "weevils", "Carabidae": "ground beetles",
    "Tenebrionidae": "darkling beetles", "Elateridae": "click beetles", "Lampyridae": "fireflies (lightning bugs)",
    "Staphylinidae": "rove beetles", "Dytiscidae": "predaceous diving beetles",
    "Formicidae": "ants", "Apidae": "bees (honey, bumble, carpenter and others)", "Vespidae": "hornets, yellowjackets and paper wasps",
    "Nymphalidae": "brush-footed butterflies", "Papilionidae": "swallowtails", "Pieridae": "whites and sulphurs",
    "Lycaenidae": "blues, coppers and hairstreaks", "Hesperiidae": "skippers", "Noctuidae": "owlet moths",
    "Sphingidae": "hawk moths", "Saturniidae": "giant silkmoths", "Geometridae": "geometer moths (inchworms)",
    "Gerridae": "water striders", "Acrididae": "short-horned grasshoppers", "Gryllidae": "true crickets",
    "Tettigoniidae": "katydids", "Drosophilidae": "small fruit flies (vinegar flies)", "Tephritidae": "true fruit flies",
    "Culicidae": "mosquitoes", "Muscidae": "house flies and relatives", "Syrphidae": "hover flies",
    "Tipulidae": "crane flies", "Tabanidae": "horse flies and deer flies", "Calliphoridae": "blow flies",
    "Pentatomidae": "stink bugs", "Reduviidae": "assassin bugs", "Miridae": "plant bugs", "Coreidae": "leaf-footed bugs",
    "Cicadidae": "cicadas", "Cicadellidae": "leafhoppers", "Membracidae": "treehoppers", "Aphididae": "aphids",
    "Libellulidae": "skimmers (dragonflies)", "Coenagrionidae": "narrow-winged damselflies", "Mantidae": "mantises",
    # ---- genera ----
    "Leptinotarsa": "Colorado potato beetle and relatives", "Drosophila": "fruit flies (vinegar flies)",
    "Apis": "honey bees", "Bombus": "bumble bees", "Xylocopa": "carpenter bees", "Musca": "house flies",
    "Aedes": "Aedes mosquitoes", "Anopheles": "Anopheles mosquitoes", "Culex": "Culex mosquitoes",
    "Harmonia": "lady beetles (includes the multicolored Asian lady beetle)", "Coccinella": "lady beetles",
    "Danaus": "milkweed butterflies (includes the monarch)", "Papilio": "swallowtails", "Pieris": "cabbage whites",
    "Cicindela": "tiger beetles", "Photinus": "fireflies", "Lucanus": "stag beetles", "Tribolium": "flour beetles",
    "Cimex": "bed bugs", "Periplaneta": "large cockroaches (includes the American cockroach)",
    "Blattella": "small cockroaches (includes the German cockroach)", "Camponotus": "carpenter ants",
    "Solenopsis": "fire ants", "Vespula": "yellowjackets", "Polistes": "paper wasps", "Vespa": "hornets",
    "Gerris": "water striders", "Aquarius": "water striders",
    "Cassida": "tortoise beetles", "Charidotella": "tortoise beetles (includes the golden tortoise beetle)",
    "Metriona": "tortoise beetles", "Microctenochira": "tortoise beetles",
}


def lay_name(name, auto=None, exact=False):
    """
    Returns (text, is_guess) or (None, False).
    Curated names win. `auto` is a common name taken from a species inside the
    group (or from the species itself when exact=True).
    """
    if name in COMMON:
        return COMMON[name], False
    if auto:
        return (auto, False) if exact else (f"e.g., {auto}", True)
    return None, False
