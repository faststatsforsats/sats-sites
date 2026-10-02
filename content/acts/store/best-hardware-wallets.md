---
title: "Best hardware wallets compared"
description: "Compare Trezor, BitBox, Jade, Ledger, and Coldcard hardware wallets by controls, connections, and security design. Choose what fits your setup."
template: guide
updated: 2026-10-02
order: 2
understand_first:
  text: "How a bitcoin wallet works"
  url: https://fastfactsforsats.com/basics/how-a-wallet-works/
placements:
  - slug: trezor
    headline: Trezor
    text: "Safe 3 uses buttons; Safe 5 and Safe 7 use touchscreens. Check the Bitcoin-only firmware and phone support you need."
  - slug: bitbox
    headline: BitBox02 Nova
    text: "USB-C, supported Bluetooth use, a Bitcoin-only edition, and microSD backup."
  - slug: jade
    headline: Blockstream Jade
    text: "Compare Core's simpler controls with Plus's QR-signing camera."
  - slug: ledger
    headline: Ledger
    text: "Compare Nano devices with Flex and Stax touchscreens. Check current availability and phone support."
sources:
  - name: "Trezor"
    url: https://trezor.io/compare
  - name: "BitBox"
    url: https://bitbox.swiss/bitbox02/
  - name: "Blockstream Jade"
    url: https://blockstream.com/jade/jade-comparison/
  - name: "Ledger"
    url: https://shop.ledger.com/pages/hardware-wallet
  - name: "Coldcard"
    url: https://coldcard.com/q
  - name: "Coldcard security advisory"
    url: https://coldcard.com/security/status
  - name: "Coinkite store"
    url: https://store.coinkite.com/
  - name: "BitBox backup guide"
    url: https://support.bitbox.swiss/basics/bitbox02-setup-microsd-backup
---
Choose a hardware wallet you can use confidently. The useful differences are the screen, phone support, backup method, and how it protects your keys.

A bigger price tag does not fix a poor backup.

## Compare the models

| Model | Screen and controls | Connection options | Main distinction |
| --- | --- | --- | --- |
| Trezor Safe 3 | Small display; buttons | USB-C | Secure element; Bitcoin-only firmware option |
| Trezor Safe 5 | Color touchscreen | USB-C | Touchscreen with secure element |
| Trezor Safe 7 | Larger color touchscreen | USB-C; Bluetooth | Two secure chips; fuller phone support |
| BitBox02 Nova | Small display; edge sensors | USB-C; Bluetooth on supported devices | Bitcoin-only edition; microSD backup |
| Jade Core | Color display; buttons | USB-C; Bluetooth | Bitcoin and Liquid; blind-oracle design |
| Jade Plus | Color display; buttons; camera | USB-C; Bluetooth; QR | Adds camera for QR signing |
| Ledger Nano S Plus | Small display; buttons | USB-C | Multiple assets; closed core firmware |
| Ledger Nano X | Small display; buttons | USB-C; Bluetooth | Multiple assets; supports phone use |
| Ledger Flex | E Ink touchscreen | USB-C; Bluetooth; NFC functions | Larger touch display |
| Ledger Stax | Curved E Ink touchscreen | USB-C; Bluetooth; NFC functions | Largest Ledger display in this comparison |
| Coldcard Q | Large display; keyboard; camera | QR; microSD; USB-C; NFC | Bitcoin-focused; check [current security advisory](https://coldcard.com/security/status) |

Check the maker's current price, shipping, availability, and compatibility before ordering. The links below lead to official product information. This comparison covers the models in these guides, rather than every wallet on sale.

## Understand the features

### Secure chips

A secure element is a chip designed to resist physical attacks. Trezor, BitBox, Ledger, and Coldcard use secure elements. Jade uses a different design involving encrypted secrets and, in its standard PIN mode, a blind-oracle service. Neither design makes careless setup safe.

### Published firmware

Published code lets outside specialists inspect how the wallet works. Trezor, BitBox, Jade, and Coldcard publish firmware source, with different licenses and designs. Ledger's core device firmware is closed. Published code is useful transparency, rather than a guarantee.

### Bitcoin support

Trezor offers Bitcoin-only firmware, BitBox sells a Bitcoin-only edition, and Coldcard focuses on Bitcoin. Jade supports Bitcoin and Liquid. Ledger supports multiple assets. Check the exact edition you are ordering.

### Phone connections

Bluetooth and QR codes can make phone use easier, but connection type alone does not establish compatibility. Check your phone, operating system, and wallet app. Trezor Safe 3 and Safe 5 have limited iPhone functionality; Safe 7 offers fuller support.

## Choose for the way you will use it

- Simple controls: Compare Trezor Safe 3 and Jade Core.
- A touchscreen: Compare Trezor Safe 5 or Safe 7 with Ledger Flex or Stax.
- A microSD backup: Look at BitBox02 Nova. Its standard card backup is not encrypted by default.
- Signing through QR codes: Look at Jade Plus or Coldcard Q. Expect a few more steps to learn.

Coldcard owners should read the [current security advisory](https://coldcard.com/security/status) before setup or continued use. The maker requires updated firmware before creating a seed. An existing seed created on affected firmware may also need migration; updating alone does not repair it.

If you already own a working Ledger, understand its firmware and backup choices, including any optional recovery service, before deciding whether to replace it.

## Buy and set it up

Use the maker's store or its listed authorized sellers. Never trust a device that arrives with backup words already supplied.

Then follow [how to set up a hardware wallet](/store/hardware-wallet-setup/) and [how to store sats safely](/store/how-to-store-sats-safely/). A properly set-up wallet is more useful than a premium model still in its box.
