# Charts

The Daily Build draws every chart in this folder from the files in `data/`, using the shared style in `lib/chartstyle.py`, and commits the images. The Stats site publishes the folder as https://faststatsforsats.com/charts/ with open CORS headers and a one-hour cache, so other sites can embed a chart with a plain `<img>` tag and it updates by itself.

Each chart produces three files: `<slug>.png` (light, 1600 by 900), `<slug>-dark.png` (dark), and `<slug>.svg` (light, for print and crisp embeds). The chart page at `/charts/<slug>/` on the Stats site shows the light or dark version to match the reader's setting and offers the embed snippet.

`index.json` lists every chart: slug, title, the finding in one sentence, the data file it was drawn from, the source, and the time it was drawn. The Social and Newsletter agents read it to pick the day's chart.

The rules every chart follows (from the style guide and the chart style): the title states the finding; one axis, never two; categorical colors in a fixed order; thin lines; the source, pull time, and site name in the footer; light and dark versions drawn from the same data.
