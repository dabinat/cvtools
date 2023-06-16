#!/usr/bin/python3

import sys, getopt, re, os
from collections import defaultdict

input_file = ''
dictionary_file = ''
limit = 0
min_frequency = 0
max_frequency = 0
min_length = 0
max_length = 0
words_only = False
no_repeats = False
strip_apostrophes = False
non_dictionary_only = False


def replace_apostrophes(line):
    # Convert curly apostrophes to straight
    line = line.replace(u"\u2018", "'")
    line = line.replace(u"\u2019", "'")
    line = line.replace(u"\u0060", "'")
    line = line.replace(u"\u00b4", "'")


def clean(line):    
    # Filter out symbols
    line = re.sub("[^a-zA-Z\u00c0-\u024f\u0370-\u1fff\u3040-\ufeff']", " ", line)

    # Remove any double spaces introduced by last regex
    line = re.sub("\ {2,}", " ", line)

    line = line.lower()

    return line


def clean_and_split(line, strip_apostrophes=False):

    replace_apostrophes(line)

    if strip_apostrophes:
        # Remove apostrophes to split words
        line = line.replace("'", " ")
        line = line.replace('"', "")

    line = clean(line)

    return line.split()


def printhelp():
    print('word_usage.py -i <input file> [-d <dictionary>] [--limit x] [--min-frequency x] [--max-frequency x] [--min-length x] [--max-length x] [--show-words-only] [--non-dictionary-words] [--strip-apostrophes] [--no-repeats]')


try:
    opts, args = getopt.getopt(sys.argv[1:],"i:d:",["input=","dictionary=","limit=","min-frequency=","max-frequency=","min-length=","max-length=","show-words-only","strip-apostrophes","no-repeats","non-dictionary-words"])
except getopt.GetoptError:
    printhelp()
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        printhelp()
        sys.exit()
    elif opt in ("-i", "--input"):
        input_file = arg
    elif opt in ("-d", "--dictionary"):
        dictionary_file = arg
    elif opt == "--limit":
        limit = int(arg)
    elif opt == "--min-frequency":
        min_frequency = int(arg)
    elif opt == "--max-frequency":
        max_frequency = int(arg)
    elif opt == "--min-length":
        min_length = int(arg)
    elif opt == "--max-length":
        max_length = int(arg)
    elif opt == "--strip-apostrophes":
        strip_apostrophes = True
    elif opt == "--show-words-only":
        words_only = True
    elif opt == "--no-repeats":
        no_repeats = True
    elif opt == "--non-dictionary-words":
        non_dictionary_only = True

word_dict = defaultdict(int)

if not os.path.exists(input_file):
    printhelp()
    sys.exit(2)

dictionary = set()

# Scan dictionary if the user specified it (assumes one word per line)
if dictionary_file:
    with open(dictionary_file, encoding='utf-8') as f:
        for line in f:
            line = clean(line).strip()
            if len(line) > 0:
                dictionary.add(line)

# Scan sentences
with open(input_file, encoding='utf-8') as f:
    for line in f:
        words = clean_and_split(line, strip_apostrophes)
        repeat_list = []

        for w in words:
            # Ignore apostrophes at start or end
            if len(w) > 1 and w[:1] == "'":
                w = w[1:]
            if len(w) > 1 and w[-1] == "'":
                w = w[:-1]

            w_len = len(w)

            if w_len > 0 and w != "'":
                if w_len < min_length or (max_length > 0 and w_len > max_length):
                    continue

                if no_repeats:
                    if w in repeat_list:
                        continue

                    repeat_list.append(w)

                val = word_dict[w]
                val += 1
                word_dict[w] = val

if min_frequency == 0 and not non_dictionary_only and dictionary_file:
    # Add dictionary words if they don't exist
    for word in dictionary:
        val = word_dict[word]
        word_dict[word] = val

# Filter by min/max frequency
filtered_words = defaultdict(int)

for word in word_dict:
    if (min_frequency == 0 or int(word_dict[word]) >= min_frequency) and \
    (max_frequency == 0 or int(word_dict[word]) <= max_frequency):

        # Check if it's in the dictionary
        if non_dictionary_only and word in dictionary:
            continue

        filtered_words[word] = word_dict[word]

# Now sort by alphabetical order of word
sorted_words = sorted(filtered_words.items(), key=lambda x: x[0])

# Sort words by most to least frequent
sorted_words = sorted(sorted_words, key=lambda x: x[1], reverse=True)

# Set limit if specified
if limit > 0 and len(sorted_words) > limit:
    sorted_words = sorted_words[:limit]

for word, num in sorted_words:
    if words_only:
        print(word)
    else:
        print("{} {}".format(word, num))
