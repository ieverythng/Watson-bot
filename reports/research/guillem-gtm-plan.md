# GTM Plan: Lead Generation for Guillem (Real Estate — Barcelona/Badalona)

## Overview

A deterministic lead generation system that helps Guillem find property owners and contact them for listings in the Barcelona metro area (Badalona, Barcelona, etc.).

## The Problem

Guillem needs to prospect property owners who aren't actively listing. Current workflow:
1. He has a CRM (Bluplat) that tracks properties and shows which agent last contacted
2. He uses another platform to look up who owns a property by address
3. If no direct owner found, he searches for family members at that address
4. From there, he tries to find phone numbers

This is manual, slow, and fragmented. We want to systematize it.

## Data Sources (Spain-Specific)

### Primary Platforms
| Platform | Purpose | Notes |
|----------|---------|-------|
| **Bluplat** | CRM — tracks properties, last agent who contacted | No public API confirmed; likely CSV import/export or private API |
| **"Englobal"** (TBD exact name) | Property ownership lookup by address | Juan mentioned this; need to confirm exact platform |
| **Catastro** | Official cadastre — parcel data, cadastral reference | Public API available; good for address normalization |
| **Registro de la Propiedad** | Legal ownership verification (nota simple) | Semi-manual, fee-based, authoritative |

### Secondary Enrichment
| Source | What It Gives |
|--------|--------------|
| **eInforma / Axesor** | Company ownership data, directors, legal addresses |
| **Páginas Amarillas / Infobel** | Business directories, company phone numbers |
| **idealista / fotocasa / habitaclia** | Portal listings — stale listings, price drops, duplicates |
| **CASAFARI** | Listing intelligence across portals (dedup, history) |

### Phone Lookup (The Hard Part)
Spain has weak public reverse-phone lookup for private individuals. Options:
- **Truecaller / Tellows** — identify numbers, not find them
- **Company registries** — good for company-owned properties
- **Commercial data brokers** — legally gray area, compliance risk

## Proposed Architecture

```
┌─────────────────────┐
│   INPUT LAYER        │
│                     │
│  - Manual address    │
│  - Bluplat export    │
│  - Portal scraping   │
│  - Stale listings    │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  ADDRESS NORMALIZER  │
│                     │
│  - Catastro API     │
│  - Standardize addr │
│  - Dedupe properties│
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ OWNERSHIP RESOLVER   │
│                     │
│  - Englobal lookup  │
│  - eInforma (co.)   │
│  - Nota simple queue│
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  CONTACT ENRICHER    │
│                     │
│  - Company phone    │
│  - Registry data    │
│  - CRM history      │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   LEAD SCORER        │
│                     │
│  - Listing age      │
│  - Price drops      │
│  - Duplicate count  │
│  - Owner type       │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  OUTPUT / BLUPLAT    │
│                     │
│  - CSV import       │
│  - API (if avail.)  │
│  - Dashboard        │
└─────────────────────┘
```

## MVP Scope (Phase 1)

### What to Build First
1. **Stale listing monitor** — scrape idealista/fotocasa/habitaclia for listings in Badalona/Barcelona that are 60+ days old, have price drops, or were withdrawn
2. **Address normalizer** — use Catastro API to standardize addresses
3. **Ownership lookup workflow** — integrate with Englobal (or whatever platform Guillem uses) to resolve owner by address
4. **Company enrichment** — if owner is a company, pull data from eInforma/Axesor for contact info
5. **CSV export → Bluplat import** — generate leads file Guillem can import into his CRM

### What to Defer
- Personal mobile number lookup (compliance risk + technically hard in Spain)
- Full Bluplat API integration (until we confirm it exists)
- Automated nota simple requests (manual for now)

## Compliance Considerations (Critical for Spain)

- **GDPR / LOPDGDD** — all personal data processing must have legal basis
- **Lista Robinson** — check before direct marketing
- **Source provenance** — document where each piece of data comes from
- **Legitimate interest assessment** — for B2B/company outreach
- **No gray-market phone data** — too risky legally

## Tech Stack Proposal

| Component | Technology |
|-----------|-----------|
| Backend | Python (FastAPI) |
| Database | PostgreSQL + PostGIS (for geospatial) |
| Scraping | Playwright / BeautifulSoup |
| Catastro API | Official REST API |
| Frontend | Simple dashboard (Streamlit or React) |
| Bluplat sync | CSV import initially, API later |

## Next Steps

1. ✅ Research complete — this document
2. ⬜ Confirm exact name of the ownership lookup platform ("Englobal"?)
3. ⬜ Ask Bluplat about API / import capabilities
4. ⬜ Create GitHub repo under ieverythng org
5. ⬜ Set up MVP project structure
6. ⬜ Build stale listing monitor (idealista/fotocasa)
7. ⬜ Integrate Catastro API for address normalization
8. ⬜ Build ownership resolver module
9. ⬜ Company enrichment via eInforma
10. ⬜ CSV export → Bluplat import workflow

## Open Questions

- What is the exact name of the second platform Guillem uses for ownership lookup?
- Does Bluplat have a public API or webhooks?
- What's Guillem's target area radius (Badalona only, or all Barcelona metro)?
- How many leads per week/month does he need?
- Budget for data services (eInforma, nota simple costs, etc.)?
