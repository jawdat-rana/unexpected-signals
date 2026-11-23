Two claims come up again and again in Dutch housing debates. One is about wealth: that the rich own the housing and everyone else rents. The other is about newcomers: that highly skilled migrants, the *kennismigranten*, take the jobs and the homes. Both can be checked against public data from Statistics Netherlands (CBS), at least partly. This story checks what it can and is clear about where the data stops.

{{ signal value="59%" label="of the Indian nationals who moved to the Netherlands in 2023–2025 settled in just five municipalities: Amsterdam, Eindhoven, The Hague, Rotterdam and Utrecht. Indian nationals are the largest group of knowledge migrants." }}

## At province level, the richest places own the fewest homes

Put the twelve provinces side by side and a clear pattern appears. Noord-Holland and Utrecht have the highest share of millionaire households (8% and 9%) and the lowest share of households that own their home (50% and 56%). Zeeland and Drenthe are the other way round: 67% own their home, and 5–6% are millionaires.

That is surprising, because CBS counts the value of your home, minus the mortgage, as wealth. You'd expect owning and being wealthy to go together.

## Town by town, the pattern flips

Look at the 342 municipalities instead and it turns around. Places with more millionaire households also have more households that own their home (a rank correlation of 0.49). Bloemendaal and Laren, where more than a third of households are worth €1 million or more, are 70%+ owners.

{{ chart src="charts/wealth.js" data="data/wealth_vs_owning.csv" title="Provinces slope down, municipalities slope up" subtitle="Share of households that own their home, and share worth €1 million or more, 1 January 2025. Grey circles are municipalities, sized by number of homes; red dots are provinces." source="CBS StatLine 86379NED" note="Wealth includes the home's value minus the mortgage. CBS rounds both shares to whole percentages." }}

The provinces mislead because each one mixes two kinds of place. Big cities like Amsterdam (30% owners), Rotterdam (34%) and Utrecht city (40%) have many renters and a fair number of wealthy households. Their size pulls the provincial average down. Meanwhile, the wealthy suburbs around them have high ownership. Averaging over a province hides both. Statisticians call this the ecological fallacy: a pattern between groups that doesn't hold inside them.

## Private landlords stopped growing in 2024

Homes owned by private landlords (individuals, companies and investors, but not housing associations) grew from 852,000 in 2012 to 1.19 million on 1 January 2024. A year later there were 6,000 fewer. It's a small drop, but it's the first since 2019, and it came in the year the Affordable Rent Act (*Wet betaalbare huur*) capped rents on mid-priced homes from July 2024.

{{ chart src="charts/landlords.js" data="data/tenure_national.csv" title="Homes owned by private landlords fell for the first time since 2019" subtitle="Homes owned by private landlords on 1 January, 2012–2025" source="CBS StatLine 82900NED" note="Private landlords: individuals, companies and institutional investors. Housing associations are counted separately." }}

One year isn't a trend, and the 2026 figures will show whether it continues.

## Skilled migrants: a small group nationally

In 2025, 13,900 knowledge migrants came to the Netherlands, down from a peak of 26,200 in 2022. Another 12,200 people came as family of a labour migrant. Between 2015 and 2024, about 155,000 knowledge migrants arrived, while the housing stock grew by about 690,000 homes.

{{ chart src="charts/arrivals.js" data="data/knowledge_migrants.csv" title="Every year, the Netherlands adds far more homes than it gets knowledge migrants" subtitle="Homes added to the housing stock and knowledge migrants arriving, per year" source="CBS StatLine 82900NED and 84809NED" note="Homes added: the change in the housing stock between 1 January of that year and the next. Knowledge migrants: non-EU/EFTA immigrants with a knowledge-migrant permit." }}

Many of them also leave again. Of the knowledge migrants who arrived in 2010, 72% had left within five years. That share has been falling, to 46% for those who arrived in 2019. More of them are staying, which means more of them will be looking to buy.

{{ chart src="charts/leaving.js" data="data/knowledge_migrants.csv" title="Fewer knowledge migrants leave within five years" subtitle="Share of each year's knowledge migrants who had left the Netherlands within five years of arriving" source="CBS StatLine 84809NED" note="The 2020 arrivals, the last year with five years of data, came during the pandemic." }}

Counting every arrival year since 1999, about 119,000 knowledge migrants are still in the Netherlands, along with about 108,000 family members who came with labour migrants. Even if every knowledge migrant headed a separate household, that would be about 1.5% of the 8.3 million homes.

## But the pressure is local

The national numbers hide where people actually settle. CBS doesn't publish knowledge migrants per municipality, but it does publish immigration by nationality. Indian nationals are the largest single group of knowledge migrants (2,550 of the 13,900 in 2025), so they're a reasonable, if imperfect, guide.

{{ chart src="charts/cities.js" data="data/indian_arrivals_by_municipality.csv" title="In Amstelveen, Eindhoven and Delft, Indian arrivals are five to ten times the national rate" subtitle="Indian nationals who moved to each municipality in 2023–2025, per 1,000 homes. The 12 municipalities with the most arrivals." source="CBS StatLine 85451NED and 82900NED" note="Not all Indian nationals are knowledge migrants: students and family members are included." }}

Amstelveen had 34 Indian arrivals per 1,000 homes in three years, against 3.5 nationally. Those are the places where the debate is about something real. A national figure can't settle it either way.

## What this can't tell you

- **Who buys which home.** The land registry (Kadaster) doesn't record the buyer's residence permit, and CBS doesn't publish home ownership by migration reason. Answering that needs a custom CBS table from its protected microdata. That's possible, but it's paid and not open.
- **Whether migrants take jobs.** These tables say nothing about jobs. Knowledge migrants must earn above a salary threshold set by the government, and a fair test would compare vacancies and unemployment in the hub cities. That's a separate story.
- **Who owns more than one home.** CBS counts homes by owner type, not owners by number of homes.
- **Cause and effect.** Every comparison here is descriptive.

## How I did it

All data comes from CBS StatLine, downloaded as full-table exports by a GitHub Action and filtered to totals. Ownership and wealth by municipality both come from the same wealth table (86379NED), so the two shares refer to the same households. Knowledge-migrant arrivals and departures come from 84809NED, which follows each year's arrivals and records how many are no longer in the country after one to 26 years. "Still here" means arrivals minus those recorded as gone at the latest measurement. The code and data are in the repo.
