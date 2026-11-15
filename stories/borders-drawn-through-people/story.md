Everyone has seen the map of Africa with its ruler-straight borders, drawn by European powers who had never been to most of the places they divided. The usual story is that those lines cut peoples in two. But Africa isn't the only place where outsiders drew borders. Britain partitioned Punjab and Bengal in 1947. Britain and France drew most of the Middle East's borders after the First World War. Spain and Portugal's colonial provinces became the countries of South America. So I asked: is Africa really the exception?

To answer that, you need one map of the world's peoples drawn the same way everywhere. The only open one I found is old. In 1964, Soviet ethnographers published the *Atlas Narodov Mira*, an atlas of the peoples of the world. Researchers at ETH Zurich digitised it as GREG: 927 groups and their homelands. I laid it over today's borders and counted the groups whose homeland is split between neighbouring countries.

{{ signal value="1 in 4" label="of the 927 peoples on a world map of ethnic homelands live on both sides of a land border today, with at least 10% of their homeland in each country." }}

## Where the borders cut

{{ chart src="charts/map.js" data="data/border_cuts.csv" title="The borders that cut through peoples run across every inhabited continent" subtitle="Land borders that split at least one people's homeland, wider where they split more. Homelands as mapped in 1964; borders as of today." source="GREG (Weidmann, Rød and Cederman 2010), Natural Earth, own overlay" note="Hover or tap a border to see who it splits." size="wide" }}

Africa has the most red, as expected. But the map has red almost everywhere: through the Andes and the Amazon, across the Middle East, along the Himalayas, and all the way along the 49th parallel.

## Africa first, but not alone

{{ chart src="charts/regions.js" data="data/split_by_region.csv" title="Africa's borders split the most peoples, and South America comes second" subtitle="Share of each region's peoples whose homeland is split by a land border, with at least 10% of the homeland on each side" source="GREG (Weidmann, Rød and Cederman 2010), Natural Earth, own overlay" note="A people counts in the region of the country that holds most of its homeland." }}

Half of Sub-Saharan Africa's peoples are split. That's the highest share in the world, so the famous story holds up. The regions you might expect next are close behind it, though:

- **South America (38%).** It splits more peoples than the Middle East does. They are almost all Indigenous peoples: the Quechua across Peru, Bolivia and Ecuador, the Aymara between Bolivia and Peru, the Mapuche (the atlas says "Araucanians") between Chile and Argentina, and dozens of Amazon peoples between Brazil and its neighbours. The colonial provinces that became these countries were drawn around Spanish and Portuguese settlement, not around the people who already lived there.
- **The Middle East and North Africa (30%).** The Kurds are split between Turkey, Iran and Iraq. The Tuareg are split between Algeria, Niger and Mali. Azerbaijanis are split between Iran and Azerbaijan.
- **South Asia (22%).** This is a lower share, but it includes some of the largest peoples in the world. The 1947 Partition line split the Bengalis between India and Bangladesh and the Punjabis between India and Pakistan. The 1893 Durand Line split the Pashtuns (the atlas calls them "Afghans") and the Baloch between Afghanistan and Pakistan.

| Region | Split peoples, largest homelands first |
| --- | --- |
| South Asia | Baloch, Pashtuns, Bengalis, Tajiks, Punjabis, Brahui |
| Middle East and North Africa | Tuareg, Kurds, Beja, Azerbaijanis, Syrian Arabs |
| South America | Quechua, Aymara, Mapuche, and Amazon peoples such as the Baniwa and Mayoruna |

All 242 split peoples, with the countries they span, are in [the full list](data/split_groups.csv).

## The unexpected part

**The border that cuts the most peoples isn't in Africa.** It's the one between Canada and the United States. It splits seven peoples, including the Inuit and Yupik (the atlas says "Eskimos"), the Salish, the Ojibwe and the Haudenosaunee (Iroquois). Next come Kenya–Tanzania (including the Maasai), China–Myanmar, and Indonesia–Malaysia on Borneo, with six each. North America overall comes third, at 32%.

That points to a pattern that is more general than "colonial borders in Africa". A border splits peoples when the people who drew it weren't the people who lived there. That covers European empires in Africa and Asia. It also covers settler states in the Americas, where the border was drawn between two settler countries through the homelands of the peoples already living there.

Europe is near the bottom (15%), even though it has plenty of disputed borders. The exceptions are the Balkans and Hungary. Hungarians are split with Romania, and Serbs and Croats across Bosnia. There is one Dutch case: the Frisians, between the Netherlands and Germany. The former Soviet Union is lower still (12%), but that partly reflects how the map was made. Soviet ethnographers drew the atlas, and the Soviet republics' borders were themselves drawn around the nationalities the atlas maps.

## What the data can't tell you

- **The atlas defines majorities by country.** It has "Brazilians", "Argentinians" and "Syria Arabs" as separate peoples, so the majority of a country is never split by construction. That's why South America's split peoples are Indigenous, and why Arabic speakers across the Middle East don't count as one split group. With a map built on language instead of nationality, the Middle East would look far more split.
- **It is a 1964 map.** Peoples have moved, cities have grown, and some atlas boundaries are rough or just wrong. Group names are the atlas's own, and some are outdated; I used today's names in the text.
- **It counts groups, not people.** The atlas has no population figures. A small Amazon people counts the same as the Bengalis. Larger groups are also more likely to straddle a border, so a coarser map gives higher shares. Compare the regions with each other, not with other studies.
- **Only land borders count.** The Tamils of India and Sri Lanka are separated by a strait, not a border line, so they don't count as split.
- **The 10% cut-off is a choice.** It comes from Michalopoulos and Papaioannou's 2016 study of Africa. It filters out slivers where a 1964 boundary and a modern border don't quite line up. Breakaway areas like Somaliland are counted as part of the country most maps show.

## How I did it

GREG's homelands were overlaid on Natural Earth's 1:10m country borders using an equal-area projection. A polygon the atlas gives to two or three peoples counts for each of them. A people is split when at least two countries each hold 10% or more of its homeland, and two of those countries share a land border. That second rule leaves out diaspora pockets the atlas also mapped, such as Italians in Argentina.

GREG has no licence beyond a request to cite it, so this repo publishes only the derived areas, not the homeland shapes. The overlay runs in GitHub Actions, and the code is in [`analysis/ethnic-borders`](https://github.com/jawdat-rana/unexpected-signals/tree/main/analysis/ethnic-borders).
