---
title: Gold priced in sats
description: How many sats a troy ounce of gold costs, month by month since 2011, from the World Bank gold price and the average bitcoin price.
template: chart
updated: '2026-10-02'
chart:
  slug: gold-in-sats
  alt: An ounce of gold cost 6,394,777 sats in August 2026
  source: World Bank Commodity Price Data (The Pink Sheet), gold, blockchain.com, market price (USD)
  pulled: October 2, 2026, 09:09 UTC
  data: /data/gold.json
attribution:
- worldbank
- blockchain
sources:
- name: World Bank Commodity Price Data (The Pink Sheet), gold
  url: https://www.worldbank.org/en/research/commodity-markets
- name: blockchain.com, market price (USD)
  url: https://www.blockchain.com/explorer/charts/market-price
---
<!-- auto:start -->
An ounce of gold cost 6,394,777 sats in August 2026. The chart shows sats per troy ounce of gold, monthly since 2011, redrawn every morning from the published data.

| When | Date | Sats per ounce |
| --- | --- | --- |
| now | August 2026 | 6,394,777 sats |
| a year ago | August 2025 | 2,926,762 sats |
| five years ago | August 2021 | 3,919,877 sats |
| ten years ago | August 2016 | 231,522,767 sats |

The numbers behind this chart are free to use: [/data/gold.json](/data/gold.json). Sats means satoshis, the smallest unit of bitcoin; 100,000,000 sats make one bitcoin.
<!-- auto:end -->

## Two stores of value, one chart

Gold is the thing people reached for to hold value before bitcoin existed, so pricing an ounce in sats puts the old answer and the new one on the same page. The dollar price of gold comes from the World Bank's monthly commodity data, which runs back to 1960; the bitcoin price is the monthly average from the daily chart. Divide the first by the second and the result is what an ounce costs someone counting in sats.

The line falls steeply because the two prices have moved at very different speeds. Gold rose from $1,340 an ounce in August 2016 to $4,411 in August 2026, a little more than three times. Over the same ten years a dollar went from buying about 173,000 sats to about 1,450, more than a hundred times fewer. So an ounce that cost about 232 million sats in 2016 cost about 6.4 million in 2026, even though gold itself more than tripled in dollars.

The line is not a one-way street. Gold gained in sats across 2014, 2018, and 2022, the years bitcoin fell hard, and again in the twelve months to August 2026, when the table above shows the ounce going from 2.9 million to 6.4 million sats. Those stretches are easy to miss on a logarithmic axis, so look at the table as well as the picture.

What this chart does not do is tell you which to hold; this site does not give that kind of advice, and the two assets differ in ways a price line cannot show. [Bitcoin and gold](https://fastfactsforsats.com/money/bitcoin-and-gold/) on Fast Facts walks through those differences: supply, portability, verification, and history. For homes and the stock market measured the same way, see [Gold, homes, and stocks in sats](/value/comparisons/).
