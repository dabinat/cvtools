#!/usr/bin/python

import sys, getopt, re
from collections import defaultdict

input_file = ''
output_success_file = ''
output_fail_file = ''

# Define custom exception
class ValidationFailure(Exception):
   pass
   
   
def runScript():
	global input_file,output_success_file,output_fail_file

	try:
		opts, args = getopt.getopt(sys.argv[1:],"i:o:of:",["input=","output-success=","output-fail="])
	except getopt.GetoptError:
		print('sentence_validator.py -i <input file> [--output-success <output file>] [-output-fail <output file>]')
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			print('sentence_validator.py -i <input file> [--output-success <output file>] [-output-fail <output file>]')
			sys.exit()
		elif opt in ("-i", "--input"):
			input_file = arg
		elif opt in ("-o", "--output-success"):
			output_success_file = arg
		elif opt in ("-of", "--output-fail"):
			output_fail_file = arg

	# Open files for writing
	if output_success_file:
		f_success = open(output_success_file, "w")

	if output_fail_file:
		f_fail = open(output_fail_file, "w")

	# Scan sentences
	with open(input_file) as f:  
		for line in f:		
			try:
				# Replace abbreviated words
				line = expandAbbreviations(line)
			
				# Replace stylized symbols
				line = line.replace(u"\u2018","'")
				line = line.replace(u"\u2019","'")
				line = line.replace(u"\u0060","'")
				line = line.replace(u"\u00B4","'")
				line = line.replace(u"\u201C","\"")
				line = line.replace(u"\u201D","\"")
			
				words = line.split()
				word_count = len(words)
				char_count = len(line)
			
				# Check if too short or too long
				if char_count < 5 or char_count > 100 or word_count < 3 or word_count > 14:
					raise ValidationFailure("length")
					
				# Check if words are reasonable length
				for w in words:
					if len(w) > 15:
						raise ValidationFailure("word length")
		
				# Check for non-English chars
				if re.match(r"[^a-zA-Z'\-,.() \"]", line) is not None:
					raise ValidationFailure("invalid chars")

				# Check if it starts with a capital letter
				first_char = line[0];
				if first_char != first_char.upper():
					raise ValidationFailure("partial sentence")
					
				# Check if it ends with valid punctuation
				last_char = line[-1];
				if not (last_char == "." or last_char == "!" or last_char == "?" or last_char == "'" or last_char == '"'):
					raise ValidationFailure("punctuation")
					
				# Validation successful
				if output_success_file:
					f_success.write(line + "\n")
					
			except ValidationFailure as vf:
					print("Validation failed ({}): {}".format(vf,line))

					if output_fail_file:
						f_fail.write(line + "\n")

	# Close files
	if output_success_file:
		f_success.close()

	if output_fail_file:
		f_fail.close()


def expandAbbreviations(line):
	source_words = line.split()	
	out_words = [];
	
	for w in source_words:
		out_word = w
		
		if w == "&":
			out_word = "and"
		elif w.count("&") > 0:
			out_word = w.replace("&"," and ")
		elif w == "Jr" or w == "Jr.":
			out_word = "Junior"
		elif w == "Sr" or w == "Sr.":
			out_word = "Senior"
		elif w == "No.":
			out_word = "Number"
		elif w == "no.":
			out_word = "number"
		elif w == "Mt" or w == "Mt.":
			out_word = "Mount"
		elif w == "i.e." or w == "i.e":
			out_word = "that is"
		elif w == "e.g." or w == "e.g":
			out_word = "for example"
		elif w == "etc" or w == "etc.":
			out_word = "et cetera"

		out_words.append(out_word)
		
	return " ".join(out_words)
	
	
runScript()

