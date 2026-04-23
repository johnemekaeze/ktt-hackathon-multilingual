"""
Synthetic data generator for T2.2 — Multilingual Grant & Tender Matcher.
Reproducible: `python generate_data.py`
Produces:
  - tenders/tender_XX.txt  (24 EN)
  - tenders/tender_XX.html (8 EN)
  - tenders/tender_XX.txt  (8 FR txt, total 40 tenders)
  - profiles.json
  - gold_matches.csv
Run time: < 2 minutes on CPU.
"""

import json
import os
import random
import csv
from datetime import datetime, timedelta

random.seed(42)

# ── Slots ────────────────────────────────────────────────────────────────────
SECTORS = ["agritech", "healthtech", "cleantech", "edtech", "fintech", "wastetech"]
BUDGETS_EN = ["USD 5,000", "USD 50,000", "USD 200,000", "USD 1,000,000"]
BUDGETS_FR = ["5 000 USD", "50 000 USD", "200 000 USD", "1 000 000 USD"]
REGIONS_EN = ["East Africa", "West Africa", "Central Africa", "Southern Africa", "Pan-Africa"]
REGIONS_FR = ["Afrique de l'Est", "Afrique de l'Ouest", "Afrique Centrale", "Afrique Australe", "Pan-Afrique"]
COUNTRIES   = ["Rwanda", "Kenya", "Senegal", "DRC", "Ethiopia", "Uganda", "Tanzania", "Ghana", "Nigeria", "Cameroon"]
ORGS_EN = [
    "African Development Fund", "GreenAfrica Initiative", "AU Innovation Hub",
    "ECOWAS Development Bank", "EAC Secretariat", "SADC Grant Facility",
    "World Bank Africa Office", "USAID East Africa", "GIZ Africa Programme", "UNDP Africa"
]
ORGS_FR = [
    "Fonds de Développement Africain", "Initiative Verte Afrique", "Hub Innovation UA",
    "Banque de Développement CEDEAO", "Secrétariat EAC", "Facilité de Subventions SADC",
    "Bureau Afrique Banque Mondiale", "USAID Afrique de l'Est", "Programme Afrique GIZ", "PNUD Afrique"
]

BOILERPLATE_EN = [
    "Applications must comply with all regional procurement guidelines.",
    "The issuing body reserves the right to cancel or modify this tender at any time.",
    "All submitted documents become the property of the issuing organization.",
    "Incomplete applications will be disqualified without further notice.",
    "Organizations with prior convictions for fraud are ineligible.",
    "Financial statements for the last three fiscal years must be attached.",
    "A signed declaration of non-conflict-of-interest is mandatory.",
    "The grant is non-transferable and must be used within the stated jurisdiction.",
    "Environmental and social impact assessments must accompany applications.",
    "Priority will be given to women-led and youth-led enterprises.",
]

BOILERPLATE_FR = [
    "Les candidatures doivent respecter toutes les directives régionales d'approvisionnement.",
    "L'organisme émetteur se réserve le droit d'annuler ou de modifier cet appel à tout moment.",
    "Tous les documents soumis deviennent la propriété de l'organisation émettrice.",
    "Les dossiers incomplets seront disqualifiés sans préavis.",
    "Les organisations condamnées pour fraude sont inéligibles.",
    "Les états financiers des trois derniers exercices doivent être joints.",
    "Une déclaration signée d'absence de conflit d'intérêts est obligatoire.",
    "La subvention est non transférable et doit être utilisée dans la juridiction indiquée.",
    "Des évaluations environnementales et sociales doivent accompagner les candidatures.",
    "La priorité sera accordée aux entreprises dirigées par des femmes et des jeunes.",
]

ELIGIBILITY_EN = [
    "SMEs registered in AU member states with at least 2 years of operation.",
    "Non-governmental organizations with proven track record in the stated sector.",
    "Cooperatives with a minimum of 20 registered members.",
    "Technology startups with a validated prototype or MVP.",
    "Community-based organizations with local government endorsement.",
]
ELIGIBILITY_FR = [
    "PME immatriculées dans les États membres de l'UA avec au moins 2 ans d'activité.",
    "Organisations non gouvernementales avec un bilan prouvé dans le secteur indiqué.",
    "Coopératives avec un minimum de 20 membres enregistrés.",
    "Startups technologiques avec un prototype validé ou un MVP.",
    "Organisations communautaires avec l'approbation du gouvernement local.",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def rand_deadline(days_min=30, days_max=300):
    return (datetime.today() + timedelta(days=random.randint(days_min, days_max))).strftime("%Y-%m-%d")

def rand_boilerplate(pool, n=4):
    return " ".join(random.sample(pool, n))


# ── Tender generators ─────────────────────────────────────────────────────────
def make_tender_en(tid, sector, budget, org, region):
    deadline = rand_deadline()
    eligibility = random.choice(ELIGIBILITY_EN)
    boiler = rand_boilerplate(BOILERPLATE_EN)
    title = f"{org} — {sector.capitalize()} Development Grant {tid:02d}"
    body = (
        f"TITLE: {title}\n"
        f"ISSUING BODY: {org}\n"
        f"SECTOR: {sector}\n"
        f"BUDGET: {budget}\n"
        f"DEADLINE: {deadline}\n"
        f"REGION: {region}\n"
        f"ELIGIBILITY: {eligibility}\n\n"
        f"DESCRIPTION:\n"
        f"This grant supports innovative {sector} solutions that address key development "
        f"challenges across {region}. Funded projects must demonstrate measurable impact "
        f"on at least 500 beneficiaries within the first year of implementation. "
        f"Applicants are expected to present a detailed work plan, budget breakdown, and "
        f"monitoring framework aligned with the Sustainable Development Goals.\n\n"
        f"ADMINISTRATIVE NOTES:\n{boiler}\n"
    )
    return title, deadline, sector, budget, region, "en", body


def make_tender_fr(tid, sector, budget_fr, org_fr, region_fr):
    deadline = rand_deadline()
    eligibility = random.choice(ELIGIBILITY_FR)
    boiler = rand_boilerplate(BOILERPLATE_FR)
    title = f"{org_fr} — Subvention {sector.capitalize()} Nº{tid:02d}"
    body = (
        f"TITRE: {title}\n"
        f"ORGANISME ÉMETTEUR: {org_fr}\n"
        f"SECTEUR: {sector}\n"
        f"BUDGET: {budget_fr}\n"
        f"DATE LIMITE: {deadline}\n"
        f"RÉGION: {region_fr}\n"
        f"ÉLIGIBILITÉ: {eligibility}\n\n"
        f"DESCRIPTION:\n"
        f"Cette subvention soutient les solutions innovantes en {sector} qui répondent aux "
        f"principaux défis du développement à travers {region_fr}. Les projets financés doivent "
        f"démontrer un impact mesurable sur au moins 500 bénéficiaires au cours de la première "
        f"année de mise en œuvre. Les candidats doivent présenter un plan de travail détaillé, "
        f"une ventilation budgétaire et un cadre de suivi aligné sur les Objectifs de Développement Durable.\n\n"
        f"NOTES ADMINISTRATIVES:\n{boiler}\n"
    )
    return title, deadline, sector, budget_fr, region_fr, "fr", body


# ── Write tenders ─────────────────────────────────────────────────────────────
os.makedirs("tenders", exist_ok=True)

tender_records = []   # list of dicts for gold_matches generation
tid = 1

# 24 EN .txt
for i in range(24):
    sector  = SECTORS[i % len(SECTORS)]
    budget  = BUDGETS_EN[i % len(BUDGETS_EN)]
    org     = ORGS_EN[i % len(ORGS_EN)]
    region  = REGIONS_EN[i % len(REGIONS_EN)]
    title, deadline, sec, bud, reg, lang, body = make_tender_en(tid, sector, budget, org, region)
    fname = f"tender_{tid:02d}.txt"
    with open(f"tenders/{fname}", "w", encoding="utf-8") as f:
        f.write(body)
    tender_records.append({"id": f"tender_{tid:02d}", "file": fname, "title": title,
                            "sector": sec, "budget": bud, "deadline": deadline,
                            "region": reg, "language": lang})
    tid += 1

# 8 EN .html
for i in range(8):
    sector  = SECTORS[i % len(SECTORS)]
    budget  = BUDGETS_EN[(i + 1) % len(BUDGETS_EN)]
    org     = ORGS_EN[(i + 2) % len(ORGS_EN)]
    region  = REGIONS_EN[(i + 1) % len(REGIONS_EN)]
    title, deadline, sec, bud, reg, lang, body = make_tender_en(tid, sector, budget, org, region)
    fname = f"tender_{tid:02d}.html"
    html_body = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title></head><body>"
        f"<h1>{title}</h1>"
        f"<table border='1'>"
        f"<tr><th>Sector</th><td>{sec}</td></tr>"
        f"<tr><th>Budget</th><td>{bud}</td></tr>"
        f"<tr><th>Deadline</th><td>{deadline}</td></tr>"
        f"<tr><th>Region</th><td>{reg}</td></tr>"
        f"</table>"
        f"<p>{body.split('DESCRIPTION:')[1].split('ADMINISTRATIVE')[0].strip()}</p>"
        f"</body></html>"
    )
    with open(f"tenders/{fname}", "w", encoding="utf-8") as f:
        f.write(html_body)
    tender_records.append({"id": f"tender_{tid:02d}", "file": fname, "title": title,
                            "sector": sec, "budget": bud, "deadline": deadline,
                            "region": reg, "language": lang})
    tid += 1

# 8 FR .txt  (total = 40)
for i in range(8):
    sector   = SECTORS[i % len(SECTORS)]
    budget   = BUDGETS_FR[i % len(BUDGETS_FR)]
    org_fr   = ORGS_FR[i % len(ORGS_FR)]
    region_fr = REGIONS_FR[i % len(REGIONS_FR)]
    title, deadline, sec, bud, reg, lang, body = make_tender_fr(tid, sector, budget, org_fr, region_fr)
    fname = f"tender_{tid:02d}.txt"
    with open(f"tenders/{fname}", "w", encoding="utf-8") as f:
        f.write(body)
    tender_records.append({"id": f"tender_{tid:02d}", "file": fname, "title": title,
                            "sector": sec, "budget": bud, "deadline": deadline,
                            "region": reg, "language": lang})
    tid += 1

print(f"✅ Generated {len(tender_records)} tenders in tenders/")

# ── profiles.json ─────────────────────────────────────────────────────────────
PROFILE_COUNTRIES = ["Rwanda", "Kenya", "Senegal", "DRC", "Ethiopia",
                     "Uganda", "Tanzania", "Ghana", "Rwanda", "Kenya"]
PROFILE_LANGS     = [["en"], ["en"], ["fr"], ["fr"], ["en"],
                     ["en"], ["sw", "en"], ["en"], ["fr", "en"], ["en"]]
PROFILE_SECTORS   = ["agritech", "healthtech", "cleantech", "fintech",
                     "edtech", "wastetech", "agritech", "healthtech",
                     "cleantech", "fintech"]
PROFILE_EMPLOYEES = [5, 12, 3, 8, 20, 6, 15, 9, 4, 30]
NEEDS = [
    "We need funding to scale our drone-based crop monitoring service for smallholder farmers.",
    "Seeking grants to deploy low-cost diagnostic kits in rural health clinics.",
    "Looking for financing to install solar micro-grids in off-grid communities.",
    "Need capital to expand mobile money services to unbanked rural populations.",
    "Seeking support to digitize secondary school curricula in underserved regions.",
    "Require funding for community waste collection and composting infrastructure.",
    "Looking for grants to build an AI-powered market linkage platform for cooperatives.",
    "Need financing to scale telemedicine services across remote districts.",
    "Seeking investment to deploy wind energy solutions in arid regions.",
    "Looking for funding to launch a savings and credit cooperative platform.",
]
PAST_FUNDING = [
    "World Bank small grant 2023",
    "None",
    "AFD pilot grant 2022",
    "None",
    "USAID seed grant 2024",
    "GIZ micro-grant 2023",
    "None",
    "UNDP innovation fund 2024",
    "EU Horizon Africa 2023",
    "None",
]

profiles = []
for i in range(10):
    profiles.append({
        "id": f"{i+1:02d}",
        "sector": PROFILE_SECTORS[i],
        "country": PROFILE_COUNTRIES[i],
        "employees": PROFILE_EMPLOYEES[i],
        "languages": PROFILE_LANGS[i],
        "needs_text": NEEDS[i],
        "past_funding": PAST_FUNDING[i],
    })

with open("profiles.json", "w", encoding="utf-8") as f:
    json.dump(profiles, f, indent=2, ensure_ascii=False)
print("✅ Generated profiles.json (10 profiles)")

# ── gold_matches.csv ──────────────────────────────────────────────────────────
# For each profile, pick the 3 tenders whose sector matches best
def best_tenders_for_profile(profile, all_tenders, n=3):
    sector = profile["sector"]
    # Prioritize exact sector match, then same language
    matched = [t for t in all_tenders if t["sector"] == sector]
    random.shuffle(matched)
    return [t["id"] for t in matched[:n]]

with open("gold_matches.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["profile_id", "tender_id", "rank"])
    for profile in profiles:
        matches = best_tenders_for_profile(profile, tender_records)
        for rank, tender_id in enumerate(matches, 1):
            writer.writerow([profile["id"], tender_id, rank])

print("✅ Generated gold_matches.csv (3 matches × 10 profiles = 30 rows)")
print("\n🏁 All data generated. Run: python matcher.py --profile 01 --topk 5")
