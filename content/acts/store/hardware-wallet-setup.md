---
title: "How to set up a hardware wallet"
description: "Set up a hardware wallet, protect and verify its backup, then test a receive and a send. Follow the maker's instructions for your model."
template: guide
updated: 2026-10-02
order: 3
understand_first:
  text: "How a bitcoin wallet works"
  url: https://fastfactsforsats.com/basics/how-a-wallet-works/
placements:
  - slug: trezor
    headline: Trezor Suite
    text: "Official software for setup, firmware, and supported backup checks."
  - slug: bitbox
    headline: BitBoxApp
    text: "Official setup and backup tools for BitBox devices. Treat a microSD backup as a secret."
  - slug: thebitcoinway
    headline: The Bitcoin Way
    text: "Guided self-custody help for people who prefer working with a person."
sources:
  - name: "Trezor"
    url: https://trezor.io/guides/trezor-devices/trezor-safe-3/get-started-with-the-trezor-safe-3
  - name: "Trezor backup formats"
    url: https://trezor.io/guides/backups-recovery/general-standards/single-share-backup-on-trezor
  - name: "BitBox backup guide"
    url: https://support.bitbox.swiss/basics/bitbox02-setup-microsd-backup
  - name: "The Bitcoin Way"
    url: https://www.thebitcoinway.com/
  - name: "mempool.space fee data"
    url: https://mempool.space/docs/api/rest#get-recommended-fees
---
Set aside about an hour without interruptions. You will create a wallet, protect the backup, check recovery, and make a small test transfer. Network confirmations can add waiting time.

Use this guide as the overall sequence. The maker's current instructions supply the exact steps for your model.

Coldcard has a separate required update sequence. Follow its [current security advisory](https://coldcard.com/security/status) before creating a seed; an affected existing seed may require migration.

## Before you begin

Have the device, a supported phone or computer, the official wallet app, and the required backup materials ready. Choose a private place where nobody can photograph or see your backup.

## <span class="step">Step 1</span> Check the device

Follow the maker's packaging and authenticity checks. Seals alone are not proof.

Stop if the device is already set up or comes with pre-filled recovery words. Contact the maker through its official site before using it.

## <span class="step">Step 2</span> Install the official app

Go directly to the maker's site. Avoid search ads, message links, and unsolicited "support" downloads.

Use trezor.io, bitbox.swiss, blockstream.com, or ledger.com to find the current software and instructions. Run any supported device authentication check.

## <span class="step">Step 3</span> Create a new wallet

Follow the official firmware and setup prompts. Choose a new wallet unless you deliberately intend to restore an existing one.

If you want Bitcoin-only firmware or an edition limited to Bitcoin, confirm the model supports it.

## <span class="step">Step 4</span> Record the backup

Write the recovery words exactly as shown, in order. The format varies: some wallets use 12 or 24 words, while newer Trezor backups commonly use 20. Follow your device's instructions, including any checks it asks you to complete.

BitBox can create a microSD backup. Its standard backup is not encrypted by default. Remove the card after setup, keep it secure, and follow the maker's instructions if you also want written recovery words.

Never photograph the backup, upload it, or share it with a helper.

## <span class="step">Step 5</span> Set device protection

Choose a strong PIN or device password, following the maker's rules. Avoid birthdays and easy patterns.

This protects access to the device. It does not protect a backup someone else has copied.

## <span class="step">Step 6</span> Verify the backup before funding

Use the maker's backup-check function where available. If its official method requires a reset and recovery, do that before depositing funds.

Follow the secure recovery procedure for the exact device and backup format. Do not improvise by typing hardware-wallet words into an ordinary website or app.

A backup is useful only if it restores the wallet. Find mistakes while the wallet is empty.

## <span class="step">Step 7</span> Receive a small test amount

Choose Receive in the official app and verify the complete address on the hardware wallet's screen. Confirm that the transfer uses Bitcoin's supported network, rather than another network's version of bitcoin.

Send a small amount from your exchange. Check withdrawal minimums and fees first. Wait for confirmation and check the balance. Timing depends on the sender, fee, and network activity.

## <span class="step">Step 8</span> Test sending

Send a small amount to another wallet you control. Check the complete destination address, amount, and fee on the hardware wallet before approving.

If the device and app show different details, cancel. Use the [network page on Fast Stats](https://faststatsforsats.com/network/) to understand current fees. Do not expect a cheap fee to guarantee a particular confirmation time.

## <span class="step">Step 9</span> Secure the backup and move more

Store the backup separately from the device. If you keep another copy, protect it in another secure location. Consider a metal backup compatible with your format.

Once the tests succeed, you can transfer more, checking the address on the device each time. [How to store sats safely](/store/how-to-store-sats-safely/) explains the storage plan.

## <span class="step">Step 10</span> Leave recovery instructions

Make a private plan describing the wallet, backup locations, and where a trusted person can find the official recovery instructions. Keep secret words out of an ordinary email or casual note.

The plan should survive a lost device and be understandable if you are no longer there to explain it.

## If you want help

The Bitcoin Way offers guided [self-custody](/store/how-to-store-sats-safely/) assistance. Check its current services and pricing. A legitimate helper can guide the process without seeing your backup words or controlling your funds.

You are finished when the backup is verified, the test transfers work, and the recovery plan is secure.
