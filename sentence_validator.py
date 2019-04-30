#!/usr/bin/python

import sys, getopt, re

input_file = ''
profanity_file = ''
profanity_list = []
output_success_file = ''
output_fail_file = ''

# Define custom exception
class ValidationFailure(Exception):
   pass
   
   
def runScript():
	global input_file,output_success_file,output_fail_file,profanity_file

	try:
		opts, args = getopt.getopt(sys.argv[1:],"i:p:o:of:",["input=","profanity-list=","output-success=","output-fail="])
	except getopt.GetoptError:
		print('sentence_validator.py -i <input file> [--profanity-list <file>] [--output-success <output file>] [-output-fail <output file>]')
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			print('sentence_validator.py -i <input file> [--profanity-list <file>] [--output-success <output file>] [-output-fail <output file>]')
			sys.exit()
		elif opt in ("-i", "--input"):
			input_file = arg
		elif opt in ("-p", "--profanity-list"):
			profanity_file = arg
		elif opt in ("-o", "--output-success"):
			output_success_file = arg
		elif opt in ("-of", "--output-fail"):
			output_fail_file = arg

	# Cache profanity
	if profanity_file:
		with open(profanity_file) as pf:  
			for line in pf:
				profanity_list.append(line.strip())

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
				line = line.replace(u"\u05BE","-")
				line = line.replace(u"\u2010","-")
				line = line.replace(u"\u2011","-")
				line = line.replace(u"\u2012","-")
				line = line.replace(u"\u2013","-")
				line = line.replace(u"\u2014","-")
				line = line.replace(u"\u2015","-")
				
				words = line.split()
				word_count = len(words)
				char_count = len(line)
			
				# Check for obviously truncated sentences
				last_word = words[-1].lower()
				sub_words = last_word.split("-")
				last_word = re.sub(r'[^[a-zA-Z.]','', sub_words[-1])
				
				if last_word == "e.g." or last_word == "i.e." or last_word == "a.k.a" or last_word == "no."\
				or last_word == "al." or last_word == "op.":
					raise ValidationFailure("partial sentence")
				# Check if too short or too long
				if char_count < 5 or char_count > 115 or word_count < 3 or word_count > 14:
					raise ValidationFailure("length")
					
				# Check if words are reasonable length
				for w in words:
					if len(w) > 16:
						sub_words = w.split("-")
						
						for sw in sub_words:
							if len(sw) > 16:
								raise ValidationFailure("word length")
		
				# Check for non-English chars
				if re.search(r"[^a-zA-Z'\-,.!?:;() \"]", line) is not None:
					raise ValidationFailure("invalid chars")

				# Check if it starts with a capital letter
				first_char = line[0];
				if first_char != first_char.upper():
					raise ValidationFailure("partial sentence")

				if first_char == "'" or first_char == "\"":
					second_char = line[1];
					if second_char != second_char.upper():
						raise ValidationFailure("partial sentence")
						
				# Check if it starts with an obviously wrong character
				if first_char == "," or first_char == "." or first_char == ";" or first_char == ":"\
				or first_char == "-" or first_char == "' ":
					raise ValidationFailure("partial sentence")
					
				# Check if it ends with valid punctuation
				last_char = line[-1];
				if not (last_char == "." or last_char == "!" or last_char == "?" or last_char == "'" or last_char == '"'):
					raise ValidationFailure("punctuation")
					
				# Look for missing words
				for w in words:
					if w == "\"\"" or w == "\"\"." or w == "\"\"," or w == "\"\";" or w == "\"\":" or w == "\"\"!"\
					or w == "\"\"?" or w == "'s":
						raise ValidationFailure("missing word")
						
				if line.count(" over of ") > 0 or line.count(" on of ") > 0 or line.count(" with of ") > 0:
						raise ValidationFailure("missing word")
					
				# Check for possible foreign terms (e.g. Persona y Sociedad)
				if containsForeignTerm(words):
						raise ValidationFailure("foreign term")
					
				# Check for profanity
				if containsProfanity(words):
					raise ValidationFailure("profanity")
					
				# Prevent long lists
				if line.count(",") > 4:
					raise ValidationFailure("long list")

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
		elif w == "Bros" or w == "Bros.":
			out_word = "Brothers"
		elif w == "i.e." or w == "i.e":
			out_word = "that is"
		elif w == "e.g." or w == "e.g":
			out_word = "for example"
		elif w == "etc" or w == "etc.":
			out_word = "et cetera"

		out_words.append(out_word)
		
	return " ".join(out_words)
	
def containsForeignTerm(words):
	for w in words:
		sub_words = w.split("-")
		for sw in sub_words:
			sw_unstripped = sw
			sw = re.sub(r'[^[a-zA-Z]','', sw)
			
			if sw_unstripped == "i" or sw_unstripped == "y" or sw.lower() == "el" or sw.lower() == "le" or sw.lower() == "ng" or sw == "les" \
			or w == "de" or w == "un" or sw == "del" or sw == "og" or sw.lower() == "la" or sw == "ap" or sw == "ibn" \
			or sw == "al" or sw == "das" or sw == "et" or sw == "fu" or sw == "ga" or sw == "sur" or sw == "du" \
			or sw == "aj" or sw == "ud" or sw.lower() == "ix" or sw.lower() == "ich" or sw.lower() == "zur" \
			or sw == "und" or sw == "una" or sw == "jou" or sw.lower() == "que" or sw == "qui" or sw == "est" or sw.lower() == "te" \
			or sw.lower() == "tu" or sw.lower() == "il" or sw.lower() == "avec" or sw.lower() == "vous" or sw.lower() == "yr" \
			or sw == "ar" or sw == "al" or sw == "il" or sw.lower() == "sa" or sw.lower().count("fj") > 0 \
			or sw.lower().count("rrr") > 0:
				return True
			
			if len(sw_unstripped) > 2:
				prefix = sw[:2] if len(sw) > 2 else ""
				prefix_unstripped = sw_unstripped[:2]
				suffix = sw[-2] if len(sw) > 2 else ""
				suffix_unstripped = sw_unstripped[-2]

				if prefix_unstripped.lower() == "l'" or prefix_unstripped.lower() == "d'" or prefix_unstripped.lower() == "q'" \
				or prefix_unstripped.lower() == "j'" or prefix_unstripped.lower() == "k'" or prefix_unstripped.lower() == "b'" \
				or prefix_unstripped.lower() == "z'" or prefix_unstripped.lower() == "s'" \
				or prefix == "Hr" or prefix.lower() == "tl" or prefix == "Rj" or prefix == "Ng" or prefix == "Nj" or prefix == "Hl" \
				or prefix == "Tx" or prefix.lower() == "cv" or prefix == "Tk" or prefix == "Zh" or prefix == "Kt" \
				or prefix.lower() == "lj" or prefix == "Kj" or prefix == "Bj" or prefix == "Hj" or prefix == "Dn" \
				or prefix == "Qe" or prefix.lower() == "sv" or prefix.lower() == "sz" or prefix.lower() == "tz" \
				or prefix.lower() == "dz" or prefix == "Rz" or prefix.lower() == "bz" or prefix.lower() == "Nz" \
				or prefix == "Mz" or prefix == "Ys" or suffix_unstripped == "'u" or suffix_unstripped == "'e" \
				or suffix_unstripped == "'a" or suffix_unstripped == "'i" or suffix_unstripped == "'o" \
				or suffix_unstripped == "'h" or suffix_unstripped == "'r":
					return True
			
	return False
	
def containsProfanity(words):	
	for w in words:
		sub_words = w.split("-")
		for sw in sub_words:
			sw = re.sub(r'[^[a-zA-Z]','', sw)
			if profanity_list.count(sw.lower()) > 0:
				return True
			
	return False
	
runScript()

