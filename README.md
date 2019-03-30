# cvstats

Python script to get word usage stats from Mozilla's Common Voice [Sentence Collector](https://common-voice.github.io/sentence-collector/#/).

## Usage

**cvstats.py -i input_file [-d dictionary_file]**

Input file is a text file with a sentence on each line.

Dictionary file is optional and is a text file with a word on each line.

## Output

A list of words and how many times they appear in the input file, sorted from most to least frequent.

If you specified a dictionary, it will also list words in the dictionary that do not appear in sentences.

**Sample output**

~~~~the 1393
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

## Where to get data

Sentences are located in the [sever/data folder](https://github.com/mozilla/voice-web/tree/master/server/data) of [mozilla/voice-web](https://github.com/mozilla/voice-web).

You can get a text file full of English words from [dwyl/english-words](https://github.com/dwyl/english-words). 

[Direct link to Sentence Collector text file for English](https://raw.githubusercontent.com/mozilla/voice-web/master/server/data/en/sentence-collector.txt)

[Direct link to English word dictionary](https://raw.githubusercontent.com/dwyl/english-words/master/words.txt)
