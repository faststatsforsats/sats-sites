---
title: How many sats are in a bitcoin?
description: "There are exactly 100,000,000 sats in one bitcoin. See the units, learn why Bitcoin uses them, and convert BTC to sats."
template: guide
updated: 2026-10-02
order: 2
attribution: [coingecko]
sources:
  - name: Bitcoin Wiki, Units
    url: https://en.bitcoin.it/wiki/Units
  - name: Bitcoin Core source, amount.h (amounts are integers of satoshis; MAX_MONEY is 21 million coins)
    url: https://github.com/bitcoin/bitcoin/blob/master/src/consensus/amount.h
  - name: Fast Stats for Sats, sats converter
    url: https://faststatsforsats.com/tools/sats-converter/
---
There are exactly:

100,000,000 sats in 1 bitcoin

That means:

1 sat = 0.00000001 BTC

At [[live:price]] per bitcoin ([[live:when]]):

$1 buys [[live:sats-per-dollar]]

$100 buys [[live:sats-for:100:usd]]

## The Bitcoin units

| Unit | Bitcoin | Sats |
| --- | --- | --- |
| 1 bitcoin | 1 BTC | 100,000,000 |
| 1 millibitcoin | 0.001 BTC | 100,000 |
| 1 bit | 0.000001 BTC | 100 |
| 1 sat | 0.00000001 BTC | 1 |

In practice, two units matter most:

Bitcoin for big numbers. Sats for small ones.

The middle units never became very popular.

## Why 100 million?

Bitcoin was designed to keep track of money using whole numbers rather than floating-point decimals.

That helps computers avoid rounding problems.

With a maximum of roughly 21 million bitcoin and 100 million sats in each one, the full supply fits neatly into the numerical system used by Bitcoin software.

It is not a display preference.

It is part of how Bitcoin works.

## A shortcut for converting dollars to sats

Take:

100,000,000 ÷ bitcoin price

If bitcoin is $100,000:

$1 = 1,000 sats

If bitcoin is $50,000:

$1 = 2,000 sats

Lower bitcoin price means more sats per dollar.

Higher bitcoin price means fewer sats per dollar.

Simple arithmetic. No crystal ball required. For any amount, the [sats converter](https://faststatsforsats.com/tools/sats-converter/) on Fast Stats does the math, and there are ready-made pages such as [$100 in sats](https://faststatsforsats.com/sats/100-usd/).

## Why sats matter

A whole bitcoin may cost more than most people would spend on almost anything besides a house or a car.

That does not mean bitcoin cannot be divided.

It can be divided 100 million ways.

Sats make those fractions feel like ordinary numbers.

<!-- quote: whole-gold-bar -->

You do not need a whole coin any more than you need a whole gold bar.

<!-- /quote: whole-gold-bar -->
