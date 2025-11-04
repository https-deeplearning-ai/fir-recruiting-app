# Company Research Agent - Voice-Over Script

**Duration: ~2 minutes**

---

## Opening (10 seconds)

"This is the Company Research Agent. It finds relevant companies from job descriptions using AI. Let me show you how it works."

---

## Step 1: Input (15 seconds)

"You paste a job description. For example, a Voice AI Engineer role that mentions companies like Deepgram and AssemblyAI.

Click 'Analyze JD.'"

---

## Step 2: Parsing (20 seconds)

"Claude AI extracts key data in 3 seconds:
- Role title: Senior Voice AI Engineer
- Target domain: voice AI
- Mentioned companies: Deepgram, AssemblyAI, ElevenLabs
- Technical skills: Python, PyTorch, speech recognition

This structured data powers the next phase."

---

## Step 3: Discovery (25 seconds)

"Phase 1: Discovery runs in 5 to 10 seconds.

It pulls from two sources:

First, companies mentioned in the JD.

Second, web search using Tavily API. Claude LLM extracts company names from search results.

Total discovered: 46 companies.

You see live updates via real-time streaming."

---

## Step 4: Screening (30 seconds)

"Phase 2: Screening takes 10 to 15 seconds.

GPT-4o-mini scores all 100 companies in batches of 20.

Batch 1 of 5: processing 20 companies.
Batch 2 of 5: processing 20 companies.

Each company gets a relevance score from 1 to 10.

The progress bar updates in real-time as batches complete.

This is the new feature we just added."

---

## Step 5: Deep Research (30 seconds)

"Phase 3: Deep Research runs for 20 to 30 seconds.

Claude Sonnet 4.5 analyzes the top 25 companies in parallel.

For Deepgram:
- Category: Direct Competitor
- Score: 9.5 out of 10
- Reasoning: Leading real-time speech recognition API, direct competitor in voice AI infrastructure
- Source: Web search, result rank 1
- Search query shown for transparency

You see which company is being evaluated live: 'Evaluating Deepgram, 3 of 25.'"

---

## Step 6: Results (20 seconds)

"Companies are grouped by relationship:

Direct Competitors: Deepgram, AssemblyAI, Speechmatics.
Adjacent Companies: ElevenLabs, Otter.ai, Descript.
Same Category: Rev.com, Trint.
Tangential: Grammarly.

22 companies selected with relevance score above 3.

Download as CSV or copy to clipboard.

Every company shows its source query and result rank."

---

## Technical Summary (15 seconds)

"Three AI models work together:

Claude Sonnet 4.5 for parsing and deep research.
GPT-4o-mini for fast batch screening.
Tavily for web search.

Real-time updates via Server-Sent Events.
Total time: 40 to 60 seconds end-to-end."

---

## Business Value (15 seconds)

"For recruiters: identify talent pools and competitor companies automatically.

For hiring managers: understand your competitive landscape and benchmark talent.

No manual research needed."

---

## Closing (10 seconds)

"That's the Company Research Agent. Paste a job description, get relevant companies in under a minute. All powered by AI."

---

## Voice-Over Timing Breakdown

| Section | Duration | Cumulative |
|---------|----------|------------|
| Opening | 10s | 10s |
| Input | 15s | 25s |
| Parsing | 20s | 45s |
| Discovery | 25s | 70s (1:10) |
| Screening | 30s | 100s (1:40) |
| Deep Research | 30s | 130s (2:10) |
| Results | 20s | 150s (2:30) |
| Technical | 15s | 165s (2:45) |
| Business Value | 15s | 180s (3:00) |
| Closing | 10s | 190s (3:10) |

**Total: ~3 minutes 10 seconds**

---

## Shortened Version (90 seconds)

If you need a 90-second version, combine sections:

### Opening (5s)
"This is the Company Research Agent. It finds relevant companies from job descriptions using AI."

### How It Works (30s)
"Paste a job description. Claude AI extracts the role title, target domain, mentioned companies, and skills in 3 seconds. Then it discovers companies from two sources: those mentioned in the JD, and web search results. 46 companies discovered in 10 seconds."

### Processing (30s)
"GPT-4o-mini screens 100 companies in batches. You see live progress: batch 1 of 5, batch 2 of 5. Claude Sonnet analyzes the top 25 in detail, scoring each from 1 to 10. Deepgram scores 9.5 as a direct competitor. Every company shows its source and search query."

### Results (15s)
"Companies grouped by relationship: direct competitors, adjacent companies, same category. 22 companies selected. Download CSV. Total time: 60 seconds."

### Closing (10s)
"No manual research needed. Paste a JD, get competitors in under a minute."

**Total: 90 seconds**
