Most of what the UN General Assembly decides, it decides without a vote. A resolution on disaster risk reduction or on people with albinism is negotiated for weeks, and then the president of the Assembly asks if anyone objects. Nobody does, the gavel comes down, and it passes "without a vote". A recorded vote, where every country's yes or no goes on the record, only happens when someone asks for one. For 35 years, that was about one resolution in four.

Then it changed in a single year. I went through every General Assembly resolution since 1990, about 12,000 of them, to see how big the change was and who was on each side.

{{ signal value="61%" label="of General Assembly resolutions went to a recorded vote in the 2025–26 session, up from about 25% in a normal year. The US voted no 173 times." }}

## One year, twice the votes

{{ chart src="charts/sessions.js" data="data/sessions.csv" title="In 2025–26, most UN resolutions went to a vote for the first time" subtitle="Share of General Assembly resolutions adopted by recorded vote, per regular session (September to September), 1990–91 to 2025–26" source="UN Dag Hammarskjöld Library, General Assembly voting data; own analysis" }}

From 1990 to 2024, the share of resolutions that went to a vote stayed between 18% and 34%. In the session that began in September 2025, it was 192 out of 317 resolutions.

A lot of these used to be routine. In 56 cases, a resolution went to a vote even though every earlier resolution with the same title had passed without one. Together, those titles had been adopted 644 times without a vote. Most of them ended 180 to 1 or 181 to 2:

| Resolution | Earlier, without a vote | 2025–26 vote | Voted no |
| --- | --- | --- | --- |
| Assistance to refugees, returnees and displaced persons in Africa | 33 times | 179 to 1 | United States |
| Protection of global climate for present and future generations | 16 times | 181 to 1 | United States |
| Disaster risk reduction | 9 times | 181 to 1 | United States |
| Sustainable mountain development | 8 times | 178 to 1 | United States |
| Persons with albinism | 5 times | 179 to 3 | Argentina, Israel, United States |
| Addressing the challenges of persons living with a rare disease | 2 times | 179 to 2 | Israel, United States |

New resolutions got the same treatment. In March 2026, the Assembly adopted International Coffee Day by 150 votes to 1. The one no was the United States.

The data doesn't say who asked for each vote. It does show that the US voted no on all 56 of these resolutions, and that it was the only no on 22 of them. All 56 are in [the full list](data/forced_votes.csv).

## Who followed

When a country votes no 173 times, the interesting question is who votes with it. To answer it, I measured agreement: of the recorded votes two countries both took part in, the share where they voted the same way (yes, no or abstain).

{{ chart src="charts/shift.js" data="data/us_agreement_shift.csv" title="Every UN member voted less like the US, and most almost never did" subtitle="Share of recorded General Assembly votes on which each member voted the same way as the US, 2024–25 session against 2025–26 session. Each dot is a country." source="UN Dag Hammarskjöld Library, General Assembly voting data; own analysis" note="Hover or tap a dot for the country." size="wide" }}

All 185 members agreed less with the US in 2025–26 than the year before. For the typical member, agreement fell from 24% to 5%, and 126 countries voted with the US on fewer than one vote in ten. This includes its allies. The Netherlands went from 50% to 14%, and the United Kingdom from 56% to 21%.

Two countries came along: Israel (78%) and Argentina (63%). When the US voted no, Israel joined it 101 times and Argentina 88 times. The next country on the list, Hungary, joined it 30 times. On 39 of the US's no votes, nobody joined it at all.

## The unexpected part

**The countries that always voted with the US didn't follow.** Micronesia, the Marshall Islands and Palau are tied to the US by treaties called Compacts of Free Association. The US pays for much of their government and defends them, and they vote with it more often than almost anyone. From 2014 to 2024, only Israel agreed with the US more often than Micronesia did (88% against 73%). They kept doing that through the first Trump term.

{{ chart src="charts/trend.js" data="data/us_agreement_trend.csv" title="Micronesia voted with the US for years. In 2025–26 it stopped" subtitle="Share of recorded General Assembly votes on which each country voted the same way as the US, per session, 2015–16 to 2025–26" source="UN Dag Hammarskjöld Library, General Assembly voting data; own analysis" }}

Micronesia agreed with the US on 80% of votes in 2023–24. In 2025–26 that fell to 23%, and the Marshall Islands fell to 10%. Argentina did the opposite. Under President Milei, who took office in December 2023, it went from about 20% agreement to 71% in 2024–25, and it is now the US's most reliable partner after Israel.

So the US didn't lose its allies' votes. It changed its own votes, and its allies kept theirs. Micronesia, the Marshall Islands and Palau all voted yes on climate protection and disaster risk reduction in 2025–26, as they always had. It's the US that now votes no.

## What the data can't tell you

- **Who asked for the vote.** The data records how a resolution was adopted, not who requested the recorded vote. The US voted no on every one of the 56 formerly routine resolutions, but another country might have asked for some of the votes.
- **Why a country voted the way it did.** A no can mean opposition to the whole text or to one paragraph. Countries explain their votes in the meeting records, which aren't in this data.
- **Agreement counts every vote the same.** A vote on Coffee Day counts as much as a vote on Ukraine. Researchers who want to weigh votes use "ideal point" estimates instead, such as [Erik Voeten's](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/LEJUQZ). I kept to simple agreement because anyone can check it.
- **Absences are left out.** A country that wasn't in the room doesn't count for or against agreement.

## How I did it

The UN's Dag Hammarskjöld Library publishes every General Assembly resolution with how it was adopted, and every country's vote on every recorded vote since 1946. I used regular sessions only (September to September), from the 45th (1990–91) to the 80th (2025–26), which the dataset covers to its end. Emergency and special sessions, such as the ones on Ukraine, are left out, so each session is comparable.

A "formerly routine" resolution is one adopted by recorded vote in 2025–26 whose title had only ever been adopted without a vote in earlier sessions. Titles are compared after dropping the ": resolution / adopted by the General Assembly" suffix, so small changes in wording count as a new title. The count of 56 is therefore a low estimate.

The code is in [`analysis/un-votes`](https://github.com/jawdat-rana/unexpected-signals/tree/main/analysis/un-votes). The UN data may be reused for non-commercial purposes with attribution.
