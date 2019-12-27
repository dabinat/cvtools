#!/usr/bin/python

import sys, getopt, re

input_file = ''
filter_file = ''
filter_list = []
output_success_file = ''
output_fail_file = ''
approved_sentences = set()

# Define custom exception
class ValidationFailure(Exception):
   pass

# Compile regexes for speed
regex_split_punctuation = re.compile(r'-|\.{3}')
regex_non_letters = re.compile(r'[^[a-zA-Z]')
regex_non_english_chars = re.compile(r"[^a-zA-Z'\-,.!?:;() \"]")
regex_unusual_apostrophes = re.compile(r"[^s^O^n^d^y^a^-^\"^\s]'[^t^s^r^m^l^v^d^a^e^n^c^\s^,^\.^\?^\!^\:^\;^\"^-]")
regex_end_in_comma_and_letter = re.compile(r"[,][\ ][A-Z][\.]$")
   
   
def runScript():
    global input_file, output_success_file, output_fail_file, filter_file
    global regex_unusual_apostrophes, regex_non_letters, regex_split_punctuation, regex_non_english_chars, regex_end_in_comma_and_letter

    try:
        opts, args = getopt.getopt(sys.argv[1:],"i:p:o:of:",["input=", "filter-list=","output-success=","output-fail="])
    except getopt.GetoptError:
        print('sentence_validator.py -i <input file> [--filter-list <file>] [--output-success <output file>] [-output-fail <output file>]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('sentence_validator.py -i <input file> [--filter-list <file>] [--output-success <output file>] [-output-fail <output file>]')
            sys.exit()
        elif opt in ("-i", "--input"):
            input_file = arg
        elif opt in ("-f","--filter-list"):
            filter_file = arg
        elif opt in ("-o", "--output-success"):
            output_success_file = arg
        elif opt in ("-of", "--output-fail"):
            output_fail_file = arg

    # Cache word filters
    if filter_file:
        with open(filter_file) as fl:  
            for line in fl:
                filter_list.append(line.strip())

    # Open files for writing
    if output_success_file:
        f_success = open(output_success_file, "w")

    if output_fail_file:
        f_fail = open(output_fail_file, "w")

    # Scan sentences
    with open(input_file) as f:  
        for line in f:
            try:
                line = line.strip()
                
                # Tidy up sentence endings
                if line.endswith("!.") or line.endswith("?.") or line.endswith(",."):
                    line = line[:-1]
                line = re.sub(r"[^\.]\.{2}$", ".", line)
                            
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
                
                # Clean up quotes
                if line.count("\"") == 1:
                    line = line.replace("\"","")
                line = line.replace("\"\"","\"")
                line = line.replace("''","'")
                line = line.replace("''","\"")

                # Replace abbreviated words
                line = expandAbbreviations(line)

                # Fix punctuation spacing
                line = re.sub(r',(?=\w)', ', ', line)
#               line = re.sub(r'(?<=[^\.])\.(?=\S[^\"\.])', '. ', line)

                words = line.split()
                word_count = len(words)
                char_count = len(line)
            
                # Check for obviously truncated sentences
                last_word = words[-1].lower()
                sub_words = regex_split_punctuation.split(last_word) # Split on - or ...
                last_word = re.sub(r'[^[a-zA-Z.]','', sub_words[-1])
                
                if last_word == "." or last_word == "," or last_word == "e.g." or last_word == "i.e." \
                or last_word == "a.k.a" or last_word == "no." or last_word == "al." or last_word == "op." \
                or last_word == "mr." or last_word == "mrs." or last_word == "Dr." or last_word == "and" \
                or last_word == "including" or last_word == "a.o." or last_word == "xx." or words[-1] == "an.":
                    raise ValidationFailure("partial sentence")

                # Look for punctuation indicative of truncation
                if " -," in line or ":." in line or " ' " in line or " \" " in line:
                    raise ValidationFailure("partial sentence")

                # Check for single letters at end
                if regex_end_in_comma_and_letter.search(line) is not None:
                    raise ValidationFailure("partial sentence")
                
                # Check if too short or too long
                if char_count < 5 or char_count > 125 or word_count < 3 or word_count > 14:
                    raise ValidationFailure("length")
                    
                # Check if words are reasonable length
                for w in words:
                    sub_words = regex_split_punctuation.split(w) # Split on - or ...
                    
                    for sw in sub_words:
                        sw = regex_non_letters.sub('', sw)

                        if lengthCheck(sw):
                            raise ValidationFailure("word length")
        
                # Check for non-English chars
                if regex_non_english_chars.search(line) is not None:
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
                if first_char == "," or first_char == "." or first_char == ";" or first_char == ":" or first_char == "-" or first_char == "';" \
                or first_char == "'\"" or first_char == "\",":
                    raise ValidationFailure("partial sentence")

                if len(line) > 2 and (line[:2] == ("' ") or line[:2] == ("\" ") or line[:2] == ("',")):
                    raise ValidationFailure("partial sentence")
                    
                # Check if it ends with valid punctuation
                last_char = line[-1];
                if not (last_char == "." or last_char == "!" or last_char == "?" or last_char == "'" or last_char == '"'):
                    raise ValidationFailure("punctuation")
                    
                # Look for too many apostrophes
                for word in words:
                    # Remove surrounding quotes
                    if word.startswith("'"):
                        word = word[1:]
                    
                    if word.endswith("'"):
                        word = word[0:-1]

                    if word.endswith("'s") or word.endswith("'t"):
                        word = word[0:-2]

                    if word.endswith("'ve"):
                        word = word[0:-3]
                    
                    if word.lower().count("'") > 2 and word.lower().count("'n'") == 0:
                        raise ValidationFailure("too many apostrophes")

                # Look for missing words
                if containsMissingWords(line):
                        raise ValidationFailure("missing word")
                    
                # Check for possible foreign terms (e.g. Persona y Sociedad)
                if containsForeignTerm(words):
                        raise ValidationFailure("foreign term")
                    
                # Check for non-standard apostrophe use
                if not regex_unusual_apostrophes.search(line) == None:
                        raise ValidationFailure("foreign term")
                    
                # Check for filtered words
                filtered_word = containsFilteredWord(words)
                if not filtered_word == None:
                    raise ValidationFailure("filtered word - " + filtered_word)
                    
                # Prevent long lists
                if line.count(",") > 4:
                    raise ValidationFailure("long list")
                    
                # Check for dupes
                cleaned_line = line.lower()
                cleaned_line = regex_non_letters.sub("", line)

                if cleaned_line in approved_sentences:
                    raise ValidationFailure("duplicate sentence")

                # Validation successful
                approved_sentences.add(cleaned_line)
                
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
    # Find and replace common terms
    line = line.replace(".com"," dot com")
    line = line.replace(".net"," dot net")
    line = line.replace(".org"," dot org")
    line = line.replace(".ie"," dot ie")
    line = line.replace(".co"," dot co")
    line = line.replace(".ac"," dot ac")
    line = line.replace(".uk"," dot uk")
    line = line.replace(".ca"," dot ca")
    line = line.replace(".fm"," dot fm")
    line = line.replace(".gov"," dot gov")
    line = line.replace(".io"," dot io")
    line = line.replace(".tv"," dot tv")
    line = line.replace("www.","www dot ")

    # Roman numerals
    prefixes = ["War","Grade","grade","Type","type","Category","category","Model","Schedule","Class","Sermon","Section","Group","group","District",\
                            "Part","part","Title","title","Phase","phase","prophase","Level","level","Ultima","Saturn","Palm","Bowl","Book","book","Corridor","Region", \
                            "Annex","Atlas","Ares","Mark","Zone","Division","Icarus","Falcon","WrestleMania","Article","Legio","Merlin","Metro","Chapter","Apple","Luft", \
                            "Panzer","Tysons","Turbo","Genesis","form","Form","Act","Budapest","FreeDonia","Dalek","Star","Berdan","Bratislava","Discoverer","Offset", \
                            "Municipio","Liga","Cullinan","Technology","Company","Civilization","Volume","Sparrow","Appendix"]
    numerals = [{"from":"I","to":"One"},{"from":"II","to":"Two"},{"from":"III","to":"Three"},{"from":"IV","to":"Four"},{"from":"V","to":"Five"}]

    for i in numerals:
        for prefix in prefixes:
            to_text = i["to"]
            # Match case
            if prefix.lower() == prefix:
                to_text = to_text.lower()
            
            line = line.replace(prefix + " " + i["from"] + " ",prefix + " " + to_text + " ")

    # Monarchs
    prefixes = ["Charles","James","John","Mary","Elizabeth","Henry","Edward","Albert","Louis","Mehmed","Napoleon","Murad","Danilo","Ahmose","Leo", \
                            "Bayezid","Valentinian","Nepherites","Volkaert","Pedro","Frederick","Ptolemy","Baldwin","William","Paul","Nicholas","Celestine", \
                            "George","Ferdinand","Ivid","Harald","Baldwin","Antiochus","Gustaf","Christian","Martin","Abgar","Philip","Ladislaus","Mohammed", \
                            "Muhammed","Jan","Floris","Walter","Afonso","Hugh","Mithridates","Dirk","Peter","Mohamed","Ramesses","Paerisades","Regio","Leopold", \
                            "Amenemhat","Harrison","Frederik","Bagrat","Bahram","Alfonso","Pelagius","Paschal","Otto","Victor","Ramiro","David","Francis","Alberic", \
                            "Demetrius","Tukulti-Ninurta","Ermengol","Mahmud","Yazdegerd","Ranavalona","Radama","Alexander","Alfred","Leka","Ladislaus","Simeon","Asen",\
                            "Darius","Cleombrotus","Sargon","Abbas","Harshavarman","Moctezuma","Prijezda","Willford","Chandragupta","Mestwin","Eupolypods","Robert", \
                            "Nahb","Augustus","Celebrezze","Kamehameha","Antimachus","Apollodotus","Psamtik","Dmitry","Selassie","Osroes","Johann", \
                            "Thutmose","Pepi","Al-Hakam","Dagobert","Murad","Selim","Constantine","Chola","Sigebert","Charibert","Fasciculus","Rasmussen","Rama", \
                            "Theodosius","Mentuhotep","Neferu","Eudamidas","Cosimo","Vonones","Demetre","Radama","Compton","Thomas","Schneider","Shoshenq","Seyon", \
                            "Yeshaq","Ruben","Acrotatus","Selene","Badi","Roosevelt","Jifar","Argishti","Mueenuddeen","Ernest","Mansur","Stateira","Justinian", \
                            "Kamehameha","Xerxes","Bernhard","Psusennes","Ariamnes","Nuh","Gould","ad-Din","Maximilian","Nebuchadnezzar","Jerome","Bogdan","Aripert", \
                            "Carlos","Amoghavarsha","Rudolf","Pedro","Faustin","Seti","Sanpei","Seleucus","Felix","Lothair","Basil","Carol","Michael","Philippe", \
                            "Teimuraz","Georg"] 

    numerals = [{"from":"I","to":"the First"},{"from":"II","to":"the Second"},{"from":"III","to":"the Third"},{"from":"IV","to":"the Fourth"},{"from":"V","to":"the Fifth"},\
                        {"from":"VI","to":"the Sixth"},{"from":"VII","to":"the Seventh"},{"from":"VIII","to":"the Eighth"},{"from":"IX","to":"the Ninth"},{"from":"X","to":"the Tenth"}]

    for prefix in prefixes:
        # This is expensive so only do the regex if there's a match
        if prefix + " " in line:            
            for i in numerals:
                # Match for "Charles I" but not "Charles I. Smith"
                line = re.sub(prefix + "\ " + i["from"] + "(?=[\.]$|\ |,|:|;|\!|'|\")", prefix + " " + i["to"], line)

    source_words = line.split() 
    out_words = [];
    
    for w in source_words:
        start_punctuation = ""
        end_punctuation = ""

        if w[0] == "\"" or w[0] == "'":
            start_punctuation = w[0]
            w = w[1:]
        
        if len(w) > 2 and (w[-2] == "'s"):
            end_punctuation = w[-2]
            w = w[:-2]

        if len(w) > 0 and (w[-1] == "," or w[-1] == "!" or w[-1] == "\"" or w[-1] == "'"):
            end_punctuation = w[-1] + end_punctuation
            w = w[:-1]

        out_word = w
        
        if w == "&":
            out_word = "and"
        elif w.count("&") > 0:
            out_word = w.replace("&"," and ")
        elif w == "Jr" or w == "Jr." or w == "Jnr":
            out_word = "Junior"
        elif w == "Sr" or w == "Sr." or w == "Snr":
            out_word = "Senior"
        elif w == "No." or w == "Nr.":
            out_word = "Number"
        elif w == "Nos.":
            out_word = "Numbers"
        elif w == "nos.":
            out_word = "numbers"
        elif w == "no.":
            out_word = "number"
        elif w == "Mt" or w == "Mt.":
            out_word = "Mount"
        elif w == "Mts.":
            out_word = "Mounts"
        elif w == "Bros" or w == "Bros.":
            out_word = "Brothers"
        elif w == "Capt" or w == "Capt.":
            out_word = "Captain"
        elif w == "Col" or w == "Col.":
            out_word = "Colonel"
        elif w == "Lt" or w == "Lt." or w == "Lieut.":
            out_word = "Lieutenant"
        elif w == "Sgt" or w == "Sgt.":
            out_word = "Sergeant"
        elif w == "Sgts" or w == "Sgts.":
            out_word = "Sergeants"
        elif w == "Gen.":
            out_word = "General"
        elif w == "Pt" or w == "Pt.":
            out_word = "Part"
        elif w == "pt" or w == "pt.":
            out_word = "part"
        elif w == "Fr" or w == "Fr.":
            out_word = "Father"
        elif w == "Rev" or w == "Rev.":
            out_word = "Reverend"
        elif w == "Vol" or w == "Vol.":
            out_word = "Volume"
        elif w == "vol" or w == "vol.":
            out_word = "volume"
        elif w == "Ch.":
            out_word = "Chapter"
        elif w == "ch.":
            out_word = "chapter"
        elif w == "pp" or w == "pp.":
            out_word = "pages"
        elif w == "p.":
            out_word = "page"
        elif w == "Ex:":
            out_word = "Example:"
        elif w == "Rep" or w == "Rep.":
            out_word = "Representative"
        elif w == "Govt" or w == "Govt.":
            out_word = "Government"
        elif w == "Dr" or w == "Dr.":
            out_word = "Doctor"
        elif w == "Drs" or w == "Drs.":
            out_word = "Doctors"
        elif w == "ca.":
            out_word = "circa"
        elif w == "Ca.":
            out_word = "California"
        elif w == "Co.":
            out_word = "Company"
        elif w == "Hon." or w == "Hon":
            out_word = "Honorable"
        elif w == "Inc.":
            out_word = "Incorporated"
        elif w == "v." or w == "vs" or w == "vs.":
            out_word = "versus"
        elif w == "Vs.":
            out_word = "Versus"
        elif w == "Msgr" or w == "Msgr.":
            out_word = "Monsignor"
        elif w == "St" or w == "St.":
            out_word = "Saint"
        elif w.endswith("St."):
            out_word = w[:-3] + "Saint"
        elif w == "Sts" or w == "Sts.":
            out_word = "Saints"
        elif w == "Ft" or w == "Ft.":
            out_word = "Fort"
        elif w.endswith("Ft."):
            out_word = w[:-3] + "Fort"
        elif w == "Ltd" or w == "Ltd.":
            out_word = "Limited"
        elif w == "Ltd's":
            out_word = "Limited's"
        elif w == "Ave.":
            out_word = "Avenue"
        elif w == "Brgy." or w == "Bgy.":
            out_word = "Barangay"
        elif w == "Hr.":
            out_word = "Higher"
        elif w == "Corp" or w == "Corp.":
            out_word = "Corporation"
        elif w == "Pfc.":
            out_word = "Private first class"
        elif w == "approx." or w == "appr.":
            out_word = "approximately"
        elif w == "Approx.":
            out_word = "Approximately"
        elif w == "Mtn.":
            out_word = "Mountain"
        elif w == "Mgmt.":
            out_word = "Management"
        elif w == "Vt.":
            out_word = "Vermont"
        elif w == "kg":
            out_word = "kilograms"
        elif w == "kg.":
            out_word = "kilograms."
        elif w == "km":
            out_word = "kilometers"
        elif w == "km.":
            out_word = "kilometers."
        elif w == "Wg.":
            out_word = "Wing"
        elif w == "Det.":
            out_word = "Detective"
        elif w == "Cllr" or w == "Cllr." or w == "Cr.":
            out_word = "Councillor"
        elif w == "Tenn" or w == "Tenn.":
            out_word = "Tennessee"
        elif w == "Brig.":
            out_word = "Brigadier"
        elif w == "Blvd" or w == "Blvd.":
            out_word = "Boulevard"
        elif w == "Lt.Col." or w == "Lieut-Col." or w == "Lt.-Col.":
            out_word = "Lieutenant Colonel"
        elif w == "Eq.":
            out_word = "Equation"
        elif w == "eq.":
            out_word = "equation"
        elif w == "Esq.":
            out_word = "Esquire"
        elif w == "Op.":
            out_word = "Opus"
        elif w == "Opp.":
            out_word = "Opuses"
        elif w == "Mk." or w == "Mk":
            out_word = "Mark"
        elif w == "mk." or w == "mk":
            out_word = "mark"
        elif w == "Hwy" or w == "Hwy.":
            out_word = "Highway"
        elif w == "Mar.":
            out_word = "March"
        elif w == "Maj" or w == "Maj.":
            out_word = "Major"
        elif w == "Maj.-Gen.":
            out_word = "Major General"
        elif w == "Gens.":
            out_word = "Generals"
        elif w == "Prof" or w == "Prof.":
            out_word = "Professor"
        elif w == "Cdr." or w == "Cmdr." or w == "Comdr." or w == "Cdr":
            out_word = "Commander"
        elif w == "d.b.a.":
            out_word = "doing business as"
        elif w == "a.k.a.":
            out_word = "also known as"
        elif w == "i.e.":
            out_word = "that is"
        elif w == "i.a.":
            out_word = "among others"
        elif w == "c.o.":
            out_word = "County"
        elif w == "viz.":
            out_word = "videlicet"
        elif w == "Prop.":
            out_word = "Proposition"
        elif w == "Jno.":
            out_word = "John"
        elif w == "ed.":
            out_word = "edition"
        elif w == "Ed.":
            out_word = "Edition"
        elif w == "rev.":
            out_word = "revision"
        elif w == "Dt.":
            out_word = "Detective"
        elif w == "Dts.":
            out_word = "Detectives"
        elif w == "sp.":
            out_word = "spelling"
        elif w == "Jct." or w == "Jcn.":
            out_word = "Junction"
        elif w == "Rs.":
            out_word = "rupees"
        elif w == "Est.":
            out_word = "Established"
        elif w == "var.":
            out_word = "variety"
        elif w == "Var.":
            out_word = "Variation"
        elif w == "Jkr.":
            out_word = "Junker"
        elif w == "Retd.":
            out_word = "Retired"
        elif w == "Gov.":
            out_word = "Governor"
        elif w == "Atty.":
            out_word = "Attorney"
        elif w == "Adml.":
            out_word = "Admiral"
        elif w == "Adv.":
            out_word = "Advocate"
        elif w == "Skr.":
            out_word = "Skipper"
        elif w == "Br.":
            out_word = "Brother"
        elif w == "Md.":
            out_word = "Maryland"
        elif w == "Md.,":
            out_word = "Maryland,"
        elif w == "Pres.":
            out_word = "President"
        elif w == "pres.":
            out_word = "president"
        elif w == "Ore.":
            out_word = "Oregon"
        elif w == "Lv." or w == "Lvl.":
            out_word = "Level"
        elif w == "Rd." or w == "Rd":
            out_word = "Road"
        elif w == "Ln." or w == "Ln":
            out_word = "Lane"
        elif w == "Ave." or w == "Ave":
            out_word = "Avenue"
        elif w == "spp.":
            out_word = "species"
        elif w == "ssp." or w == "subsp.":
            out_word = "subspecies"
        elif w == "Adj.":
            out_word = "Adjudicator"
        elif w == "Sec.":
            out_word = "Section"
        elif w == "Mfg.":
            out_word = "Manufacturing"
        elif w == "Tec.Sgt." or w == "Tec.Sgt":
            out_word = "Technical Sergeant"
        elif w == "iii.":
            out_word = "three"
        elif w == "iv.":
            out_word = "four"
        elif w == "vi.":
            out_word = "six"
        elif w == "vii.":
            out_word = "seven"
        elif w == "viii.":
            out_word = "eight"
        elif w == "ix.":
            out_word = "nineteen"
        elif w == "xi.":
            out_word = "twenty-two"
        elif w == "xiii.":
            out_word = "twenty-three"
        elif w == "xiv.":
            out_word = "twenty-four"
        elif w == "xv.":
            out_word = "twenty-five"
        elif w == "xvi.":
            out_word = "twenty-six"
        elif w == "xvii.":
            out_word = "twenty-seven"
        elif w == "xviii.":
            out_word = "twenty-eight"
        elif w == "ofyet":
            out_word = "of yet"
        elif w == "Co.Tyrone":
            out_word = "County Tyrone"
        elif w == "Nr":
            out_word = "Near"
        elif w == "nr":
            out_word = "near"
        elif w == "Mgr" or w == "Mgr.":
            out_word = "Manager"
        elif w == "Mme" or w == "Mme.":
            out_word = "Madame"
        elif w == "b.":
            out_word = "born"

        out_words.append(start_punctuation + out_word + end_punctuation)
        
    return " ".join(out_words)
    
def containsForeignTerm(words): 
    global regex_split_punctuation

    for w in words:
        sub_words = regex_split_punctuation.split(w) # Split on - or ...
        for sw in sub_words:
            sw_unstripped = sw
            
            # Prevent merging of apostrophes that could trigger erroneous results
            if sw.endswith("'s"):
                sw = sw[:-2]
            if sw.startswith("o'"):
                sw = sw[2:]

            sw = re.sub(r'[^[a-zA-Z]','', sw)
            sw_lower = sw.lower()
            
            if sw_unstripped == "i" or sw_unstripped == "y" or sw_unstripped == "e":
                return True
            
            # Case sensitive
            full_patterns = ["le","ng","les","del","al","das","du","dos","el","des","dil","ma","fu","pe","si","im","Ii","ni"]
        
            for p in full_patterns:
                if sw == p:
                    return True
            
            # Case insensitive
            full_insensitive_patterns = ["og","la","ap","ibn","et","ga","sur","aj","ud", \
            "ix","ich","zur","und","una","jou","jus","que","qui","est","te","tu","il","avec","vous","yr","ar","sa","auf","ny", \
            "na","vi","ein","ist","alte","mon","lei","lui","mi","moi","rasa","zu","mit","von","au","je","ne","jah","uz","png", \
            "ja","za","ka","ba","ch","lok","ool","ry","haq","huq","ul","ga","roi","dh","pe","aa","ke","ona","ww","ak", \
            "mi","fa","ji","deg","gu","dei","toh","ar","ge","rrh","aoi","och","fod","megc","om","ol","ua","pu","ee","xie","nwo","sui","siya"]
        
            for p in full_insensitive_patterns:
                if sw_lower == p:
                    return True

            # Starts
            insensitive_starts = ["mb","nd","cni","uem","krk","yps","mw","khu","mst","mku","mh","mt","dje","ouag","izq","shch","nh","slh","prf",\
            "ht","sb","gsc","gsa","gsh","jha","psk","izb","xio","xua","ss","pyeo","kii","md","lv","srp","vli","pht","atq","ks","maar","maac","maan", \
            "maal","maay","mij","bsh","ff","sree","nk","sht","mf","nts","nta","ntc","nto","ntu","nty","nte","nti","ntl","iwa","dho","dham","dhav", \
            "dho","dhar","dhau","dhaw","dham","dhan","dhe","dhu","dhar","dhi","dhr","tj","khag","hao","sf","cw","akh","mri","mru","mro","mre","bho", \
            "chh","bhi","mrd","rattu","sattu","xia","xiu","xie","gye","mv","mg","mma","anky"]
        
            for p in insensitive_starts:
                if sw_lower.startswith(p):
                    return True

            # Ends
            insensitive_ends = ["rinae","dj","idae","siella","irae","dinae","tinae","linae","ginae","binae","sinae","thinae","ziella","vci","eong", \
            "yeon","izae","rji","tji","ensis","erae","losia","otl","ehr","rurus","ocactus","raea","oidea","pidea","nwg","chwr","vsk","zd","chiv","hwy", \
            "gwy","kii","sija","cija","dija","lija","nija","zija","kija","jija","pija","dw","wr","yj","kn","kw","skyi","cillus","kga","dh","hg","gt", \
            "adt","oru","nje","attu","swamy","lw","gyi","ndha","hr","nj"]
        
            for p in insensitive_ends:
                if sw_lower.endswith(p):
                    return True

            partial_patterns = ["sz","fj","rrr","vlt","icz","aen","aoa","gks","ldj","bha","oji","ijc","zej","aad","aass","nayi", \
            "yy","iiv","zdz","jja","jju","uuk","plj","vlj","dtt","aat","mts","vya","gnj","qar","jy","bhak","visn","abha","djed", \
            "ajat","rii","sii","tii","mii","jii","zii","sii","oii","pii","gii","lii","cii","nii","dzt","yngl","kht","qut","ilij", \
            "jg","aak","aey","ijp","gaon","lj","gju","zuu","eae","ydd","aew","ggj","tsip","dsche","iid","uqa","ianu","cnem","dyal" \
            "naja","naji","jid","gve","mjo","oelo","bhm","cj","gaa","bhm","idae","erft","aemu","raa","yaa","aay","ijs","ijen","ijer", \
            "ijes","ijed","oij","uij","zij","iim","iij","ooj","oides","imae","ilae","imae","aao","jh","ijr","jm","js","jt","jz", \
            "jf","jh","jk","jl","jp","jc","jv","jb","cx","gx","quu","waa","eaa","taa","uaa","paa","aaa","daa","faa","haa","jaa", \
            "laa","xaa","vaa","baa","eee","ooo","uuu","aax","aaz","aav","aaf","aag","aaj","aaq","aaw","aae","aau","aai","aap", \
            "euu","ruu","tuu","yuu","puu","auu","suu","duu","fuu","guu","huu","juu","kuu","luu","vuu","buu","muu","uuz","uuc","uuv", \
            "uub","uun","uua","uus","uud","uug","uuh","uuj","uul","uuq","uuw","uue","uur","uut","uui","uup","qii","yii","dii","fii", \
            "bii","iiz","iix","iic","iib","iis","iif","iik","iil","iiw","iie","iir","iiy","iiu","iio","iip","haa","gji","erae","ygg", \
            "dihy","zhs","azn","yaj","ijn","khn","czu","vyr","evg","vyd","uaca","jni","mrr","kkl","zvia","kkav","rkk","wys","uxii","asaa", \
            "hiei","yaya","wij","ijk","bvr","itja","zhn","jna","jra","satya","aev","hii","hhh","zzz","ajn","dhh","eorh","lsve","rzy","prze", \
            "korz","krze","hrze","brze","jij","phof","zha","zhi","zhu","czh","dtj","jiq","gkh","yts","vij","wph","krb","rija","lakh","sakh", \
            "dakh","bakh","czk","okch","ekch","ukch","giy","ovgr","vattu","onnu","jd","umz","aee","dhs","obz","abz","ukw","khra"]
            
            for p in partial_patterns:
                if sw_lower.count(p) > 0:
                    return True
            
            if len(sw_unstripped) > 2:
                prefix = sw[:2] if len(sw) > 2 else ""
                prefix_lower = prefix.lower()
                prefix_unstripped = sw_unstripped[:2]
                prefix_unstripped_lower = prefix_unstripped.lower()
                
                suffix = sw[-2] if len(sw) > 2 else ""
                suffix_lower = suffix.lower()
                suffix_unstripped = sw_unstripped[-2]
                suffix_unstripped_lower = suffix_unstripped.lower()

                if prefix_unstripped_lower == "l'" or prefix_unstripped_lower == "d'" or prefix_unstripped_lower == "q'" \
                or prefix_unstripped_lower == "j'" or prefix_unstripped_lower == "k'" or prefix_unstripped_lower == "b'" \
                or prefix_unstripped_lower == "z'" or prefix_unstripped_lower == "s'" \
                or prefix == "Hr" or prefix_lower == "tl" or prefix == "Rj" or prefix == "Ng" or prefix == "Nj" or prefix == "Hl" \
                or prefix == "Tx" or prefix_lower == "cv" or prefix == "Tk" or prefix == "Zh" or prefix == "Kt" \
                or prefix_lower == "lj" or prefix == "Kj" or prefix == "Bj" or prefix == "Hj" or prefix == "Dn" \
                or prefix == "Qe" or prefix_lower == "sv" or prefix_lower == "sz" or prefix_lower == "tz" \
                or prefix_lower == "dz" or prefix == "Rz" or prefix_lower == "bz" or prefix_lower == "Nz" \
                or prefix == "Mz" or prefix == "Ys" or prefix == "Mx" or prefix == "tx" or prefix == "Yx" \
                or prefix_lower == "ix" or prefix_lower == "gx" or prefix_lower == "lx" or prefix_lower == "xx" \
                or prefix == "Nx" or prefix == "Vs" or prefix == "Vr" or prefix == "Vh" or prefix == "Vv" or prefix_lower == "vn" \
                or prefix == "Kw" or prefix == "Kp" or prefix == "Ks" or prefix == "Kg" or prefix == "Kz" or prefix == "Kv" \
                or prefix == "Qw" or prefix == "Qo" or prefix == "Qh" or prefix_lower == "ql" or prefix == "Qv" \
                or prefix_lower == "qn" or prefix_lower == "wd" or prefix == "Wl" or prefix_lower == "wm" or prefix == "Zw" \
                or prefix == "Zr" or prefix == "Zs" or prefix_lower == "zd" or prefix == "Zv" or prefix == "Zb" \
                or prefix_lower == "zn" or prefix == "Zm" or prefix == "Pf" or prefix == "Hv" or prefix == "Gj" \
                or prefix == "Srir" \
                or prefix == "Ts" or prefix_lower == "bw" or suffix == "kw" or suffix == "khr" or suffix_unstripped == "'u" \
                or suffix_unstripped == "'e" or suffix_unstripped == "'a" or suffix_unstripped == "'i" \
                or suffix_unstripped == "'o" or suffix_unstripped == "'h" or suffix_unstripped == "'r":
                    return True
                    
            # Q not followed by a U or I
            if "q" in sw_lower:
                if re.search(r"q[^ui',.:;!?\"\s]", sw_unstripped) is not None:
                    return True

            # Filter scientific-style names like "S. umbelliferum"
            line = " ".join(words)

            if "\"" in line:
                if re.search(r"\"[A-Z]\. ([a-z]{5,})\"", line) is not None:
                    return True

    return False
    
def containsFilteredWord(words):
    global regex_split_punctuation

    for w in words:
        sub_words = regex_split_punctuation.split(w) # Split on - or ...
        
        for sw in sub_words:
            sw = re.sub(r"[^[a-zA-Z']","", sw)
            if filter_list.count(sw.lower()) > 0:
                return sw
            
    return None
    
def containsMissingWords(line):
    words = line.split()

    for w in words:
        if w == "\"\"" or w == "\"\"." or w == "\"\"," or w == "\"\";" or w == "\"\":" or w == "\"\"!" or w == "'" \
        or w == "\"\"?" or w == "," or w == "." or w == "'s" or w == "\"\"," or w == "\",\"" or w.startswith("??") or w.startswith("\"??"):
            return True
            
    criteria = ["over of", "on of", "with of", "by of", "between of", "between and", "and and", "of and", "of of",\
     "than and","than of", "of but", "about long", "about wide", "about tall", "about short", "about thick",\
     "about deep", "about high", "about in size", "about from", "about off", "approximately long", "approximately wide",\
     "approximately tall", "approximately short", "approximately thick", "approximately deep", "approximately high",\
     "approximately in size", "from in", "to in", "from inches", "is in size", "than in size", "measures high", "measures wide",\
     "measures long", "measures in size","measuring in", "measuring between", "of per", "elevation of in", "elevation of and",\
     "lies only from", "about downstream", "about upstream", "about north", "about south", "about east", "about west",\
     "about northwest", "about northeast","about southwest", "about southeast", "approximately north", "approximately south", \
     "approximately east", "approximately west", "approximately northwest", "approximately northeast","approximately southwest",\
     "approximately southeast", "is in length", "of span", "is above sea level", "about in area","approximately in area", \
     "radius of from", "radius of and", "a area", "around long", "around wide", "around tall", "around short", "around thick", \
     "around deep", "around high", "around in size", "around in diameter", "weighed around and", "has of shoreline", "more than wide", "of include", \
     "that and are", "nearly by road", "about of", "around of", "approximately of", "up to long", \
     "up to wide", "up to tall", "up to thick", "up to deep", "up to high", "up to in size", "of about and", "of about from", \
     "of above sea level", "within of", "within a radius", "and from the border", "and from the frontier", "covers of land", \
     "covers of marine", "covers of grassland", "covers of wetlands", "of rs", "is just long", "an estimated long", \
     "an estimated wide", "an estimated tall", "an estimated thick", "an estimated deep", "an estimated high", \
     "an estimated in size", "to tall", "to diameter", "the and", "weighs by", "engages over adults", "approximately to", \
     "owned of land", "is in height", "is in width", "is in depth", "cooked to mixed", "up to and", "approximately past the", \
     "work in but", "from to wide", "calculated at and", "to of", "height of made", "height of and", "deep and in diameter", \
     "to about before", "than in diameter", "distance of from", "distance of to", "are in diameter", \
     "of nearly above sea level", "of nearly below sea level", "about later", "is some long", "of is", "located on owned", \
     "bulkheads thick", "located from", "few off", \
     "temperature of during", "precipitation is with", "long by in", "between per", "averages per", "about away", \
     "less than in", "from about up", "of around from", "reach of length", "other than are", "about away", \
     "the which", "around above", "around below", "about per", "are there are", "for for", "over while", "about inland", \
     "at on", "by be", "about apart", "on bordering", "greater than favor", \
     "more than thick", "are there are", "roughly wide", "roughly long", "roughly high", "roughly tall", "roughly deep", \
     "roughly short", "roughly from", "are each while", "averages of rain", \
     "dived to and", "approximately from", "ranging from long", "ranging from deep", "ranging from tall", \
     "ranging from wide", "to via", "at at", "with in", "is located is", "approximately below", "measuring deep", \
     "measuring long", "measuring wide", "measuring tall", "produce of thrust", "produce of torque", "of is", "the in", \
     "they and are", "nearly of", "variation is and", \
     "weigh and", "averages annually", "carried of fuel", "of the his", "of the her", "far as away", "measured at long", \
     "for about to", "temperatures above are", "approximately westward", "approximately eastward", "approximately northward", \
     "approximately southward", "rainfall was in one", "strength of has", "about below", "encompasses of land", \
     "over with higher", "estimated around and", "is in span", "is otherwise is", "can reach high", "can reach tall", \
     "can reach wide", "can reach deep", "-long", "-wide", "-deep", "-tall", "-high", "from of", \
     "less than long", "less than high", "less than deep", "less than tall", "greater than on", "less than on", \
     "more than on", "elevation of above", "elevation of below", "to above sea level", "to below sea level", \
     "to above ground level", "to below ground level", "less than to", "more than to", "greater than to", "is only away", \
     "about north", "about south", "about east", "about west", "the and", "is only wide", "is only long", "is only high", \
     "in of grounds", "remains above through", "remains above throughout", "remains below through", "remains below throughout", \
     "weigh and are", "up to of", "some north", "some east", "some south", "some west", "some northeast", "some northwest", \
     "some southeast", "some southwest", "over in size", "over in width", "over in height", "over in depth", "about of", \
     "services to will", "length of or", "width of or", "depth of or" "height of or", "from to", "area of in", "consists of in", \
     "average of in", "average low of in", "average high of in", "maximum of in", "minimum of in", "neighborhood of in", "speed of in", \
     "purchase of in", "survivors of in", "altitude of in", "out of in", "temperature of in", "depth of in", "arrival of in", "heights of in", \
     "peaks of in", "excess of in", "sources of in", "amplitude of in", "pronunciation of in", "temperate of in", \
     "record of in", "distance of in", "depths of in", "basin of in", "suburb of in", "levels of in", "levels of in", "wingspan of in", \
     "role of in", "total of in", "capable of in", "January of in", "consisted of in", "top of in", "length of in", "at in length", "highs around and", \
     "orbits at and", "between in diameter", "estimated as from", "given as from", "approximately in diameter", "born on in", "approximately north east", \
     "it is and", "of another north", "of another east", "of another south", "of another west", "varies from throughout", "as far as away", "at is", \
     "speed of has", "between in elevation", "comprised about or", "in the at", "long by wide", "its length is and", "its width is and", \
     "its depth is and", "its height is and", "reach in length", "reach in size", "reaches in length", "reaches in size", "around of", "approximately of", \
     "is and at", "runs for through", "flows for through", "eastward for through", "around of", "approximately of", "is mm", "was mm", "were mm", "is km", \
     "was km", "were km", "between mm", "between mm", "for mm", "for km"]
     
    unstripped = re.sub(r'[^[a-zA-Z ,\"\':;\."]','', line)
    stripped = re.sub(r'[^[a-zA-Z ]','', line).lower()
     
    for c in criteria:
        # Make sure phrase appears without punctuation in the middle e.g. but, and
        if unstripped.count(c) > 0:
            if stripped.count(" " + c + " ") > 0 or stripped.startswith(c + " ") or stripped.endswith(" " + c):
                return True
    
    if unstripped.startswith("It and "):
        return True

    if re.search(r"(the)\ [A-Z]\.$", line) is not None:
        return True

    return False

def lengthCheck(word):
    word = word.lower()

    # Remove common prefixes like "un"
    prefixes = ["un", "re", "anti", "straight", "super", "extra", "inter", "dis", "math", "in", "circum", "const", "pre", "non", "counter", "radio", "intel", \
    "semi", "con", "business"]
    
    for prefix in prefixes:
        if word.startswith(prefix):
            word = word[len(prefix):]

    # Remove common suffixes like "ing"
    suffixes = ["es", "ness", "s", "'s", "ised", "ized", "ise", "ize", "ed", "en", "ism", "ing", "ly", "ion", "al", "ity", "y", "ment", "ic", "ive", "ist", \
    "ar", "ible", "able", "re", "ce", "er", "or", "an", "burg", "ship", "ous", "ia", "borough", "land", "town", "ville", "house", "person", "people", "ton", "son", \
    "mouth", "foot", "waite", "worth", "ham", "dale", "point", "stead"]
    
    for suffix in suffixes:
        if word.endswith(suffix):
            suffix_length = len(suffix) * -1
            word = word[:suffix_length]
            
    return len(word) > 13
    
runScript()

