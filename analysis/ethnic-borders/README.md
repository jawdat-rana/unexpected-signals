# Ethnic borders

Which peoples do today's borders split? Used by the story
`stories/borders-drawn-through-people`.

1. `overlay.py` downloads GREG (a digitised version of the 1964 Atlas Narodov
   Mira, 927 groups) and Natural Earth 1:10m countries. It measures each
   group's homeland area per country in an equal-area projection. GitHub
   Actions runs it (`fetch` workflow, `name=borders`) and commits the derived tables,
   not the GREG polygons, to the `raw-borders` branch.
2. `story_data.py` decides which groups are split, groups them into regions,
   finds the land borders that cut them, and writes the chart data and a light
   world map (Natural Earth) to `stories/borders-drawn-through-people/data/`.

```
pip install geopandas pyogrio shapely pyproj
git worktree add raw-borders origin/raw-borders
python analysis/ethnic-borders/story_data.py raw-borders
```

Method notes:
- A group is split when at least two countries each hold 10% or more of its
  homeland (the cut-off of Michalopoulos and Papaioannou 2016) and two of
  those countries share a land border. The border rule leaves out diaspora
  pockets the atlas also mapped, like Italians in Argentina.
- A polygon the atlas gives to two or three groups counts for each of them.
- Natural Earth's breakaway areas (Somaliland, Northern Cyprus, Baikonur) are
  folded into the state most maps show.
- Each group's region is the region of the country holding most of its
  homeland. The region list is in `story_data.py`.
- The atlas defines many majorities by state ("Brazilians", "Syria Arabs"), so
  a country's majority is almost never split by construction.

Data licences: GREG states no licence and asks for a citation (Weidmann, Rød
and Cederman 2010, *Journal of Peace Research* 47(4)). Only derived areas are
published here. Natural Earth is public domain.
