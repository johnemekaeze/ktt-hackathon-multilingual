# village_agent.md — Product & Business Adaptation

## T2.2 · Multilingual Grant & Tender Matcher
## Offline Distribution Design for Illiterate Cooperative Leaders

---

## 1. Target User

| Attribute | Detail |
|-----------|--------|
| **Who** | Cooperative leader (president/secretary), age 35–65 |
| **Literacy** | Minimal to none in French or English |
| **Device** | Basic feature phone (voice/SMS capable) |
| **Connectivity** | 2G intermittent, 30–60% network uptime in target zones |
| **Location** | Rural Rwanda, DRC, Senegal — district cooperative hub |
| **Languages** | Kinyarwanda, Lingala, Wolof (primary), French (partial) |

---

## 2. Three Distribution Options Considered

### Option A — Voice Call Centre → IVR → Human Agent

| Item | Detail |
|------|--------|
| **Flow** | Weekly batch → call centre agent calls each cooperative → reads top 3 grants aloud → answers 2 Q&A |
| **CAC** | ~RWF 4,500 / cooperative / activation |
| **Pros** | High trust; handles questions; works on any phone |
| **Cons** | Expensive at scale; requires staffing; latency |

**Weekly cost at 500 cooperatives:**
- 500 × 4 min avg call × RWF 18/min airtime = RWF 36,000
- 3 agents × 8 h/day × 1 day/week × RWF 3,500/h = RWF 84,000
- **Total: ~RWF 120,000/week → RWF 240/cooperative/week**
- One-time activation (training, consent form): RWF 4,000/coop → **CAC ≈ RWF 4,500**

---

### Option B — WhatsApp Audio Broadcast ✅ **RECOMMENDED**

| Item | Detail |
|------|--------|
| **Flow** | Matcher runs Sunday night → summaries translated to Kinyarwanda/Lingala/Wolof voice clips (TTS, 60–90 sec) → broadcast to WhatsApp group of cooperative leaders every Monday 7 AM |
| **CAC** | ~RWF 1,200 / cooperative / activation |
| **Pros** | Low cost; async (leader listens when free); shareable; WhatsApp penetration growing rapidly |
| **Cons** | Requires smartphone (can use shared community phone); needs WiFi/data |

**Weekly cost at 500 cooperatives:**
- Meta WhatsApp Business API: USD 0.005/message × 500 = USD 2.50 ≈ RWF 3,500/week
- TTS generation (Google Cloud / Coqui-TTS open source): ~RWF 500/week (cloud) or free (local)
- Part-time coordinator (4 h/week): RWF 5,000
- **Total: ~RWF 9,000/week → RWF 18/cooperative/week**
- One-time activation (number collection, consent, WhatsApp group setup): RWF 800/coop → **CAC ≈ RWF 1,200**

---

### Option C — Printed Bulletin Board at District Cooperative

| Item | Detail |
|------|--------|
| **Flow** | Matcher runs → human-readable French/local language 1-page brief printed → posted at district cooperative board every Monday |
| **CAC** | ~RWF 600 / cooperative / activation |
| **Pros** | No connectivity required; zero digital literacy barrier; durable |
| **Cons** | Slow (leaders must travel to board); stale between weeks; no personalisation |

**Weekly cost at 500 cooperatives (assuming 50 district boards):**
- Printing 50 × 2 pages A4 colour: 50 × RWF 200 = RWF 10,000
- Courier/moto delivery to 50 districts: RWF 15,000
- **Total: ~RWF 25,000/week → RWF 50/cooperative/week**
- One-time activation: RWF 400/coop (register board, consent) → **CAC ≈ RWF 600**

---

## 3. Recommendation: Option B — WhatsApp Audio Broadcast

### Justification

| Criterion | Voice Centre | WhatsApp Audio | Printed Board |
|-----------|:---:|:---:|:---:|
| Cost/coop/week (RWF) | 240 | **18** | 50 |
| CAC (RWF) | 4,500 | **1,200** | 600 |
| Personalisation | ✅ | ✅ | ❌ |
| No literacy required | ✅ | ✅ | ⚠️ |
| Works offline | ✅ | ⚠️ (needs data once) | ✅ |
| Scale to 5,000 coops | ❌ expensive | ✅ | ⚠️ logistics |
| Speed of update | Same day | **Same day** | 1 week lag |

WhatsApp Audio wins on **cost × personalisation × scalability**. While Printed Board has a lower CAC, it cannot personalise by sector, cannot update in real-time, and requires physical logistics. Voice Centre has highest trust but is 13× more expensive per weekly touch.

At **500 cooperatives** scale:
- WhatsApp: **RWF 9,000/week** total operating cost
- Voice Centre: **RWF 120,000/week**
- Printed: **RWF 25,000/week**

---

## 4. Weekly Cadence

```
Sunday 22:00  →  matcher.py --all --topk 3 runs on server
Sunday 22:05  →  summarizer generates Kinyarwanda/FR audio scripts
Sunday 22:10  →  TTS (Coqui or gTTS) converts scripts to .ogg voice clips
Monday 07:00  →  WhatsApp Business API broadcasts to all 500 groups
Monday 07:05  →  Cooperative leader receives 60-sec voice note
Monday–Friday →  Leader can forward, reply with questions (human agent responds Wed/Fri)
Saturday      →  Coordinator reviews engagement, flags unread messages
```

---

## 5. Sample WhatsApp Audio Script (Kinyarwanda → translated here in EN)

> *"Muraho bavandimwe. Uyu munsi wa Kuwa Kabiri, nibura imfashanyo 3 zihari ku mirimo ya [sector] muri [region]. Uwa mbere ni [Tender Title] — iha amafaranga hafi [budget]. Igihe cyo gutura ari [deadline]. Iyi imfashanyo ihuye na [cooperative name] kubera [reason]. Kugira ngo umenye byinshi, vugana na [agent name] kuri +250 78X XXX XXX."*

**Translation:**
> *"Hello colleagues. This Monday, there are at least 3 funding opportunities for [sector] businesses in [region]. The first is [Tender Title] — offering approximately [budget]. The deadline is [deadline]. This grant matches [cooperative name] because [reason]. To learn more, contact [agent name] at +250 78X XXX XXX."*

---

## 6. Privacy & Consent Plan

| Element | Implementation |
|---------|----------------|
| **Opt-in** | Written/verbal consent form collected by field coordinator at first activation |
| **Data stored** | Name, phone number, sector, cooperative ID only |
| **No data sold** | Explicit clause in consent agreement |
| **Opt-out** | Reply "STOP" or call coordinator — removed within 24 hours |
| **Regulatory** | Complies with Rwanda Data Protection Law (2021) / Senegal Law 2008-12 / DRC Telecoms Regulation |
| **Audio retention** | Voice clips deleted after 14 days |

---

## 7. 90-Day Scale-Up Roadmap

| Week | Milestone |
|------|-----------|
| 1–2 | Pilot with 20 cooperatives in 1 district (Rwanda) |
| 3–4 | Collect feedback, refine audio templates |
| 5–8 | Expand to 100 cooperatives across 3 districts |
| 9–12 | Scale to 500 cooperatives; onboard 2 additional countries (Senegal, DRC) |

---

## 8. Stretch: Code-Switched Query Support

The matcher supports mixed-language queries like:
> *"je cherche un grant pour agritech, 50k or less"*

Implementation: the `ranker.py` `rank()` function builds the query string from `needs_text`, which may be French, English, or mixed. The multilingual MiniLM embedding model handles code-switching natively — no pre-processing required.

---

*Artifact prepared for T2.2 · AIMS KTT Hackathon · April 2026*
