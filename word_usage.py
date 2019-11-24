#!/usr/bin/python

import sys, getopt, re, os
from collections import defaultdict

input_file = ''
dictionary_file = ''
limit = 0
min_frequency = 0
max_frequency = 0
words_only = False
no_repeats = False
split_by_apostrophe = False


def clean(line, split=False):
    # Remove apostrophes to split words cutted
    line = line.replace("'", " ")

    # Convert curly apostrophes to straight
    line = line.replace(u"\u2018", "'")
    line = line.replace(u"\u2019", "'")
    line = line.replace(u"\u0060", "'")
    line = line.replace(u"\u00b4", "'")

    # Filter out symbols
    line = re.sub("[^a-zA-Z\u00c0-\u024f\u1e00-\u1eff']", " ", line)

    # Remove any double spaces introduced by last regex
    line = re.sub("\ {2,}", " ", line)

    line = line.lower()

    if split:
        return line.split()

    return line


def printhelp():
    print('word_usage.py -i <input file> [-d <dictionary>] [--limit x] [--min-frequency x] [--max-frequency x] [--show-words-only] [--strip-by-apostrophe] [--no-repeats]')


try:
    opts, args = getopt.getopt(sys.argv[1:],"i:d",["input=","dictionary=","limit=","min-frequency=","max-frequency=","show-words-only","strip-by-apostrophe","no-repeats"])
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
    elif opt == "--strip-by-apostrophe":
        split_by_apostrophe = True
    elif opt == "--show-words-only":
        words_only = True
    elif opt == "--no-repeats":
        no_repeats = True

word_dict = defaultdict(int)

if not os.path.exists(input_file):
    printhelp()
    sys.exit(2)    

# Scan sentences
with open(input_file) as f:
    for line in f:
        words = clean(line, split_by_apostrophe)
        repeat_list = []

        for w in words:
            # Ignore apostrophes at start or end
            if len(w) > 1 and w[:1] == "'":
                w = w[1:]    
            if len(w) > 1 and w[-1] == "'":
                w = w[:-1]
        
            if len(w) > 0 and w != "'":
                if no_repeats:
                    if w in repeat_list:
                        continue
                        
                    repeat_list.append(w)
                    
                val = word_dict[w]
                val += 1
                word_dict[w] = val

# Scan dictionary if the user specified it (assumes one word per line)
if min_frequency == 0 and dictionary_file:
    with open(dictionary_file) as f:
        for line in f:
            line = clean(line)
            if len(line) > 0:
                # Add word if it doesn't exist
                val = word_dict[line]
                word_dict[line] = val

# Filter by min/max frequency
filtered_words = defaultdict(int)

for word in word_dict:
    if (min_frequency == 0 or int(word_dict[word]) >= min_frequency) and \
    (max_frequency == 0 or int(word_dict[word]) <= max_frequency):
        filtered_words[word] = word_dict[word]

# Now sort by alphabetical order of word
sorted_words = sorted(filtered_words.items(), key=lambda x:x[0]);

# Sort words by most to least frequent
sorted_words = sorted(sorted_words, key=lambda x:x[1], reverse=True);

# Set limit if specified
if limit > 0 and len(sorted_words) > limit:
    sorted_words = sorted_words[:limit]

for word,num in sorted_words:
    if words_only:
        print(word)
    else:
        print("{} {}".format(word,num))
