In the middle of November the internet seemed to fall over every other day. Microsoft 365 went down for a day, US airspace closed for hours, AWS stumbled, and Chase and United had bad afternoons. People suspected an attack. Every company involved said it wasn't one, and the causes that have been published point the other way: a faulty update, new hardware, a software bug.

That came straight after what security people call "Black October": a month of big flaws in PHP, Linux, GitLab and Oracle, several found with the help of AI, a poisoned AI library on PyPI, and a record Microsoft update. So the question is simple. Is there more danger out there, or just more to fix?

{{ signal value="4×" label="as many software security flaws were published in October 2026 as in October 2025: 17,050 against 4,274. The number added to the US list of flaws attackers are known to use went from 31 to 36." }}

## Flaws found shot up, flaws used didn't

Every publicly known security flaw gets a CVE number. In 2025, about 4,000 were published a month. Since spring 2026 that number has climbed every month, to 17,050 in October. In ten months of 2026 there have been more than 89,000, over twice as many as in the whole of 2025.

CISA, the US cyber agency, keeps a separate list of flaws with solid evidence that attackers are using them, the Known Exploited Vulnerabilities catalogue. That list grew too, but slowly: 282 additions from January to October, against 214 in the same months of 2025.

{{ chart src="charts/found.js" data="data/found_vs_exploited.csv" title="Published flaws quadrupled, exploited flaws rose far less" subtitle="Monthly count, as an index where each series' 2025 monthly average = 100. January 2024 to October 2026" source="CVE List; CISA Known Exploited Vulnerabilities catalogue" note="Hover for the counts behind the index." }}

Put the two together and the odds change. In 2025, about 5 in every 1,000 new flaws were added to CISA's list. In 2026 so far it is 3 in 1,000. Most of the new flaws are real, but most will never be used against anyone.

## A lot of the new flaws were found by AI

CVE records can credit who found the flaw. Since the summer, more of them name an AI system or an AI security team: Anthropic's Claude, OpenAI, Google's Big Sleep, AISLE, XBOW and others. In October 2025, 16 flaws had such a credit. In October 2026 it was 277.

{{ chart src="charts/ai.js" data="data/monthly.csv" title="Flaws credited to AI went from a handful to hundreds a month" subtitle="Published CVEs whose credits name an AI system or AI research team, per month, January 2025 to October 2026" source="CVE List, own text match on the credits field" note="A floor, not a total: most CVE records don't say how a flaw was found." }}

That is still under 2% of all flaws, so AI credits alone don't explain a fourfold rise. The rise comes from almost every direction at once. VulnCheck, which assigns numbers for many smaller projects, went from 158 in October 2025 to 2,473. GitHub's advisories went from 272 to 1,536, Oracle from 78 to 1,078. Many of these teams now run AI tools over code without always saying so in the credits.

## Microsoft: eight times the fixes, the same number of attacks

Microsoft's October update was reported as fixing "over 1,400" flaws, against about 170 a year earlier. The CVE List agrees: Microsoft published 1,475 CVEs in October 2026 and 180 in October 2025.

{{ chart src="charts/microsoft.js" data="data/monthly.csv" title="Microsoft now fixes over a thousand flaws a month" subtitle="CVEs published by Microsoft per month, January 2024 to October 2026" source="CVE List (CVEs assigned by Microsoft); Microsoft Security Update Guide" note="Hover a bar for how many were already being exploited when the fix came out." }}

Microsoft also marks which flaws were already under attack when it shipped the fix. From January to October 2026 that was 20 flaws. In the same months of 2025 it was 22. So the size of the update grew eightfold while the number of attacks it was racing against stayed flat.

## What did change: the time to patch

The attacks that do happen come fast. Of the flaws CISA added in 2026, 60% were added within 30 days of the flaw being published, the highest share in four years. 132 were added within a week, against 97 in the whole of 2025.

{{ chart src="charts/speed.js" data="data/exploit_speed.csv" title="Six in ten exploited flaws are now used within a month" subtitle="Share of flaws added to CISA's catalogue within 30 days of their CVE being published, by year added" source="CVE List; CISA Known Exploited Vulnerabilities catalogue" note="* 2026 up to 20 November. 2021 and 2022 left out: CISA was then adding years of older flaws in bulk." }}

That is the squeeze IT teams are in. There are four times as many fixes to install, and the few that matter have to go in within days. A company can't test thousands of changes a month the way it tested hundreds. Installing them fast means more changes that go wrong. Installing them slowly means a window for the few flaws that attackers jump on. Microsoft's own outage on 12 November was traced to a defect in an update to its network gateways, made back in July.

## In the Netherlands

The NCSC, the Dutch national cyber security centre, groups flaws per product into advisories. It published 65 in October 2026, against 43 a year earlier. That is a rise of half, not four times, because one advisory can cover dozens of flaws. Its PHP advisory came out on 21 October, the day of the PHP2Shell fix. Dutch, Belgian and Finnish government sites were reportedly taken offline as a precaution while they patched.

## What the data can't tell you

| Limit | What it means here |
| --- | --- |
| CISA's list is a floor | It holds flaws with solid public evidence of attacks and a fix. Many attacks are never reported, and the list is US-focused. |
| Recent flaws have had less time | A flaw from October 2026 can still be exploited next year. The gap between "found" and "used" will narrow somewhat as 2026 flaws age. |
| AI credits are self-reported | Most records don't say how a flaw was found. The count is a lower bound and depends on the words people use. |
| The outages aren't in the data | No public dataset links an outage to an update. The link between faster patching and the November outages is what the companies said, not something these numbers show. |
| A CVE is not a fix | One fix can close several CVEs, and one CVE can need fixes in many products. |

## How I did it

I counted every published record in the CVE List snapshot of 23 November 2026 by publish month and by the organisation that assigned it, and took its highest CVSS score. For "found by AI" I matched the credits field against the names of AI systems and AI security teams, and checked a sample by hand. I counted additions to CISA's catalogue by the date added and matched them to the CVE publish date for the 30-day measure. Microsoft's counts are CVEs that Microsoft itself assigned, so Chromium and Linux flaws it also ships are left out; its "exploited" flag comes from its monthly update guides. The NCSC-NL counts come from its published CSAF advisories. Microsoft, NCSC-NL and CISA's website don't answer every server, so the downloads run in GitHub Actions.
