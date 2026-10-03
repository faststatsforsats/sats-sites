---
title: What is a sat worth today?
description: See what sats are worth in money, groceries, gold, and homes. Explore free charts, historical comparisons, and a converter with the sources shown.
template: home
updated: 2026-10-02
attribution: [coingecko, bls, fred, worldbank, altme, mempool, blockchain]
# The first screen (Jim's improvement plan, October 2026). The headline, the introduction, and the button are his words.
# `note`, under the button, is the first two sentences of the paragraph that opened his Stats copy, word for word. The
# first of them keeps the live figure on the first screen; it went back in on October 3, 2026, at his word.
hero:
  headline: "What does your money buy in sats?"
  intro: "A dollar. A dozen eggs. A place to live. See how Bitcoin changes the numbers, then explore the history for yourself."
  button:
    text: "Explore the numbers"
    url: /charts/
  note: "A dollar buys [[live:sats-per-dollar]] right now. A sat is a small piece of bitcoin: 100,000,000 sats make one bitcoin."
# Words around the comparison beside the headline (the figures and the sentence under them come from lib/stats_data.py).
# `dates` sits under the one-year and five-year views, `dates_today` under the Today view, where the dollar figure is
# the latest price with its own time and the other two rows name their month and quarter.
compare:
  heading: "A dollar, a dozen eggs, and a new home: today, one year ago, five years ago"
  legend: "Show"
  today_label: "Today"
  price_label: "Latest price"
  dates: "A dollar uses the daily average price, eggs the monthly average, and a new home the quarterly figure."
  dates_today: "Eggs use the latest monthly average and a new home the latest quarterly figure."
today_heading: "What is a sat worth today?"
# Three stories. Each card opens a chart: a picture (`art`, from shared/art.yml) or two bars from the comparison
# (`figure`), the headline, the chart's own finding as the fact, then one quoted line. `take` is the plan's line for
# that chart; a card without one shows its picture's own caption.
stories_heading: "Three stories in the numbers"
stories:
  - art: hen-two-price-tags
    headline: "Same carton. Two price tags."
    url: /charts/eggs-in-sats/
    button: "Explore the egg chart"
  - art: gold-and-paper-airplane
    headline: "Gold versus Bitcoin: change the dates, change the story."
    take: "Two things can be scarce and still take different roads."
    url: /charts/gold-in-sats/
    button: "Explore the gold chart"
  - figure: home
    figure_title: "US median new-home sale price, in bitcoin"
    headline: "Same front door. Different arithmetic."
    take: "Before you count the bedrooms, count the assumptions."
    url: /charts/home-in-bitcoin/
    button: "Explore the home chart"
converter_heading: "Sats converter"
converter_more: "Open the converter page to see how it works"
# One chart a week, in turn, starting again after the last, so "This week's chart" stays true. Weeks run Monday to
# Sunday, counted from `start`. Each line is the plan's line for that chart, printed in quotation marks with no name on it. The three charts the stories above
# open are left out of the turn.
weekly:
  heading: "This week's chart"
  start: 2026-09-28
  charts:
    - slug: twenty-five-a-week
      line: "Regular buying can build a stack. The market still owes you nothing."
    - slug: sats-per-dollar
      line: "A dollar can buy more sats and fewer groceries. Always ask what is sitting on the other side of the price tag."
    - slug: price-usd
      line: "A mountain looks smoother on a postcard than it does under your boots."
    - slug: fear-greed
      line: "A loud crowd can still be facing the wrong direction."
    - slug: hashrate
      line: "Do not judge the whole engine by one rattle."
# Shown once the weekly email's form exists (newsletter_embed in sites/stats/site.yml, step 25)
subscribe:
  heading: "Get one surprising chart each week."
sources:
  - name: blockchain.com, market price and hash rate
    url: https://www.blockchain.com/explorer/charts
  - name: CoinGecko, today's price in 30 currencies
    url: https://www.coingecko.com
  - name: U.S. Bureau of Labor Statistics, average prices
    url: https://www.bls.gov/cpi/
  - name: FRED, Federal Reserve Bank of St. Louis
    url: https://fred.stlouisfed.org
  - name: World Bank Commodity Price Data (The Pink Sheet)
    url: https://www.worldbank.org/en/research/commodity-markets
  - name: alternative.me Crypto Fear & Greed Index
    url: https://alternative.me/crypto/fear-and-greed-index/
  - name: mempool.space, recommended fees and block height
    url: https://mempool.space
---
The charts refresh each morning from public data, with sources and dates shown. Some figures, including hash rate, are estimates. Explore the history, check a price, or try the [sats converter](/tools/sats-converter/). [Fast Facts for Sats](https://fastfactsforsats.com/) explains Bitcoin; [Fast Acts for Sats](https://fastactsforsats.com/) shows how to use it.
