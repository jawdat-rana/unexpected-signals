# How this is made

Yes, this site is made with AI, and a lot of it. Claude, an AI model from Anthropic, writes the code, downloads and cleans the data, builds the charts and drafts the text. It does that well and fast. Without it, one person couldn't run a story a week, each with its own data pipeline.

What it doesn't do is decide. These parts are mine:

- **The question.** Every story starts with something I wanted to know, or a claim I wanted to check. Is autumn really the worst month for trains? Did October's flood of software flaws mean more attacks?
- **What's worth testing.** Which data can answer the question, and which comparison is fair.
- **What's fair to say.** I read each draft against the numbers and pull back anything that goes further than the data does.
- **What to cut.** Claims that rest on a single source, or that I can't check, come out.

## An example

The first draft of [Black October](../stories/black-october/) said many of October's new security flaws were found with AI, that the number of flaws attackers used barely moved, and that patching was what broke things in November. The data supports a weaker version of each. Under 2% of the flaw records credit AI, attacks did rise (just far less than flaws), and the November outages had several causes. The published version says "some of them found with AI", "rose far less" and "what grew was the pressure to patch fast".

The draft also said that many security teams now run AI tools without crediting them. That may be true, but nothing in the data shows it, so it now says the records can't tell.

## Check it yourself

You don't have to take my word, or the AI's. Every story lists its data sources with their licences, every chart links to the numbers behind it, and the code that turns the raw public data into each number is [on GitHub](https://github.com/jawdat-rana/unexpected-signals). If you find a mistake, [open an issue](https://github.com/jawdat-rana/unexpected-signals/issues). I'll fix it and say what changed at the top of the story.
