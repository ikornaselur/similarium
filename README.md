# Similarium
A Slack bot to play Similarium together as a team on a Slack channel.

Similarium is based on [Semantle](https://semantle.com/)

## Development

### Requirements

* `poetry` for dependency management
* `GoogleNews-vectors-negative300.bin.gz` from [here](https://code.google.com/archive/p/word2vec/). Extract it to the root of the repo

`numpy` and `gensim` are extra dependencies only required to initialise the
database with the wordlists. To install install them you need to run `poetry
install -E dump` for the scripts to work. 

If you already have a database that has been populated, these dependencies are
not required

### Config

Copy `config.example.toml` to `config.toml` and replae the secrets with
relevant values

### Data processing

The project expects an english word list and a banned word list to work with.

1. `make wordlists`: Download the default wordlists
2. `make init_db`: Ensure the database is initialised with relevant
   tables
3. `make prepare_data`: Store main vectors + hints in database

you can also run `make all` to run the two steps above in a row

The whole process should take just 5-10 minutes to run.

### Testing

The tests have access to a pre-populated sqlite database with a handful of
words. To populate the database, three secret words were picked:

  * apple
  * excited
  * future

For each secret, few neighboring words were picked, based on their percentile:

  * 990 - 999
  * 500
  * 100
  * 10
  * 1

The following words are in the test database:

  anticipation, anyone, apple, apples, berry, blueberry, caramel, cherries,
  circumstanced, continue, current, delighted, ecstatic, effused, elated,
  enthused, excited, exciting, forewarning, forthcoming, fruit, future, grape,
  happy, kind, marveled, next, nutshells, peach, pear, pears, pleased, potato,
  potential, prospects, proud, psyched, seedpods, someday, strawberry,
  thrilled, uncertain, upcoming, vagaries, varieties, viability,

"cherries" is a special word which has a Word2Vec entry, but no Nearby entry.
It has a 989 percentile normally to "apple", but was added this way to be
easily able to test similar words that end up not being found in the
pre-populated "nearby" words. This would be a '???' word in the original game.


## Deployment

You need to create a new Slack App. The app needs the following features and
functionality:

* Slash commands
  - `/similarium` command to manage games in the Slack team
* Bots
* Permissions
  - Bot Token Scopes:
    - `chat:write`
    - `commands`
    - `users:read`
  - `connections:write` Only if running in Socket mode
* Interactive Components
  - Required only when running in callback mode, can be ignored for Socket mode

## Attributions
Based heavily on the original GNU GPLv3 licensed Semantle source code by [David
Turner](https://novalis.org/).
