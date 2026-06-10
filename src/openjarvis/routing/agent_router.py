"""Intelligent agent router — dispatches queries to the best-fitting domain agent.

Two-tier routing:
1. **Keyword tier** — fast deterministic matching via weighted keyword sets.
2. **LLM tier** — semantic classification when keyword tier is ambiguous.

When no agent is explicitly requested via ``--agent``, the router analyses the
query text, scores every registered domain agent, and returns the winner.
If the confidence is below the configured threshold the fallback agent is used.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Keyword registry — weighted per agent
# ---------------------------------------------------------------------------

_KEYWORDS: dict[str, dict[str, float]] = {
    "bavaria_booking": {
        "buchung": 3.0, "zimmer": 3.0, "preis": 3.0, "reservierung": 3.0,
        "übernachtung": 3.0, "gästezimmer": 3.0, "doppelzimmer": 3.0,
        "einzelzimmer": 3.0, "landhaus bavaria": 4.0, "bayerischer wald": 3.5,
        "zwiesel": 3.5, "ferienwohnung": 3.0, "pension": 3.0, "gasthof": 3.0,
        "hotel": 2.0, "room": 2.0, "booking": 2.0, "gast": 2.5, "gäste": 2.5,
        "aufenthalt": 2.5, "nächtigung": 2.5, "halbpension": 2.5,
        "vollpension": 2.5, "frühstück": 2.0, "kurtaxe": 2.5, "saison": 2.5,
        "saisonpreis": 2.5, "zimmerpreis": 2.5, "verfügbarkeit": 2.5,
        "belegung": 2.5, "auslastung": 2.5, "gutschein": 2.0,
        "gutscheincode": 2.5, "rabatt": 2.0, "angebot": 2.0,
        "sonderangebot": 2.5, "arrangement": 2.5, "wochenendarrangement": 3.0,
        "website": 2.0, "homepage": 2.0, "vercel": 2.0, "domain": 2.0,
        "dns": 2.0, "a-record": 2.5, "cname": 2.5, "mx": 2.5, "spf": 2.5,
        "dkim": 2.5, "dmarc": 2.5, "ssl": 2.0, "tls": 2.0, "https": 2.0,
        "redirect": 2.0, "build": 2.0, "deploy": 2.0, "lint": 1.5,
        "eslint": 1.5, "next.js": 2.5, "nextjs": 2.5, "react": 1.5,
        "komponente": 2.0, "komponenten": 2.0, "tailwind": 1.5, "css": 1.5,
        "ical": 2.5, "kalender": 2.0, "sync": 2.5, "synchronisierung": 2.5,
        "booking.com": 2.5, "airbnb": 2.5, "ferienwohnung-direkt": 2.5,
        "deskline": 2.5, "channel-manager": 3.0, "doppelbelegung": 3.0,
        "überbuchung": 3.0, "admin": 2.0, "admin-panel": 2.5, "login": 1.5,
        "session": 1.5, "redis": 2.5, "kv": 2.5, "key-value": 2.0,
        "datenbank": 2.0, "db": 1.5, "prisma": 2.0, "orm": 1.5,
        "api": 2.0, "endpoint": 2.0, "route": 1.5, "stripe": 2.5,
        "zahlung": 2.0, "kasse": 2.0, "rechnung": 2.5, "mwst": 2.0,
        "mehrwertsteuer": 2.0, "zahlungsstatus": 2.5,
    },
    "legal_assistant": {
        "recht": 3.0, "legal": 3.0, "rechtlich": 2.0, "juristisch": 2.5,
        "anwalt": 2.5, "gericht": 2.5, "prozess": 2.0, "klage": 2.5,
        "verurteilung": 2.5, "datenschutz": 3.5, "dsgvo": 4.0,
        "gdpr": 3.5, "dsvgo": 3.5, "personenbezogene daten": 3.5,
        "einwilligung": 3.0, "cookie": 2.5, "cookie-banner": 3.0,
        "tracking": 2.5, "analytics": 2.0, "google analytics": 2.5,
        "matomo": 2.5, "privatsphäre": 2.5, "datenweitergabe": 3.0,
        "auftragsverarbeitung": 3.0, "avv": 3.0, "dsgvo-artikel": 3.0,
        "betroffenenrechte": 3.0, "auskunft": 2.5, "löschung": 2.5,
        "vergessenwerden": 2.5, "datenschutzbeauftragter": 3.0,
        "dsb": 3.0, "tom": 2.5, "technische und organisatorische maßnahmen": 3.5,
        "vertrag": 3.0, "vertragsentwurf": 3.0, "vertragsprüfung": 3.5,
        "agb": 3.0, "allgemeine geschäftsbedingungen": 3.0, "widerruf": 3.0,
        "widerrufsrecht": 3.5, "rücktritt": 2.5, "kündigung": 2.5,
        "kündigungsfrist": 3.0, "haftung": 2.5, "haftungsbeschränkung": 3.0,
        "schadensersatz": 2.5, "gewährleistung": 2.5, "gerichtsstand": 3.0,
        "schlichtung": 2.5, "kmu-de": 3.0, "bgb": 2.5, "hgb": 2.5,
        "urheberrecht": 2.5, "copyright": 2.5, "lizenz": 2.5,
        "markenrecht": 2.5, "patent": 2.0, "bildrecht": 2.5,
        "nutzungsrecht": 2.5, "compliance": 3.0, "regulatorik": 3.0,
        "eu ai-act": 4.0, "ai-act": 3.5, "künstliche intelligenz": 2.5,
        "ki-gesetz": 3.0, "transparenzpflicht": 3.0, "risikostufe": 2.5,
        "gastg": 3.5, "gaststättengesetz": 3.5, "aufstichlizenz": 3.5,
        "gaststättenerlaubnis": 3.5, "lebensmittelrecht": 3.0,
        "hygienerecht": 3.0, "hygienevorschriften": 3.0, "jugendschutz": 3.0,
        "jugendschutzgesetz": 3.0, "alkohol": 2.5, "ausschank": 2.5,
        "schankerlaubnis": 3.0, "arbzg": 3.5, "arbeitszeitgesetz": 3.5,
        "arbeitszeit": 2.5, "arbeitsrecht": 3.0, "arbeitnehmer": 2.5,
        "arbeitgeber": 2.5, "überstunden": 2.5, "ruhezeit": 2.5,
        "pause": 2.0, "pausenregelung": 2.5, "mindestlohn": 2.5,
        "entgelt": 2.5, "lohn": 2.0, "gehalt": 2.0, "urlaubsanspruch": 2.5,
        "krankentage": 2.0, "verbraucherschutz": 3.0, "fernabsatzgesetz": 3.0,
        "bgb-infov": 3.0, "informationspflicht": 3.0,
        "preisangabenverordnung": 3.0, "pangv": 3.0, "preisangaben": 2.5,
        "mwst": 2.5, "mehrwertsteuer": 2.5, "preis": 1.5, "risiko": 2.0,
        "risikobewertung": 2.5, "risikomatrix": 2.5, "abmahnung": 4.0,
        "abmahngefahr": 4.0, "rechtliches risiko": 3.0,
        "rechtssicherheit": 2.5, "impressum": 3.0, "impressumspflicht": 3.5,
        "transparenz": 2.5, "tmg": 2.5, "telemediengesetz": 2.5,
        "diensteanbieter": 2.5, "anschrift": 2.0, "telefon": 1.5,
        "email": 1.5, "ust-id": 2.5, "steuernummer": 2.5,
        "handelsregister": 2.5,
    },
    "marketing_assistant": {
        "marketing": 3.0, "werbung": 2.5, "werbetext": 3.0,
        "copywriting": 2.5, "text": 1.5, "content": 2.0,
        "content marketing": 2.5, "storytelling": 2.5, "marke": 2.5,
        "markenführung": 3.0, "brand": 2.5, "branding": 3.0,
        "brand voice": 3.0, "markenidentität": 3.0,
        "corporate identity": 2.5, "ci": 2.0, "logo": 2.0, "slogan": 2.5,
        "claim": 2.5, "motto": 2.0, "newsletter": 3.5, "email": 2.0,
        "e-mail": 2.0, "mailing": 2.5, "mail": 1.5, "email-marketing": 3.0,
        "email-sequenz": 3.0, "drip-campaign": 2.5, "willkommensmail": 2.5,
        "follow-up": 2.5, "absage": 2.0, "bestätigung": 2.0,
        "buchungsbestätigung": 2.5, "empfangsbestätigung": 2.5,
        "abmeldelink": 2.5, "unsubscribe": 2.0, "abmeldung": 2.0,
        "einwilligung": 2.0, "opt-in": 2.5, "double opt-in": 2.5,
        "öffnungsrate": 2.5, "clickrate": 2.5, "ctr": 2.0,
        "bounce-rate": 2.0, "abwanderungsrate": 2.0, "kampagne": 3.0,
        "kampagnenplanung": 3.5, "campagne": 2.5, "aktion": 2.0,
        "sonderaktion": 2.5, "saisonkampagne": 3.0, "weihnachtskampagne": 3.0,
        "sommerkampagne": 3.0, "osterkampagne": 3.0, "aktionszeitraum": 2.5,
        "zielgruppe": 2.5, "targeting": 2.5, "retargeting": 2.5,
        "remarketing": 2.5, "a/b-test": 3.0, "split-test": 3.0,
        "variante": 2.0, "varianten": 2.0, "conversion": 2.5,
        "konversion": 2.5, "conversion-rate": 2.5, "landing-page": 2.5,
        "zielseite": 2.5, "cta": 2.5, "call-to-action": 2.5,
        "button": 1.5, "funnel": 2.5, "sales-funnel": 2.5,
        "customer journey": 2.5, "guest journey": 2.5, "kundenreise": 2.5,
        "touchpoint": 2.5, "kontaktpunkt": 2.5, "seo": 3.0,
        "suchmaschinenoptimierung": 3.5, "google": 2.0,
        "google ranking": 2.5, "serp": 2.5, "suchergebnis": 2.0,
        "keyword": 2.5, "schlüsselwort": 2.5, "suchbegriff": 2.5,
        "longtail": 2.5, "long-tail": 2.5, "backlink": 2.5,
        "linkaufbau": 2.5, "meta": 2.5, "meta-title": 3.0,
        "meta-description": 3.0, "title-tag": 2.5, "description-tag": 2.5,
        "open graph": 2.5, "og-tags": 2.5, "canonical": 2.5,
        "hreflang": 2.5, "sitemap": 2.0, "robots.txt": 2.0, "crawler": 2.0,
        "indexierung": 2.5, "page-speed": 2.5, "core web vitals": 2.5,
        "lcp": 2.0, "cls": 2.0, "inp": 2.0, "structured data": 2.5,
        "schema.org": 2.5, "rich snippet": 2.5, "local seo": 3.0,
        "google business": 2.5, "google my business": 2.5, "bewertung": 2.5,
        "review": 2.5, "rezension": 2.5, "sterne": 2.0, "social": 2.5,
        "social media": 3.0, "social-media": 3.0, "facebook": 2.0,
        "instagram": 2.0, "tiktok": 2.0, "pinterest": 2.0, "youtube": 2.0,
        "linkedin": 1.5, "xing": 1.5, "twitter": 1.5, "x": 1.5,
        "hashtag": 2.5, "story": 2.0, "reel": 2.0, "shorts": 2.0,
        "post": 1.5, "beitrag": 1.5, "feed": 1.5, "content-plan": 2.5,
        "redaktionsplan": 2.5, "content-kalender": 2.5,
        "veröffentlichungsplan": 2.5, "google ads": 3.0, "adwords": 2.5,
        "sea": 2.5, "suchmaschinenwerbung": 3.0, "facebook ads": 2.5,
        "meta ads": 2.5, "instagram ads": 2.5, "werbebudget": 2.5,
        "cpc": 2.0, "cpm": 2.0, "cost-per-click": 2.0, "roas": 2.0,
        "return on ad spend": 2.0, "werbekosten": 2.0, "analytics": 2.0,
        "webanalyse": 2.5, "tracking": 2.0, "dashboard": 2.0, "kpi": 2.5,
        "kennzahl": 2.5, "kennzahlen": 2.5, "metrik": 2.0, "report": 2.0,
        "bericht": 2.0, "statistik": 2.0, "besucher": 2.0, "pageview": 2.0,
        "seitenaufruf": 2.0, "absprungrate": 2.0, "verweildauer": 2.0,
        "nutzerverhalten": 2.5, "gästebuch": 2.5, "bewertungsplattform": 2.5,
        "holidaycheck": 2.5, "tripadvisor": 2.5, "booking.com extranet": 2.5,
        "partnerhub": 2.0, "genuss": 2.0, "wellness": 2.0, "spa": 2.0,
        "sauna": 2.0, "massage": 2.0, "wandern": 2.0, "radtour": 2.0,
        "ski": 2.0, "natur": 2.0, "berge": 2.0, "wald": 2.0,
        "bayerisch": 2.5, "bayerischer wald": 3.0, "zwiesel": 2.5,
        "regen": 2.0, "bodema": 2.0, "großer arber": 2.5,
        "nationalpark": 2.5,
    },
    "operations_assistant": {
        "workflow": 3.0, "prozess": 3.0, "prozessoptimierung": 3.5,
        "optimierung": 2.5, "effizienz": 2.0, "effizienzsteigerung": 2.5,
        "produktivität": 2.5, "automation": 3.0, "automatisierung": 3.0,
        "automatisieren": 3.0, "robotic process automation": 2.5, "rpa": 2.0,
        "workflow-engine": 2.5, "orchestration": 2.5,
        "prozessmodellierung": 3.0, "bpmn": 2.5, "bottleneck": 2.5,
        "engpass": 2.5, "schwachstelle": 2.0, "lean": 2.0, "six sigma": 2.0,
        "continuous improvement": 2.5, "kvp": 2.5, "ist-soll": 3.5,
        "soll-ist": 3.5, "gap-analyse": 3.0, "status-quo": 2.5,
        "as-is": 2.5, "to-be": 2.5, "zielbild": 2.5, "housekeeping": 3.5,
        "reinigung": 2.5, "zimmerreinigung": 3.0, "putzplan": 2.5,
        "reinigungsplan": 2.5, "reinigungskraft": 2.5, "putzkraft": 2.5,
        "zimmerstatus": 2.5, "belegt": 2.0, "frei": 2.0, "check-out": 2.5,
        "check-in": 2.5, "abreise": 2.0, "anreise": 2.0, "umsatz": 2.0,
        "wäsche": 2.5, "bettwäsche": 2.5, "handtücher": 2.5,
        "minibar": 2.0, "kosmetik": 2.0, "reinigungsmittel": 2.5,
        "desinfektion": 2.5, "hygiene": 2.5, "personal": 2.0,
        "mitarbeiter": 2.0, "team": 1.5, "personalplanung": 2.5,
        "dienstplan": 2.5, "schichtplan": 2.5, "schicht": 2.0,
        "frühdienst": 2.5, "spätdienst": 2.5, "nachtdienst": 2.5,
        "personalbedarf": 2.5, "fehlzeit": 2.0, "krankheit": 2.0,
        "urlaub": 2.0, "urlaubsplanung": 2.5, "zeiterfassung": 3.0,
        "stempeluhr": 2.5, "arbeitszeit": 2.5, "überstunden": 2.5,
        "gleitzeit": 2.0, "lohn": 2.0, "gehalt": 2.0, "lohnabrechnung": 2.5,
        "minijob": 2.5, "450-euro-job": 2.5, "aushilfe": 2.0,
        "praktikant": 2.0, "azubi": 2.0, "auszubildender": 2.5,
        "chef": 1.5, "geschäftsführer": 2.0, "inhaber": 2.0,
        "inventory": 2.5, "lager": 2.0, "bestand": 2.0, "warenbestand": 2.5,
        "stammdaten": 2.5, "artikelstamm": 2.5, "warenwirtschaft": 2.5,
        "wawi": 2.5, "bestellsystem": 2.5, "bestellung": 2.0,
        "einkauf": 2.0, "einkaufsliste": 2.5, "lieferant": 2.5,
        "lieferung": 2.0, "wareneingang": 2.5, "inventur": 2.5,
        "mindestbestand": 2.5, "meldebestand": 2.5, "verderb": 2.5,
        "haltbarkeit": 2.5, "mindesthaltbarkeitsdatum": 2.5,
        "lebensmittel": 2.0, "getränke": 2.0, "wein": 2.0, "bier": 2.0,
        "spirituosen": 2.0, "orderbird": 3.5, "kasse": 2.0,
        "kassensystem": 2.5, "pos": 2.0, "point of sale": 2.0,
        "speisekarte": 2.5, "menü": 2.0, "gericht": 2.0,
        "getränkekarte": 2.5, "tagesgericht": 2.5, "tageskarte": 2.5,
        "saisonkarte": 2.5, "angebot": 2.0, "mittagessen": 2.0,
        "abendessen": 2.0, "frühstück": 2.0, "brunch": 2.0, "buffet": 2.0,
        "à la carte": 2.0, "reservierung": 2.0, "tischreservierung": 2.5,
        "gastraum": 2.0, "sitzplatz": 2.0, "kapazität": 2.0,
        "auslastung": 2.0, "umsatz pro gast": 2.5, "deckungsbeitrag": 2.5,
        "kalkulation": 2.5, "rezeptur": 2.5, "zutaten": 2.0,
        "portion": 2.0, "portionierung": 2.5, "allergene": 2.5,
        "allergenkennzeichnung": 3.0, "zusatzstoffe": 2.5,
        "nahrungsmittel": 2.0, "halal": 2.0, "koscher": 2.0,
        "vegetarisch": 2.0, "vegan": 2.0, "glutenfrei": 2.0,
        "laktosefrei": 2.0, "deskline": 3.0, "prisma": 2.5,
        "channel-manager": 2.5, "pms": 2.5,
        "property management system": 2.5, "hotelsoftware": 3.0,
        "buchungssystem": 3.0, "reservierungssystem": 3.0,
        "gästemanagement": 2.5, "crm": 2.0,
        "customer relationship management": 2.0, "gästedatenbank": 2.5,
        "mailchimp": 2.0, "brevo": 2.0, "sendinblue": 2.0, "klaviyo": 2.0,
        "hubspot": 2.0, "zapier": 2.5, "make": 2.0, "n8n": 2.0,
        "api": 1.5, "schnittstelle": 2.0, "integration": 2.0,
        "controlling": 2.5, "kosten": 2.0, "kostenstelle": 2.5,
        "kostenrechnung": 2.5, "ergebnis": 2.0, "gewinn": 2.0,
        "umsatz": 2.0, "umsatzsteuer": 2.5, "kassenbuch": 2.5,
        "tagesabschluss": 2.5, "z-reports": 2.5, "bericht": 2.0,
        "report": 2.0, "dashboard": 2.0, "kennzahl": 2.0,
        "kennzahlen": 2.0, "kpi": 2.0, "benchmark": 2.0, "vergleich": 2.0,
        "budget": 2.0, "prognose": 2.0, "forecast": 2.0,
        "saisonalität": 2.5, "saison": 2.0, "hauptsaison": 2.5,
        "nebensaison": 2.5, "zwischensaison": 2.5,
    },
    "security_assistant": {
        "security": 3.0, "sicherheit": 3.0, "cybersecurity": 3.0,
        "cyber-sicherheit": 3.0, "it-sicherheit": 3.0,
        "informationssicherheit": 3.0, "datensicherheit": 3.0,
        "schutz": 2.0, "sicherheitsmaßnahme": 2.5,
        "sicherheitsrichtlinie": 2.5, "security policy": 2.5,
        "risikoanalyse": 2.5, "risikomanagement": 2.5, "bedrohung": 2.5,
        "threat": 2.5, "threat model": 2.5, "angriff": 2.5, "attack": 2.5,
        "incident": 2.5, "vorfall": 2.5, "security incident": 3.0,
        "notfall": 2.0, "notfallplan": 2.5, "business continuity": 2.5,
        "disaster recovery": 2.5, "backup": 2.5, "restore": 2.5,
        "owasp": 4.0, "owasp top 10": 4.5, "top 10": 3.0,
        "web security": 3.0, "application security": 3.0, "appsec": 3.0,
        "xss": 3.5, "cross-site scripting": 3.5, "cross site scripting": 3.5,
        "reflected xss": 3.5, "stored xss": 3.5, "dom xss": 3.5,
        "sql injection": 4.0, "sqli": 4.0, "injection": 3.0,
        "command injection": 3.5, "nosql injection": 3.5,
        "ldap injection": 3.5, "xpath injection": 3.5, "xxe": 3.5,
        "xml external entity": 3.5, "ssrf": 3.5,
        "server-side request forgery": 3.5, "csrf": 3.5,
        "cross-site request forgery": 3.5, "clickjacking": 3.0,
        "ui redressing": 3.0, "open redirect": 3.0,
        "directory traversal": 3.0, "path traversal": 3.0, "lfi": 3.0,
        "local file inclusion": 3.0, "rfi": 3.0,
        "remote file inclusion": 3.0, "broken access control": 3.5,
        "access control": 3.0, "authorization": 2.5, "authentication": 3.0,
        "auth": 2.5, "rbac": 3.0, "role-based access control": 3.0,
        "abac": 3.0, "permission": 2.5, "berechtigung": 2.5,
        "privilege escalation": 3.5, "horizontal escalation": 3.5,
        "vertical escalation": 3.5, "idor": 3.5,
        "insecure direct object reference": 3.5,
        "sensitive data exposure": 3.5, "data exposure": 3.0,
        "information disclosure": 3.0, "cryptographic failure": 3.5,
        "crypto": 2.5, "insecure design": 3.0,
        "security misconfiguration": 3.5, "misconfiguration": 3.0,
        "default credentials": 3.5, "default password": 3.5,
        "vulnerable component": 3.0, "dependency": 2.5, "third party": 2.5,
        "identification": 2.5, "auth failure": 3.0,
        "credential stuffing": 3.5, "brute force": 3.5, "brute-force": 3.5,
        "password spraying": 3.5, "session fixation": 3.5,
        "session hijacking": 3.5, "data integrity": 2.5,
        "logging failure": 2.5, "insufficient logging": 2.5,
        "monitoring": 2.0, "siem": 2.5, "security information": 2.5,
        "event management": 2.5, "ids": 2.5, "intrusion detection": 2.5,
        "ips": 2.5, "intrusion prevention": 2.5, "waf": 2.5,
        "web application firewall": 2.5, "csp": 3.0,
        "content security policy": 3.0, "sri": 2.5,
        "subresource integrity": 2.5, "hsts": 3.0,
        "strict transport security": 3.0, "hpkp": 2.5, "expect-ct": 2.5,
        "permissions policy": 2.5, "feature policy": 2.5,
        "referrer policy": 2.5, "x-content-type-options": 2.5,
        "x-frame-options": 2.5, "x-xss-protection": 2.5,
        "secure cookie": 2.5, "httponly": 2.5, "samesite": 2.5,
        "cookie flags": 2.5, "secret": 3.0, "secrets": 3.0,
        "api key": 3.5, "api-key": 3.5, "apikey": 3.5, "api_secret": 3.5,
        "token": 3.0, "access token": 3.5, "refresh token": 3.5,
        "jwt": 3.0, "json web token": 3.0, "passwort": 2.0,
        "password": 2.0, "passphrase": 2.5, "private key": 3.5,
        "ssh key": 3.5, "ssh-key": 3.5, "certificate": 2.5, "cert": 2.0,
        "tls cert": 2.5, "client secret": 3.5, "consumer secret": 3.5,
        "oauth": 2.5, "oauth2": 2.5, "mfa": 2.5, "2fa": 2.5,
        "two factor": 2.5, "zwei faktor": 2.5, "otp": 2.5,
        "one time password": 2.5, "leak": 3.0, "leaked": 3.0, "exposed": 3.0,
        "committed": 2.5, "git history": 2.5, ".env": 2.5,
        "environment variable": 2.5, "härtung": 3.0, "hardening": 3.5,
        "bastion": 2.5, "dmz": 2.5, "zero trust": 2.5, "zero-trust": 2.5,
        "segmentation": 2.5, "network segmentation": 2.5, "vlan": 2.0,
        "vpn": 2.0, "wireguard": 2.5, "openvpn": 2.5,
        "infrastructure": 2.5, "infrastruktur": 2.5, "cloud": 2.0,
        "cloud security": 3.0, "aws": 2.0, "azure": 2.0, "gcp": 2.0,
        "vercel": 1.5, "netlify": 1.5, "docker": 2.0, "container": 2.0,
        "container security": 3.0, "kubernetes": 2.0, "k8s": 2.0,
        "pod security": 3.0, "helm": 1.5, "terraform": 2.0, "iac": 2.0,
        "infrastructure as code": 2.0, "cfn": 2.0, "cloudformation": 2.0,
        "serverless": 2.0, "lambda": 2.0, "function": 1.5, "edge": 1.5,
        "cdn": 2.0, "cloudflare": 2.0, "akamai": 2.0, "fastly": 2.0,
        "rate limit": 3.0, "rate-limiting": 3.0, "throttling": 2.5,
        "ddos": 3.0, "denial of service": 3.0, "bot": 2.5,
        "bot detection": 2.5, "captcha": 2.5, "recaptcha": 2.5,
        "turnstile": 2.5, "hCaptcha": 2.5, "cve": 3.5, "cves": 3.5,
        "vulnerability": 3.0, "vulnerabilities": 3.0, "schwachstelle": 3.0,
        "schwachstellen": 3.0, "exploit": 3.5, "exploitation": 3.5,
        "poc": 2.5, "proof of concept": 2.5, "zero day": 3.5,
        "zero-day": 3.5, "0day": 3.5, "cvss": 3.0, "severity": 2.5,
        "critical": 2.5, "high": 2.0, "medium": 1.5, "low": 1.5,
        "patch": 2.5, "update": 2.0, "upgrade": 2.0, "fix": 2.0,
        "remediation": 2.5, "mitigation": 2.5, "workaround": 2.0,
        "compensating control": 2.5, "scan": 2.0, "scanner": 2.5,
        "security scan": 3.0, "vulnerability scan": 3.0, "penetration": 3.0,
        "pentest": 3.0, "penetration test": 3.0, "red team": 3.0,
        "blue team": 3.0, "purple team": 3.0, "bug bounty": 2.5,
        "ethical hacking": 2.5, "ctf": 2.0, "capture the flag": 2.0,
        "pci-dss": 3.5, "pci": 3.0, "payment card industry": 3.0,
        "gdpr": 2.5, "dsvgo": 2.5, "iso 27001": 3.0, "iso27001": 3.0,
        "isms": 2.5, "information security management": 2.5, "soc 2": 2.5,
        "soc2": 2.5, "hipaa": 2.0, "ferpa": 2.0, "nerc cip": 2.0,
        "nist": 2.5, "nist csf": 2.5, "cyber essentials": 2.5, "bsi": 2.5,
        "bundesamt": 2.5, "it-grundschutz": 2.5, "bsi grundschutz": 2.5,
        "verschlüsselung": 2.5, "encryption": 2.5, "verschlüsseln": 2.5,
        "verschlüsselt": 2.5, "unverschlüsselt": 3.0, "plaintext": 3.0,
        "klartext": 3.0, "hash": 2.5, "hashing": 2.5, "salting": 2.5,
        "peppering": 2.5, "kdf": 2.5, "key derivation": 2.5, "argon2": 2.5,
        "bcrypt": 2.5, "scrypt": 2.5, "pbkdf2": 2.5, "aes": 2.5,
        "rsa": 2.5, "ecc": 2.5, "ecdsa": 2.5, "ed25519": 2.5, "tls": 2.5,
        "ssl": 2.0, "mtls": 2.5, "mutual tls": 2.5, "starttls": 2.5,
        "cipher": 2.5, "cipher suite": 2.5,
        "perfect forward secrecy": 2.5, "pfs": 2.5, "forward secrecy": 2.5,
        "quantum": 2.0, "post-quantum": 2.5, "pq": 2.0,
    },
}

# Agents that should never be auto-selected (built-in, non-domain)
_ROUTER_BLACKLIST: frozenset[str] = frozenset({
    "simple",
    "orchestrator",
    "native_react",
    "native_openhands",
    "react",
    "openhands",
    "rlm",
    "claude_code",
    "operative",
    "monitor",
    "monitor_operative",
    "deep_research",
    "morning_digest",
    "proactive_agent",
})

_DEFAULT_FALLBACK: str = "orchestrator"
_DEFAULT_THRESHOLD: float = 1.5
_DEFAULT_MIN_SCORE: float = 0.5


def _normalise(text: str) -> str:
    """Lower-case and de-umlaut for German text."""
    text = text.lower()
    text = text.replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")
    return text


def _tokenize(text: str) -> list[str]:
    """Strip punctuation, split on whitespace/hyphens."""
    return re.findall(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", text)


@dataclass(frozen=True, slots=True)
class RoutingResult:
    """Outcome of a routing decision."""

    agent_id: str
    confidence: float  # 0.0 - 1.0
    method: str  # "keyword" | "llm" | "fallback"
    scores: dict[str, float] | None = None  # per-agent raw scores


class AgentRouter:
    """Routes user queries to the most appropriate domain agent.

    Usage::

        router = AgentRouter()
        result = router.route("Prüfe die Zimmerpreise")
        assert result.agent_id == "bavaria_booking"
    """

    def __init__(
        self,
        *,
        keywords: dict[str, dict[str, float]] | None = None,
        blacklist: set[str] | None = None,
        fallback_agent: str = _DEFAULT_FALLBACK,
        threshold: float = _DEFAULT_THRESHOLD,
        min_score: float = _DEFAULT_MIN_SCORE,
        llm_router_fn: Callable[[str], str] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        keywords:
            Override the built-in keyword registry.
        blacklist:
            Agent IDs excluded from routing.
        fallback_agent:
            Agent used when no domain agent scores well.
        threshold:
            Score gap required between winner and runner-up for a confident
            keyword decision.  If the gap is smaller, the router falls back
            to ``llm_router_fn`` (if provided) or ``fallback_agent``.
        min_score:
            Minimum absolute score the winner must reach; otherwise fallback.
        llm_router_fn:
            Optional ``query_text -> agent_id`` callable used when keyword
            scoring is ambiguous.
        """
        self._keywords = keywords if keywords is not None else _KEYWORDS
        # Copy the blacklist so runtime mutations are isolated
        self._blacklist: set[str] = set(blacklist if blacklist is not None else _ROUTER_BLACKLIST)
        self._fallback = fallback_agent
        self._threshold = threshold
        self._min_score = min_score
        self._llm_router = llm_router_fn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, query_text: str) -> RoutingResult:
        """Analyse *query_text* and return the best agent."""
        norm_query = _normalise(query_text)
        tokens = _tokenize(norm_query)
        scores: dict[str, float] = {}

        for agent_id, kws in self._keywords.items():
            if agent_id in self._blacklist:
                continue
            score = 0.0
            matched_multiword: set[str] = set()
            matched_substring: set[str] = set()

            for token in tokens:
                # 1) Exact token match
                if token in kws:
                    score += kws[token]
                    continue

                # 2) Substring match — German compound words
                #    e.g. token "zimmerpreise" contains keyword "zimmer"
                for kw, weight in kws.items():
                    if (token.startswith(kw) or token.endswith(kw)) and len(kw) >= 3:
                        if kw not in matched_substring:
                            score += weight * 0.5  # half weight for substring
                            matched_substring.add(kw)

            # 3) Multi-word keyword match (count once per query)
            for kw, weight in kws.items():
                if " " in kw and kw in norm_query:
                    if kw not in matched_multiword:
                        score += weight
                        matched_multiword.add(kw)

            scores[agent_id] = score

        if not scores:
            logger.debug("routing: no scores produced, falling back to %s", self._fallback)
            return RoutingResult(
                agent_id=self._fallback,
                confidence=0.0,
                method="fallback",
            )

        sorted_agents = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        winner_id, winner_score = sorted_agents[0]
        runner_up_score = sorted_agents[1][1] if len(sorted_agents) > 1 else 0.0

        # Determine confidence metrics
        gap = winner_score - runner_up_score
        confidence = self._calculate_confidence(winner_score, gap)

        logger.debug(
            "routing: winner=%s score=%.2f runner_up=%.2f gap=%.2f confidence=%.2f",
            winner_id,
            winner_score,
            runner_up_score,
            gap,
            confidence,
        )

        # Decision gate
        if winner_score >= self._min_score and gap >= self._threshold:
            return RoutingResult(
                agent_id=winner_id,
                confidence=confidence,
                method="keyword",
                scores=scores,
            )

        # Ambiguous or too low — try LLM if available
        if self._llm_router is not None:
            llm_choice = self._llm_router(query_text)
            if llm_choice and llm_choice not in self._blacklist:
                return RoutingResult(
                    agent_id=llm_choice,
                    confidence=0.7,  # moderate confidence in LLM
                    method="llm",
                    scores=scores,
                )

        # Fallback
        return RoutingResult(
            agent_id=self._fallback,
            confidence=0.0,
            method="fallback",
            scores=scores,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_confidence(score: float, gap: float) -> float:
        """Map raw score + gap to a 0.0-1.0 confidence."""
        # Score component: saturates around 10
        score_part = min(score / 10.0, 1.0)
        # Gap component: saturates around 5
        gap_part = min(gap / 5.0, 1.0)
        # Weighted combination
        return round(score_part * 0.4 + gap_part * 0.6, 3)

    def register_keywords(self, agent_id: str, keywords: dict[str, float]) -> None:
        """Add or overwrite keywords for an agent at runtime."""
        self._keywords[agent_id] = keywords

    def blacklist_agent(self, agent_id: str) -> None:
        """Exclude an agent from routing."""
        self._blacklist.add(agent_id)

    def whitelist_agent(self, agent_id: str) -> None:
        """Re-allow a previously blacklisted agent."""
        self._blacklist.discard(agent_id)
