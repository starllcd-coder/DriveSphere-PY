from .models import VehicleBrand, VehicleModel, VehicleCategory


VEHICLE_BRANDS_MODELS = {
    # extended Toyota models
    "Toyota": [
        "Corolla",
        "Camry",
        "RAV4",
        "Hilux",
        "Land Cruiser",
        "Prado",
        "Fortuner",
        "C-HR",
        "Yaris",
        "Yaris Cross",
        "Prius",
        "Avalon",
        "Sienna",
        "Tacoma",
        "Tundra",
    ],
    "Honda": ["Civic", "Accord", "CR-V", "HR-V", "City"],
    "Nissan": ["Sunny", "Altima", "X-Trail", "Patrol", "Qashqai"],
    "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe", "Accent"],
    "Kia": ["Cerato", "Optima", "Sportage", "Sorento", "Seltos"],
    "Ford": ["Focus", "Fusion", "Escape", "Explorer", "Ranger"],
    "Chevrolet": ["Cruze", "Malibu", "Captiva", "Tahoe", "Silverado"],
    "Volkswagen": ["Golf", "Passat", "Tiguan", "Jetta", "Touareg"],
    "Audi": ["A3", "A4", "A6", "Q5", "Q7"],
    "BMW": ["3 Series", "5 Series", "X3", "X5", "X7"],
    "Mercedes-Benz": ["C-Class", "E-Class", "S-Class", "GLC", "GLE"],
    "Lexus": ["ES", "IS", "RX", "NX", "LX"],
    "Tesla": ["Model 3", "Model S", "Model X", "Model Y"],
    "Volvo": ["S60", "S90", "XC40", "XC60", "XC90"],
    "Subaru": ["Impreza", "Legacy", "Forester", "Outback", "XV"],
    "Mazda": ["Mazda3", "Mazda6", "CX-5", "CX-30", "CX-9"],
    "Mitsubishi": ["Lancer", "Outlander", "Pajero", "ASX", "Mirage"],
    "Suzuki": ["Swift", "Vitara", "Ciaz", "Jimny", "Baleno"],
    "Renault": ["Clio", "Megane", "Duster", "Captur", "Koleos"],
    "Peugeot": ["208", "308", "3008", "5008", "Partner"],
    "Skoda": ["Octavia", "Superb", "Karoq", "Kodiaq", "Fabia"],
    "Land Rover": ["Discovery", "Range Rover", "Defender", "Evoque", "Sport"],
    "Jeep": ["Wrangler", "Cherokee", "Grand Cherokee", "Compass", "Renegade"],
    "Dodge": ["Charger", "Challenger", "Durango", "Journey", "Caravan"],
    "RAM": ["1500", "2500", "3500", "ProMaster", "TRX"],
    "Infiniti": ["Q50", "Q60", "QX50", "QX60", "QX80"],
    "BYD": ["Atto 3", "Dolphin", "Seal", "Song Plus", "Tang", "Han", "Qin Plus", "Yuan Plus"],
    "Geely": ["Coolray", "Emgrand", "Azkarra", "Tugella", "Okavango"],
    "Chery": ["Tiggo 8", "Tiggo 7", "Tiggo 4 Pro", "Arrizo 5", "Arrizo 6"],
    "Great Wall": ["Poer", "Cannon", "Wingle 7", "Tank 300", "Tank 500"],
    "Haval": ["H6", "Jolion", "H9", "H2", "Dargo"],
    "MG": ["MG5", "MG6", "MG ZS", "MG HS", "MG RX5"],
    "Wuling": ["Mini EV", "Hongguang", "Almaz", "Cortez", "Sunshine"],
    "Changan": ["CS35 Plus", "CS55 Plus", "CS75 Plus", "Alsvin", "UNI-T"],
    "Dongfeng": ["AX7", "T5", "T5 EVO", "Glory 560", "Rich 6"],
    "BAIC": ["X35", "X55", "X7", "BJ40", "BJ80"],
    "JAC": ["S2", "S3", "S4", "T6", "T8"],
    "GAC": ["GS3", "GS4", "GS5", "GS8", "Empow"],
    "FAW Bestune": ["T55", "T77", "T99", "B70", "B50"],
    "NIO": ["ES6", "ES8", "ET5", "ET7", "EC6"],
    "XPeng": ["P7", "G3", "G6", "G9", "P5"],
    "Li Auto": ["L7", "L8", "L9"],
    "Hongqi": ["H5", "H7", "H9", "E-HS9", "HS5"],
    "Lynk and Co": ["01", "02", "03", "05", "06"],
    "Zeekr": ["001", "009", "X", "007"],
    "Jetour": ["X70", "X90", "Dashing", "X95", "Traveler"],
    "Exeed": ["TXL", "VX", "LX", "RX", "TX"],
    "Omoda": ["C5", "E5", "C7", "C3", "C9"],
    "DFSK": ["Glory 580", "Glory 560", "Fengon 500", "Fengon 600", "K01"],
    "Cadillac": ["CT4", "CT5", "XT4", "XT5", "Escalade"],
    "GMC": ["Terrain", "Acadia", "Yukon", "Sierra"],
    "Porsche": ["911", "Cayenne", "Macan", "Panamera", "Taycan"],
    "Mini": ["Cooper", "Cooper S", "Countryman", "Clubman"],
    "Citroen": ["C3", "C4", "C5 Aircross"],
    "Fiat": ["500", "Panda", "Tipo"],
    "Alfa Romeo": ["Giulia", "Stelvio"],
    "Mahindra": ["Thar", "XUV700", "Scorpio"],
    "Tata Motors": ["Tiago", "Nexon", "Harrier"],
    "Isuzu": ["D-Max", "MU-X"],
}


def ensure_vehicle_brands_models() -> None:
    for brand_name, models in VEHICLE_BRANDS_MODELS.items():
        brand, _ = VehicleBrand.objects.get_or_create(name=brand_name)
        for model_name in models:
            VehicleModel.objects.get_or_create(brand=brand, name=model_name)


# default vehicle categories
VEHICLE_CATEGORIES = [
    "Sedan",
    "Hatchback",
    "SUV",
    "Crossover",
    "Coupe",
    "Convertible",
    "Minivan",
    "Pickup",
    "Wagon",
    "Van",
]


def ensure_vehicle_categories() -> None:
    for name in VEHICLE_CATEGORIES:
        VehicleCategory.objects.get_or_create(name=name)


# helper to ensure brands/models and categories together
def ensure_all_fleet_seed_data() -> None:
    ensure_vehicle_brands_models()
    try:
        # import here to avoid circular imports in some contexts
        from .models import VehicleCategory
    except Exception:
        pass
    ensure_vehicle_categories()
