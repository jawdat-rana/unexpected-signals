The U.S. midterms just ended, and "foreign money in elections" is back in the headlines. So I looked at the public data. First, the legal point: foreign nationals and governments can't donate to U.S. campaigns. They have two legal ways to influence Washington instead.

**Door 1: companies.** A foreign firm's U.S. subsidiary can run a PAC, funded by its American employees. **Door 2: hired agents.** Governments, state companies and parties hire registered U.S. lobbyists and PR firms, and have to disclose it under the Foreign Agents Registration Act (FARA).

{{ signal value="$23.7M" label="given in the 2024 cycle by 109 PACs of foreign-owned companies. UBS's U.S. PAC alone gave $2.9M." }}

## Two doors, two kinds of economy

When you put each country on both axes, the countries don't land in one cloud. They split by which door they use.

{{ chart src="charts/two-doors.js" data="data/two_doors_2024.csv" title="Countries reach Washington through their companies or through hired agents" subtitle="PAC giving by U.S. subsidiaries of each country's companies (2024 cycle) against foreign clients with registered U.S. agents (2023–24)" source="FEC and DOJ FARA eFile bulk data, own matching of PACs to foreign parents" note="Countries with no PAC money are shown if they had at least 20 FARA clients." }}

- **Through companies:** Switzerland, France and the Netherlands give mostly through PACs and have few FARA clients. The Netherlands has $0.8M through PACs and just 3 FARA clients.
- **Through hired agents:** Saudi Arabia, Ukraine, the UAE and Qatar have dozens of FARA clients and no PAC money at all.
- **Both:** Japan, the UK, Germany and Canada use both doors.

The pattern follows how each economy is built. Countries with big private multinationals end up in U.S. politics through their employees. Countries without big U.S. subsidiaries, often where the state runs the economy, hire lobbyists instead.

## Door 1, country by country

Swiss, German, British and Japanese firms lead. The Netherlands is seventh, through four PACs: Aegon's Transamerica, Philips, Heineken and Ahold Delhaize.

{{ chart src="charts/pac-bars.js" data="data/pac_money_by_country_2024.csv" title="Swiss and German companies' PACs gave the most" subtitle="Contributions from U.S. PACs of foreign-owned companies to other committees, by the parent company's country, 2024 cycle" source="FEC bulk data, own matching of PACs to foreign parents" note="Every matched PAC is in [the full list](data/matched_pacs_2024.csv)." }}

## What this doesn't show

- PAC money comes from Americans, and as a group these PACs give to both parties. OpenSecrets puts 2024 at roughly 42% Democratic and 58% Republican.
- FARA counts clients, not dollars. The bulk data has no amounts.
- Ukraine's FARA count is wartime lobbying, which is its own story.
- The door groups use simple cut-offs, written in the code. Countries near a line, like South Korea, could go either way.

## How I did it

The FEC doesn't mark which PACs have a foreign parent, so I matched corporate PACs to a hand-made list of 195 foreign parent companies. Then I totalled each PAC's contributions to other committees by the parent's country. A company counts where it is run, not where it is registered. So Medtronic, Accenture, Chubb and CNH Industrial are left out, and Airbus counts as French. FARA clients are counted per country for 2023 and 2024. The parent list, the matches and the code are all in the repo.

Part 2 looks at the other side: American donors who give to foreign-policy and diaspora PACs, counted with the same method.
