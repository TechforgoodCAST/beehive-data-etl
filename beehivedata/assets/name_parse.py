import re
import titlecase

def title_exceptions(word, **kwargs):

    word_test = word.strip("(){}<>.")

    # lowercase words
    if word_test.lower() in ['a', 'an', 'of', 'the', 'is', 'or']:
        return word.lower()

    # uppercase words
    if word_test.upper() in ['UK', 'FM', 'YMCA', 'PTA', 'PTFA',
                             'NHS', 'CIO', 'U3A', 'RAF', 'PFA', 'ADHD',
                             'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI',
                             'AFC', 'CE', 'CIC'
                            ]:
        return word.upper()

    # words with only vowels that aren't all uppercase
    if word_test.lower() in ['st', 'mr', 'mrs', 'ms', 'ltd', 'dr', 'cwm', 'clwb', 'drs']:
        return None

    # words with number ordinals
    ord_numbers_re = re.compile("([0-9]+(?:st|nd|rd|th))")
    if bool(ord_numbers_re.search(word_test.lower())):
        return word.lower()

    # words with dots/etc in the middle
    for s in [".", "'", ")"]:
        dots = word.split(s)
        if(len(dots) > 1):
            # check for possesive apostrophes
            if s == "'" and dots[-1].upper() == "S":
                return s.join([titlecase.titlecase(i, title_exceptions) for i in dots[:-1]] + [dots[-1].lower()])
            # check for you're and other contractions
            if word_test.upper() in ["YOU'RE", "DON'T", "HAVEN'T"]:
                return s.join([titlecase.titlecase(i, title_exceptions) for i in dots[:-1]] + [dots[-1].lower()])
            return s.join([titlecase.titlecase(i, title_exceptions) for i in dots])

    # words with only vowels in (treat as acronyms)
    vowels = re.compile("[AEIOUYaeiouy]")
    if not bool(vowels.search(word_test)):
        return word.upper()

    return None


def parse_name(name):
    if type(name) != str:
        return name

    name = name.strip()

    # if it contains any lowercase letters then return as is
    for c in name:
        if c.islower():
            return name

    # try titlecasing
    try:
        name = titlecase.titlecase(name, title_exceptions)
    except:
        pass

    # Make sure first letter is capitalise
    return name[0].upper() + name[1:]
