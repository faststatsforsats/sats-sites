---
title: "Bitcoin in five minutes"
description: "Five short answers for a first look at Bitcoin: what a sat is, whether you need a whole coin, what a wallet holds, the price, and the rules."
template: route
updated: 2026-10-02
nav: first
nav_label: "Five-minute guide"
attribution: [coingecko]
more_label: "The full explanation:"
stop_label: "Question {n} of {total}"
# Each stop quotes the explainer behind it, word for word: `take` lifts that page's opening blocks, `under` the blocks
# under one of its subheads. The questions for stops 2, 3, and 5 are the home page's three cards.
stops:
  - question: "What is a sat?"
    from: /basics/what-is-a-sat/
    take: 5
  - question: "Do I need a whole bitcoin?"
    from: /basics/how-many-sats-in-a-bitcoin/
    under: "Why sats matter"
  - question: "What does a wallet actually hold?"
    from: /basics/how-a-wallet-works/
    take: 2
  - question: "Why does bitcoin have a price?"
    from: /money/why-bitcoin-has-a-price/
    take: 5
  - question: "Who decides the rules?"
    from: /network/who-decides-the-rules/
    take: 3
# The optional knowledge check. `answer` is the number of the right option. Each `why` is pulled at build time from the
# passage that the explainer behind the stop with the same number marks with <!-- quote: name -->, so the check keeps
# no copy of it. A mark that is taken out leaves that reason off the page and prints a note; the build goes through.
check:
  heading: "Check what stuck"
  intro: "Five quick questions, one for each answer above. Your answers are not saved or sent anywhere."
  button: "Check my answers"
  show: "Show the answer"
  right: "Correct."
  wrong: "Not quite."
  answer_is: "The answer:"
  score: "You got {right} of {total}."
  unanswered: "Pick an answer for every question to see your score."
  questions:
    - q: "How many sats are in one bitcoin?"
      options: ["1,000", "1,000,000", "100,000,000"]
      answer: 3
      why: {quote: sats-in-a-bitcoin}
    - q: "Do you need to buy a whole bitcoin?"
      options: ["Yes, one coin is the smallest amount", "No, it can be divided 100 million ways", "Only some exchanges sell less than one"]
      answer: 2
      why: {quote: whole-gold-bar}
    - q: "What does a bitcoin wallet manage?"
      options: ["Your keys", "The coins themselves", "Your bank details"]
      answer: 1
      why: {quote: manages-keys}
    - q: "Where does bitcoin's price come from?"
      options: ["The Bitcoin software sets it", "One official exchange sets it", "People buy it and people sell it"]
      answer: 3
      why: {quote: latest-trade}
    - q: "Who decides Bitcoin's rules?"
      options: ["The developers", "The biggest miners", "No single person, company, or government"]
      answer: 3
      why: {quote: rules-live-in-software}
next:
  heading: "Where to go next"
  links:
    - text: "How Bitcoin Works, Without the Jargon"
      url: /
      note: "Every explanation on Fast Facts, by subject."
    - text: "Sats converter"
      url: https://faststatsforsats.com/tools/sats-converter/
      note: "See what any amount is in sats right now, on Fast Stats."
    - text: "How to store sats safely"
      url: https://fastactsforsats.com/store/how-to-store-sats-safely/
      note: "The practical next step once you know what a wallet holds, on Fast Acts."
---
<p class="lead">Five questions, each answered in under a minute.</p>

Every answer below is taken from the full explanation behind it. Stop after five minutes, or follow any link to keep going.
