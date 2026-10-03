---
title: "Who decides Bitcoin's rules?"
description: "No single person, company, or government decides Bitcoin's rules. Learn who proposes changes, who checks the rules, and what a change takes."
template: guide
updated: 2026-10-02
order: 2
attribution: [mempool]
sources:
  - name: "bitcoin.org FAQ, Who controls the Bitcoin network?"
    url: https://bitcoin.org/en/faq
  - name: "Bitcoin Wiki, Full node (what full nodes check and reject)"
    url: https://en.bitcoin.it/wiki/Full_node
  - name: "bitcoin.org, Bitcoin Core validation (full nodes and the 21 million limit)"
    url: https://bitcoin.org/en/bitcoin-core/features/validation
  - name: "Bitcoin developer guide, Block Chain (consensus rule changes, hard forks and soft forks)"
    url: https://developer.bitcoin.org/devguide/block_chain.html
  - name: "BIP 99, Motivation and deployment of consensus rule changes (what miners can and cannot impose)"
    url: https://github.com/bitcoin/bips/blob/master/bip-0099.mediawiki
  - name: "BIPs repository, README (what publishing a BIP does and does not mean)"
    url: https://github.com/bitcoin/bips
  - name: "BIP 3, Updated BIP Process"
    url: https://github.com/bitcoin/bips/blob/master/bip-0003.md
  - name: "Bitcoin Core, CONTRIBUTING.md (what a consensus change requires)"
    url: https://github.com/bitcoin/bitcoin/blob/master/CONTRIBUTING.md
  - name: "Bitcoin Core, About"
    url: https://bitcoincore.org/en/about/
  - name: "BIP 141, Segregated Witness (Consensus layer)"
    url: https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki
  - name: "Bitcoin Core source, chainparams.cpp (SegWit height 481,824)"
    url: https://github.com/bitcoin/bitcoin/blob/v29.0/src/kernel/chainparams.cpp
  - name: "blockchain.com, block 481,824 (mined August 24, 2017, UTC)"
    url: https://www.blockchain.com/explorer/blocks/btc/481824
  - name: "BIP 341, Taproot (90% threshold and activation at block 709,632)"
    url: https://github.com/bitcoin/bips/blob/master/bip-0341.mediawiki
  - name: "blockchain.com, block 709,632 (mined November 14, 2021, UTC)"
    url: https://www.blockchain.com/explorer/blocks/btc/709632
  - name: "Bitcoin Core 0.21.1 release notes (Taproot signaling)"
    url: https://bitcoincore.org/en/releases/0.21.1/
  - name: "Bitcoin Optech Newsletter #175, November 17, 2021 (Taproot activated)"
    url: https://bitcoinops.org/en/newsletters/2021/11/17/
  - name: "Bitcoin Optech, Soft fork activation (how SegWit activated)"
    url: https://bitcoinops.org/en/topics/soft-fork-activation/
  - name: "IRS Chief Counsel Advice 202114020 (the August 1, 2017 hard fork and Bitcoin Cash)"
    url: https://www.irs.gov/pub/irs-wd/202114020.pdf
  - name: "UAHF Technical Specification, version 1.6 (the block size rule behind Bitcoin Cash)"
    url: https://upgradespecs.bitcoincashnode.org/uahf-technical-spec/
  - name: "mempool.space, block height (the live figure on this page)"
    url: https://mempool.space
  - name: "Fast Stats for Sats, Bitcoin hash rate since 2011"
    url: https://faststatsforsats.com/charts/hashrate/
---
<!-- quote: nobody-decides -->

No single person, company, or government decides Bitcoin's rules.

<!-- /quote: nobody-decides -->

<!-- quote: rules-live-in-software -->

The rules live in software that people choose to run, and a new rule is enforced only by those who adopt it.

<!-- /quote: rules-live-in-software -->

So the network follows the rules its participants actually check.

## What are the rules?

A node is a computer running Bitcoin software.

A full node downloads every block, each a batch of transactions, and checks it against a list of rules.

Those are the consensus rules. A few of them:

- A block may create only so many new bitcoin
- Every payment needs a valid signature
- The same coins cannot be spent twice
- A block can only be so big

[Bitcoin halvings explained](/money/halvings/) and [The 21 million bitcoin limit](/money/the-21-million-cap/) cover the first, and [How Bitcoin fees work](/network/fees-and-the-mempool/) the last.

Break one, and a full node rejects the block, even if every other node accepts it.

More than [[live:height]] blocks have passed those checks so far ([[live:when:fees]]). [The Bitcoin network today](https://faststatsforsats.com/network/) on Fast Stats shows the latest one.

## Who does what?

**Developers** write and review the code. Anyone can propose a change. Nobody can make you install it.

**Node operators** run it: businesses and people at home. Their nodes do the checking.

**Miners** spend computing power to build new blocks. They choose which transactions go in. They cannot make a rule-breaking block valid.

[Bitcoin hash rate since 2011](https://faststatsforsats.com/charts/hashrate/) on Fast Stats shows an estimate of that computing power over time.

**Users and businesses** choose which software to trust and which coin to accept.

<!-- quote: pickup-game -->

Think of a pickup game with no league and no referee.

The players call the fouls.

<!-- /quote: pickup-game -->

Anyone can suggest a new rule. It only counts in games where the players agree to it.

## How is a change proposed?

Usually as a Bitcoin Improvement Proposal, or BIP: a public document that describes the idea.

Drafts that meet the editors' criteria get a number and a place in a public archive on GitHub, the BIPs repository.

A BIP is a proposal, not a law.

The repository says publication does not mean a proposal is a good idea, has community consensus, or is about to be adopted.

BIP 3, the process document, is blunter: no formal or informal body decides which BIPs get adopted.

## Soft fork or hard fork?

A soft fork adds or tightens rules. Blocks made under the new rules still pass the old checks, so nodes that never upgrade stay on the same blockchain. That holds while most mining power enforces the new rules.

A hard fork loosens or replaces a rule. Blocks that use the new rule fail the old checks, so nodes that do not upgrade reject them, and the chain can split in two for good.

SegWit, which gave signatures a separate part of the block, was a soft fork. Its rules took effect at block 481,824, in August 2017.

Taproot, which added a new kind of signature, was another. Miners signal readiness by marking their blocks, and Taproot needed that mark on 90% of the blocks in a window of about two weeks. Upgraded nodes began enforcing it at block 709,632, in November 2021.

Bitcoin Cash came from a hard fork. On August 1, 2017, a group that wanted bigger blocks switched to a different size rule. The chains parted after block 478,558: two games, two coins.

## Where it gets messy

Change is slow.

SegWit's BIP is dated December 2015 and Taproot's January 2020, so each took more than a year and a half.

Part of that is deliberate. Bitcoin Core, a direct descendant of the original Bitcoin program, requires extensive mailing list discussion and a numbered BIP before any consensus change.

Change can also be contentious.

SegWit stalled while miner signaling sat far below the 95% it needed. Users, then miners, exchanges, and other businesses pushed plans of their own before it activated, and how much each contributed is still debated.

Influence is uneven.

Signals are counted in blocks, so the biggest miners count most. A large business running its own node carries more weight than a hobbyist. How much more is a judgment, not a measurement.

If a company holds your coins, the checking is up to the company, not you. [How a bitcoin wallet works](/basics/how-a-wallet-works/) explains who holds the keys, and [How to store sats safely](https://fastactsforsats.com/store/how-to-store-sats-safely/) on Fast Acts walks through the choices.

A government can regulate how people use bitcoin. That is not the same as changing what a node accepts.

And "nobody decides" does not mean "nothing changes." SegWit and Taproot both changed the rules.

## Why this matters if you hold bitcoin

The 21 million limit is not a company promise.

It is one of the rules full nodes check.

Could it be raised?

A block that created extra coins would break today's rules, and today's full nodes would reject it.

So it would take a hard fork: the people and businesses running nodes would have to choose new software.

Anyone who refused would stay on the original chain, with the original limit.

Possible in principle. Whether enough people would ever choose it is a judgment, not a fact.

<!-- quote: someone-to-play-with -->

Anyone can write new rules for Bitcoin. The hard part is finding someone to play with.

<!-- /quote: someone-to-play-with -->
