# cvtools

Scripts to get stats and validate data from Mozilla's [Common Voice](https://voice.mozilla.org) project. All scripts require Python 3.

## sentence_validator

Python script to filter out invalid sentences.

### Usage

~~~~
sentence_validator.py -i <input_file> [--profanity-list <file>] [--output-success <output_file>] [--output-fail <output_file>]
~~~~

`-i` - a text file with a sentence on each line.

`--profanity-list` - (optional) a text file with a word on each line. Specifying this option filters sentences containing words found in the text file.

`--output-success` - (optional) specifies the file to write successfully validated sentences to.

`--output-fail` - (optional) specifies the file to write failed sentences to.

### Output

The script outputs a list of failed sentences, including the reason why they failed validation.

If output files were specified, the script will write successful sentences to one file and failed sentences to another.

**Sample output**

~~~~Validation failed (length): Ver Tanzt?
Validation failed (partial sentence): is the debut album of Black Ox Orkestar, a Montreal-based band.
Validation failed (length): The group performed music, produced artwork, films, videos, live theatre, multi-media, and wrote literature.
Validation failed (invalid chars): → ↑ → and Asphixiation appear on both of Chapter Music's "Can't Stop It!
Validation failed (length): Norris.
Validation failed (length): When done properly, flame plastic polishing produces the clearest finish, especially when polishing acrylic.
Validation failed (length): is gone.
Validation failed (partial sentence): cuts off all contact with her.
Validation failed (length): Yipe!
...
~~~~

### Where to get data

Sentences are located in the [server/data folder](https://github.com/mozilla/voice-web/tree/master/server/data) of [mozilla/voice-web](https://github.com/mozilla/voice-web).

A text file of profanity can be found at [dabinat/profanity](https://github.com/dabinat/profanity).

## word_usage

Python script to get word usage stats from Mozilla's Common Voice [Sentence Collector](https://common-voice.github.io/sentence-collector/#/).

### Usage

~~~~
word_usage.py -i <input_file> [-d <dictionary_file>] [--limit x] [--min-frequency x] [--max-frequency x] [--show-words-only]
~~~~

`-i` - a text file with a sentence on each line.

`-d` - a text file with a word on each line (optional).

`--limit` - returns only the *x* most popular words.

`--min-frequency` - returns only words that have at least *x* matches. (This causes the dictionary argument to be ignored because all missing dictionary words would have a frequency of 0.)

`--max-frequency` - returns only words with up to *x* matches.

`--show-words-only` - outputs the word without the number of matches. Useful for piping a word list to a separate file.

### Output

A list of words and how many times they appear in the input file, sorted from most to least frequent.

If you specified a dictionary, it will also list words in the dictionary that do not appear in sentences.

**Sample output**

~~~~
the 1393
a 706
to 551
of 483
and 446
is 416
was 387
in 365
i 341
he 302
you 258
it 240
his 195
for 184
that 176
are 164
my 160
this 155
on 150
...
~~~~

### Where to get data

Sentences are located in the [server/data folder](https://github.com/mozilla/voice-web/tree/master/server/data) of [mozilla/voice-web](https://github.com/mozilla/voice-web).

You can get a text file full of English words from [dwyl/english-words](https://github.com/dwyl/english-words). 

[Direct link to Sentence Collector text file for English](https://raw.githubusercontent.com/mozilla/voice-web/master/server/data/en/sentence-collector.txt)

[Direct link to English word dictionary](https://raw.githubusercontent.com/dwyl/english-words/master/words.txt)
