Being the only country in the world to vote no takes some nerve. At the UN General Assembly, a lone no is on the record forever, next to 180 yes votes. So when a country does it, and does it again every year, it is telling you what it cares about more than its reputation.

Everyone knows the two countries that do this most: the United States and Israel. I wanted to know who else stands alone, and on what. So I went through every recorded General Assembly vote since 1946, all 5,730 of them, and pulled out the ones with exactly one no.

{{ signal value="42 years" label="Türkiye has voted no on every Law of the Sea resolution since 1984. For the last 35 years it has almost always been the only no." }}

## Who stands alone

{{ chart src="charts/lone.js" data="data/lone_no.csv" title="After the US and Israel, the loneliest no votes come from North Korea, India, Türkiye and France" subtitle="Number of recorded General Assembly votes on which the country was the only one to vote no, 1946–2026, log scale" source="UN Dag Hammarskjöld Library, General Assembly voting data; own analysis" note="Hover or tap a bar for the resolution each country most often stood alone against." }}

Only 52 countries have ever been the lone no. For most of them it happened once or twice. For a handful it's a habit, and in most cases it's one resolution, again and again:

| Country | Lone no's | Most often alone against | Times |
| --- | --- | --- | --- |
| North Korea | 37 | The Comprehensive Nuclear-Test-Ban Treaty | 14 (2009–2023) |
| India | 35 | Conventional arms control at the regional and subregional levels | 29 (1996–2025) |
| Türkiye | 34 | Oceans and the Law of the Sea | 32 (1991–2025) |
| France | 27 | The Comorian island of Mayotte | 15 (1976–1992) |
| Russia | 14 | Implementing the Convention on Cluster Munitions | 5 (2019–2024) |
| Iran | 13 | The Hague Code of Conduct against Ballistic Missile Proliferation | 8 (2005–2020) |
| Pakistan | 5 | A treaty banning the production of fissile material for nuclear weapons | 5 (2010–2021) |

Each of these is a red line that rarely makes the news: a treaty a country won't sign, or a territory it won't give up. Three of them have run for decades.

## Three countries, three red lines

{{ chart src="charts/lonely.js" data="data/lonely_votes.csv" title="Türkiye, India and France each voted no on the same resolution year after year, usually alone" subtitle="Every recorded General Assembly vote on three resolutions, 1976–2025. One dot per vote." source="UN Dag Hammarskjöld Library, General Assembly voting data; own analysis" note="Red: the only no. Grey: no, with others. Hollow: abstained or absent." size="wide" }}

**Türkiye and the sea.** Every year the Assembly adopts a long resolution on the oceans that calls on all countries to join the 1982 UN Convention on the Law of the Sea. Türkiye has voted no every time since 1984, 42 votes in a row. Until 1990, the United States voted no as well, because it objected to the convention's rules on deep-seabed mining. Those rules were renegotiated in 1994, the US switched, and Türkiye was left on its own. It was the only no in 32 of the 42 votes.

The reason is the Aegean Sea. The convention lets a country claim 12 nautical miles of territorial waters. If Greece did that around its islands, many of which lie just off the Turkish coast, Türkiye would need Greek permission to reach large parts of the open sea. Turkey's parliament has said it would treat that as a cause for war. So Türkiye has never joined the convention, and every year it says so with one vote.

**India and Pakistan.** The UN hasn't voted on Kashmir in a long time. The Security Council passed its last resolution that names Kashmir in 1957, and its last one on India and Pakistan in December 1971. Two other drafts on Kashmir, in February 1957 and June 1962, were vetoed by the Soviet Union. The General Assembly has never held a recorded vote on a resolution about Kashmir.

But the rivalry still shows up in the votes. Every year, Pakistan puts forward a resolution on conventional arms control "at the regional and subregional levels". It sounds abstract. India, the much larger military power, reads it as aimed at itself, because it asks the countries of a region to keep their armed forces in balance. India abstained in 1994 and 1995. Since 1996 it has voted no 29 times, and each time it was the only country to do so. Pakistan returns the favour on a treaty to ban the production of fissile material for nuclear weapons: it was the lone no five times from 2010 to 2021.

**France and Mayotte.** When the Comoros became independent in 1975, one of its four islands, Mayotte, stayed French, after voting against independence in referendums in 1974 and 1976. The Assembly called that a violation of the Comoros' territorial unity and voted on it almost every year. France was the only no 15 times between 1976 and 1992. Then the votes stopped. The question is still on the Assembly's agenda, but there has been no recorded vote on it since 1994. Mayotte became a French département in 2011.

## The unexpected part

**The loudest disputes go quiet, and the votes move somewhere else.** Kashmir is one of the most dangerous disputes in the world, between two nuclear powers, and the UN has voted on it less than on Mayotte. The fight carried on in arms-control resolutions that few people read. Türkiye and Greece have the same pattern: they have nearly gone to war over the Aegean several times, and at the UN it shows up as one no on a yearly resolution about the oceans.

## What the data can't tell you

- **Who wrote each resolution.** The voting data lists the votes, not the sponsors. Who put forward each text comes from the draft documents and from the news at the time.
- **Why a country voted no.** Countries explain their votes in the meeting records, which aren't in this data. The reasons given here come from the countries' own public positions.
- **Votes on paragraphs.** Countries sometimes vote alone against one paragraph and then for the whole text. The dataset only has the votes on whole resolutions.
- **Titles change.** I matched resolutions by their exact title. "Law of the Sea" became "Oceans and the Law of the Sea" in 1997, so the chart includes both. Other countries' counts may be split across titles in the same way.

## How I did it

The UN's Dag Hammarskjöld Library publishes every country's vote on every recorded General Assembly vote since 1946, and every Security Council resolution with its vote. A lone no is a recorded vote with exactly one no, whatever the number of abstentions. The Security Council resolutions about India and Pakistan are the ones whose description, agenda item or subjects mention Kashmir, Jammu, or India and Pakistan. The vetoes come from the Library's veto list.

The code is in [`analysis/un-votes`](https://github.com/jawdat-rana/unexpected-signals/tree/main/analysis/un-votes). The UN data may be reused for non-commercial purposes with attribution.
