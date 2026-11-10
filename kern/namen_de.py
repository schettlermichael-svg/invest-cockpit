"""Deutsche Namen für Yahoos Sektoren und Branchen und die deutschen Unternehmensbeschreibungen
(daten/steckbrief_de/beschreibungen.json, von Claude aus Yahoos englischem Text übertragen; neue Titel ergänzt der
Nachtlauf)."""
import os

PFAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "daten", "steckbrief_de", "beschreibungen.json")

SEKTOR = {
    "Basic Materials": "Grundstoffe", "Communication Services": "Kommunikation", "Consumer Cyclical": "Zyklischer Konsum",
    "Consumer Defensive": "Basiskonsum", "Energy": "Energie", "Financial Services": "Finanzen", "Healthcare": "Gesundheit",
    "Industrials": "Industrie", "Real Estate": "Immobilien", "Technology": "Technologie", "Utilities": "Versorger",
}

BRANCHE = {
    "Advertising Agencies": "Werbeagenturen", "Aerospace & Defense": "Luft- und Raumfahrt, Verteidigung",
    "Agricultural Inputs": "Agrarbedarf", "Airlines": "Fluggesellschaften",
    "Airports & Air Services": "Flughäfen und Flugdienste", "Aluminum": "Aluminium",
    "Apparel Manufacturing": "Bekleidungshersteller", "Apparel Retail": "Bekleidungshandel",
    "Asset Management": "Vermögensverwaltung", "Auto & Truck Dealerships": "Auto- und Lkw-Händler",
    "Auto Manufacturers": "Autohersteller", "Auto Parts": "Autozulieferer", "Banks - Diversified": "Großbanken",
    "Banks - Regional": "Regionalbanken", "Beverages - Brewers": "Brauereien",
    "Beverages - Non-Alcoholic": "Alkoholfreie Getränke", "Beverages - Wineries & Distilleries": "Wein und Spirituosen",
    "Biotechnology": "Biotechnologie", "Broadcasting": "Rundfunk", "Building Materials": "Baustoffe",
    "Building Products & Equipment": "Bauprodukte und -ausrüstung", "Business Equipment & Supplies": "Bürobedarf",
    "Capital Markets": "Kapitalmärkte", "Chemicals": "Chemie", "Coking Coal": "Kokskohle",
    "Communication Equipment": "Kommunikationstechnik", "Computer Hardware": "Computer-Hardware",
    "Confectioners": "Süßwaren", "Conglomerates": "Mischkonzerne", "Consulting Services": "Beratung",
    "Consumer Electronics": "Unterhaltungselektronik", "Copper": "Kupfer", "Credit Services": "Kreditdienstleister",
    "Department Stores": "Kaufhäuser", "Diagnostics & Research": "Diagnostik und Forschung",
    "Discount Stores": "Discounter", "Drug Manufacturers - General": "Pharmakonzerne",
    "Drug Manufacturers - Specialty & Generic": "Spezial- und Generika-Pharma",
    "Education & Training Services": "Bildung und Weiterbildung",
    "Electrical Equipment & Parts": "Elektrische Ausrüstung", "Electronic Components": "Elektronische Bauteile",
    "Electronic Gaming & Multimedia": "Videospiele und Multimedia",
    "Electronics & Computer Distribution": "Elektronik- und Computervertrieb",
    "Engineering & Construction": "Ingenieur- und Bauwesen", "Entertainment": "Unterhaltung",
    "Farm & Heavy Construction Machinery": "Land- und Baumaschinen", "Farm Products": "Agrarprodukte",
    "Financial Conglomerates": "Finanzkonglomerate", "Financial Data & Stock Exchanges": "Finanzdaten und Börsen",
    "Food Distribution": "Lebensmittelgroßhandel", "Footwear & Accessories": "Schuhe und Accessoires",
    "Furnishings, Fixtures & Appliances": "Einrichtung und Haushaltsgeräte", "Gambling": "Glücksspiel",
    "Gold": "Gold", "Grocery Stores": "Lebensmittelhandel", "Health Information Services": "Gesundheits-IT",
    "Healthcare Plans": "Krankenversicherer", "Home Improvement Retail": "Baumärkte",
    "Household & Personal Products": "Haushalts- und Körperpflege", "Industrial Distribution": "Industriegroßhandel",
    "Information Technology Services": "IT-Dienstleistungen", "Insurance - Diversified": "Versicherungskonzerne",
    "Insurance - Life": "Lebensversicherer", "Insurance - Property & Casualty": "Sachversicherer",
    "Insurance - Reinsurance": "Rückversicherer", "Insurance - Specialty": "Spezialversicherer",
    "Insurance Brokers": "Versicherungsmakler", "Integrated Freight & Logistics": "Fracht und Logistik",
    "Internet Content & Information": "Internetinhalte", "Internet Retail": "Onlinehandel", "Leisure": "Freizeit",
    "Lodging": "Hotels", "Lumber & Wood Production": "Holz", "Luxury Goods": "Luxusgüter",
    "Marine Shipping": "Seeschifffahrt", "Medical Care Facilities": "Kliniken und Pflege",
    "Medical Devices": "Medizintechnik", "Medical Distribution": "Medizingroßhandel",
    "Medical Instruments & Supplies": "Medizinbedarf", "Metal Fabrication": "Metallverarbeitung",
    "Mortgage Finance": "Hypothekenfinanzierung", "Oil & Gas Drilling": "Öl- und Gasbohrung",
    "Oil & Gas E&P": "Öl- und Gasförderung", "Oil & Gas Equipment & Services": "Öl- und Gasausrüstung",
    "Oil & Gas Integrated": "Integrierte Ölkonzerne", "Oil & Gas Midstream": "Pipelines und Speicher",
    "Oil & Gas Refining & Marketing": "Raffinerien", "Other Industrial Metals & Mining": "Industriemetalle und Bergbau",
    "Other Precious Metals & Mining": "Edelmetalle", "Packaged Foods": "Nahrungsmittel",
    "Packaging & Containers": "Verpackungen", "Personal Services": "Persönliche Dienstleistungen",
    "Pollution & Treatment Controls": "Umwelttechnik", "Publishing": "Verlage",
    "REIT - Diversified": "REIT gemischt", "REIT - Healthcare Facilities": "REIT Gesundheitsimmobilien",
    "REIT - Hotel & Motel": "REIT Hotels", "REIT - Industrial": "REIT Logistik und Industrie",
    "REIT - Mortgage": "REIT Hypotheken", "REIT - Office": "REIT Büro", "REIT - Residential": "REIT Wohnen",
    "REIT - Retail": "REIT Handel", "REIT - Specialty": "REIT Spezial", "Railroads": "Eisenbahnen",
    "Real Estate - Development": "Projektentwicklung", "Real Estate Services": "Immobiliendienstleistungen",
    "Recreational Vehicles": "Freizeitfahrzeuge", "Rental & Leasing Services": "Vermietung und Leasing",
    "Residential Construction": "Wohnungsbau", "Resorts & Casinos": "Resorts und Casinos", "Restaurants": "Restaurants",
    "Scientific & Technical Instruments": "Mess- und Prüfgeräte", "Security & Protection Services": "Sicherheitsdienste",
    "Semiconductor Equipment & Materials": "Halbleiterausrüstung", "Semiconductors": "Halbleiter", "Silver": "Silber",
    "Software - Application": "Anwendungssoftware", "Software - Infrastructure": "Infrastruktursoftware",
    "Solar": "Solar", "Specialty Business Services": "Unternehmensdienste", "Specialty Chemicals": "Spezialchemie",
    "Specialty Industrial Machinery": "Spezialmaschinenbau", "Specialty Retail": "Fachhandel",
    "Staffing & Employment Services": "Personaldienstleister", "Steel": "Stahl", "Telecom Services": "Telekommunikation",
    "Thermal Coal": "Kraftwerkskohle", "Tobacco": "Tabak", "Tools & Accessories": "Werkzeuge",
    "Travel Services": "Reisedienste", "Trucking": "Spedition", "Uranium": "Uran",
    "Utilities - Diversified": "Versorger gemischt", "Utilities - Independent Power Producers": "Unabhängige Stromerzeuger",
    "Utilities - Regulated Electric": "Stromversorger", "Utilities - Regulated Gas": "Gasversorger",
    "Utilities - Regulated Water": "Wasserversorger", "Utilities - Renewable": "Erneuerbare Energien",
    "Waste Management": "Entsorgung",
}

_beschreibungen = None
_stand = None



def branche(name):
    """Deutscher Branchenname; auch für mit „ · “ verbundene Namen (Themen-Gruppen)."""
    if not name:
        return name
    return " · ".join(BRANCHE.get(n, SEKTOR.get(n, n)) for n in str(name).split(" · "))
