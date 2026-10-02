---
title: Bitcoin hash rate since 2011
description: Explore Bitcoin's estimated hash rate since 2011. Learn what EH/s means, why daily readings vary, and what the chart can tell you.
template: chart
updated: '2026-10-02'
chart:
  slug: hashrate
  alt: Estimated hash rate was 898 EH/s on October 1, 2026
  source: blockchain.com, total hash rate
  source_links:
  - name: blockchain.com, total hash rate
    url: https://www.blockchain.com/explorer/charts/hash-rate
  pulled: October 2, 2026, 12:37 UTC
  data: /data/network.json
attribution:
- blockchain
sources:
- name: blockchain.com, total hash rate
  url: https://www.blockchain.com/explorer/charts/hash-rate
---
<!-- auto:start -->
The estimated network hash rate was 898 EH/s on October 1, 2026. Each point shows the estimated mining calculations per second, in EH/s.

| When | Date | EH/s |
| --- | --- | --- |
| latest | October 1, 2026 | 898 EH/s |
| a year ago | October 1, 2025 | 1,077 EH/s |
| five years ago | October 1, 2021 | 132 EH/s |
| ten years ago | October 1, 2016 | 1.9 EH/s |

Download the data behind this chart: [/data/network.json](/data/network.json). There are 100,000,000 sats in one bitcoin.
<!-- auto:end -->

## What hash rate measures

Hash rate estimates how many calculations Bitcoin miners perform each second as they compete to add blocks. One exahash is a billion billion calculations, so EH/s means exahashes per second.

The network does not report an exact total. The provider estimates it from the number of blocks found and the mining difficulty. Blocks arrive unevenly, so a daily estimate can jump or drop even when the underlying computing power changes little.

Look at the longer trend as well as individual days. The logarithmic scale shows equal multiples at equal distances. More computing power generally makes an attack requiring a large share of that power harder, but this line does not measure every aspect of security.

Hash rate can fall, and it is not a price forecast or a count of users. [The Bitcoin network today](/network/) puts it beside block height and current fee estimates.
