# Semantle Slack Bot
A Slack bot to play [Semantle](https://semantle.novalis.org/) together as a
team on a Slack channel.

## Development

### Requirements

* `poetry` for dependency management
* `GoogleNews-vectors-negative300.bin.gz` from [here](https://code.google.com/archive/p/word2vec/). Extract it to the root of the repo

### Data processing

The project expects an english word list and a banned word list to work with.

1. `make wordlist`: Download the default wordlists
2. `make dump_vecs`: Create an SQLite database and store main vectors
3. `make dump_hints`: Store hints in the database

you can also run `make all` to run the three steps above in a row


## Attributions
Based heavily on the
[novalis_dt/semantle](https://gitlab.com/novalis_dt/semantle) source code by
David Turner.
