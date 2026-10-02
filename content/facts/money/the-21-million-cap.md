---
title: The 21 million bitcoin limit
description: "Bitcoin is limited to roughly 21 million coins. Learn where that number comes from, how the network enforces it, and when new issuance ends."
template: guide
updated: 2026-10-02
order: 2
attribution: [mempool]
sources:
  - name: Bitcoin Wiki, Controlled supply
    url: https://en.bitcoin.it/wiki/Controlled_supply
  - name: Bitcoin Core source, amount.h (MAX_MONEY) and validation.cpp (GetBlockSubsidy)
    url: https://github.com/bitcoin/bitcoin/blob/master/src/consensus/amount.h
  - name: mempool.space, block height (the live figure on this page)
    url: https://mempool.space
---
Bitcoin has a maximum supply of roughly:

21 million coins

About [[live:supply]] have already been issued, based on block [[live:height]] ([[live:when:fees]]).

The limit is not a company promise.

It is a rule checked by the network.

## Where does 21 million come from?

Bitcoin began by creating 50 new bitcoin per block.

Every 210,000 blocks, that amount is cut in half.

So issuance looks like this:

50

25

12.5

6.25

3.125

1.5625

And so on.

Add all those rewards together over Bitcoin's lifetime and the total approaches 21 million.

The exact maximum is slightly below 21 million. [Bitcoin halvings explained](/money/halvings/) has the dates.

## Who enforces the limit?

Bitcoin nodes do.

A node checks whether every new block follows Bitcoin's rules.

If a miner tries to create more bitcoin than the rules allow, properly operating nodes reject the block.

The miner can spend a fortune producing the block.

It still does not make the block valid.

Money can buy computing power. It cannot buy permission from arithmetic.

## Could the rule ever be changed?

Software can always be changed.

But changing Bitcoin's supply rule would only affect people who voluntarily chose to run the new rules.

Anyone who kept the original rules would continue recognizing the original Bitcoin network.

That makes changing the cap very different from a company simply issuing more shares.

There is no CEO of Bitcoin.

There is no board meeting where somebody votes to print another 10 million coins.

## When will the last bitcoin be created?

New issuance keeps shrinking with each halving.

The final tiny fractions are expected to be issued around the year 2140.

After that, miners are expected to earn revenue entirely from [transaction fees](/network/fees-and-the-mempool/).

## Issued does not mean available

Some bitcoin has been permanently lost.

Private keys have disappeared.

Coins have been sent to addresses that cannot be spent.

Some early mining rewards were never claimed.

Nobody knows the exact amount.

That means the number of bitcoin that can actually circulate is likely lower than the amount issued.

The supply ceiling cannot rise because coins were lost.

Lost coins simply make the remaining supply a little scarcer. The [sats per dollar chart](https://faststatsforsats.com/charts/sats-per-dollar/) on Fast Stats shows what a growing dollar supply and a fixed one of sats have done to the ratio between them.
