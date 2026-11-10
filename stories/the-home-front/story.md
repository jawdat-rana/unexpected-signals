[Part 1](../two-doors-into-washington/) looked at how other countries reach Washington. This part is about American money. Every dollar here comes from U.S. citizens and residents, given through PACs whose name or stated purpose is about a country abroad, a diaspora community or a faith. That's legal, and it's reported to the Federal Election Commission like any other PAC money.

I applied one rule to every group, and found 108 such committees between 2016 and 2026. In the 2024 cycle, 45 of them spent money on federal elections: $143M in total.

{{ signal value="$104M" label="spent on the 2024 elections through pro-Israel PACs, almost three-quarters of all the money in this story. About $76M of it went into primaries." }}

## One group changed scale in 2022

Until 2020, pro-Israel PACs spent about as much as J Street or the faith-based PACs, or less. That changed in the 2022 cycle, when AIPAC, the largest pro-Israel lobby, started its own PAC and a super PAC, the United Democracy Project. Pro-Israel PAC spending went from $11M in 2020 to $57M in 2022 and $104M in 2024.

{{ chart src="charts/totals.js" data="data/home_front_by_cycle.csv" title="Since 2022, pro-Israel PACs outspend all other groups combined" subtitle="Contributions and independent expenditures by U.S. PACs about a foreign country, diaspora or faith, per two-year election cycle" source="FEC bulk data, own list of committees" note="* The 2026 cycle has data up to the pre-general reports in mid-October 2026. Pro-Israel includes AIPAC PAC, United Democracy Project, DMFI, NORPAC and smaller PACs. J Street is counted as its own group." }}

Two things make these numbers bigger than the giving of most PACs:

- **Bundling.** Most of AIPAC PAC's $54M in 2024 was donors' money earmarked for a named candidate and passed on by the PAC. JStreetPAC and NORPAC work the same way. It still comes from individual Americans, but the PAC chooses and promotes the candidates.
- **Super PAC spending.** The United Democracy Project spent $38M for and against candidates in 2024, on top of AIPAC PAC's giving. A super PAC can take unlimited money, but it can't coordinate with a campaign.

## The money goes into primaries

About three-quarters of pro-Israel PAC money went into primaries in 2024, and over 80% so far in 2026. Fewer people vote in primaries than in general elections, so the same money goes further there.

{{ chart src="charts/primaries.js" data="data/home_front_by_cycle.csv" title="Pro-Israel PAC spending on primaries grew from $6M to $76M in four years" subtitle="Contributions and independent expenditures for primary elections, per two-year cycle" source="FEC bulk data, own list of committees" note="Primary share from itemized records, applied to each PAC's reported total. Runoffs not counted. * 2026 up to mid-October." }}

Among the other groups, J Street also leans toward primaries (about 60% in 2024). Faith-based PACs mostly spend in general elections: the Republican Jewish Coalition's super PAC put most of its $16.5M in 2024 into the general.

## Every group, side by side

Most diaspora groups have a PAC, but most of those PACs are small. Armenian-American and Taiwanese-American PACs exist and spent almost nothing in 2024. The Cuban-American U.S.-Cuba Democracy PAC gave $0.6M in 2016 and $15K in 2024.

| Group | 2024 total | 2024 primaries | 2026 so far |
|---|---|---|---|
| Pro-Israel | $103.9M | $75.6M | $126.7M |
| Faith-based (Jewish, Muslim, Hindu, Sikh) | $20.6M | $3.4M | $9.4M |
| J Street | $14.6M | $8.9M | $12.3M |
| Indian-American | $2.9M | $1.0M | $1.5M |
| Arab-American | $418K | $17K | – |
| Turkish-American | $131K | $78K | $154K |
| Ukrainian-American | $101K | $38K | $43K |
| Pakistani-American | $86K | $14K | $142K |
| Other diaspora | $80K | $37K | $77K |
| Iranian-American | $74K | $34K | $86K |
| Cuban-American | $15K | $8K | – |
| Critical of Israel policy | $14K | $14K | $194K |

Every committee and its numbers per cycle are in [the full list](data/home_front_committees.csv).

## What this doesn't show

- **This is not foreign money.** These are American donors and American PACs. Comparing them with Part 1 would mix two different things.
- **A faith is not a foreign policy.** Faith-based PACs are their own group because many of them work on domestic issues. Counting them with the country groups would suggest that their members' politics are about another country.
- **Only PACs that say what they are about.** A PAC with a neutral name isn't counted, for any group, so every total here is a floor.
- **PAC money only.** Lobbying, non-profits that don't report donors, and individual donations given directly to campaigns aren't here.
- **No party split.** Most of these groups give to both parties, but showing that fairly needs a baseline of all PACs. That's for a follow-up.

## How I did it

The FEC doesn't label PACs by cause. So I searched the names of every registered committee for countries, diasporas and faiths, and checked each hit by hand. Hits like Zions Bancorporation or tribal gaming PACs were left out. For each committee I took two numbers from its own summary reports: contributions to candidates and committees (which include bundled donations), and independent expenditures. Groups that file independent expenditures without being a PAC are added from the FEC's independent expenditure file. The primary share comes from the itemized records, where every transaction is marked as primary or general. The committee list, the code and the data are all in the repo.
