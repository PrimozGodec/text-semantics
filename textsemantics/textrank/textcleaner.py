"""
Module was removed from gensim - this is a fixed copy.

This module contains functions and processors used for processing text,
extracting sentences from text, working with acronyms and abbreviations.

Data
----

.. data:: SEPARATOR - Special separator used in abbreviations.
.. data:: RE_SENTENCE - Pattern to split text to sentences.
.. data:: AB_SENIOR - Pattern for detecting abbreviations (example: Sgt. Pepper).
.. data:: AB_ACRONYM - Pattern for detecting acronyms.
.. data:: AB_ACRONYM_LETTERS - Pattern for detecting acronyms (example: P.S. I love you).
.. data:: UNDO_AB_SENIOR - Pattern like AB_SENIOR but with SEPARATOR between abbreviation and next word.
.. data:: UNDO_AB_ACRONYM - Pattern like AB_ACRONYM but with SEPARATOR between abbreviation and next word.

"""


from textsemantics.textrank.syntactic_unit import SyntacticUnit
from gensim.parsing.preprocessing import preprocess_documents
from gensim.utils import tokenize, has_pattern
from six.moves import range
import re
import logging

logger = logging.getLogger(__name__)

HAS_PATTERN = has_pattern()
if HAS_PATTERN:
    from pattern.en import tag

SEPARATOR = r'@'
RE_SENTENCE = re.compile(r'(\S.+?[.!?])(?=\s+|$)|(\S.+?)(?=[\n]|$)', re.UNICODE)
AB_SENIOR = re.compile(r'([A-Z][a-z]{1,2}\.)\s(\w)', re.UNICODE)
AB_ACRONYM = re.compile(r'(\.[a-zA-Z]\.)\s(\w)', re.UNICODE)
AB_ACRONYM_LETTERS = re.compile(r'([a-zA-Z])\.([a-zA-Z])\.', re.UNICODE)
UNDO_AB_SENIOR = re.compile(r'([A-Z][a-z]{1,2}\.)' + SEPARATOR + r'(\w)', re.UNICODE)
UNDO_AB_ACRONYM = re.compile(r'(\.[a-zA-Z]\.)' + SEPARATOR + r'(\w)', re.UNICODE)


def replace_with_separator(text, separator, regexs):
    """Get text with replaced separator if provided regular expressions were matched.

    Parameters
    ----------
    text : str
        Input text.
    separator : str
        The separator between words to be replaced.
    regexs : list of `_sre.SRE_Pattern`
        Regular expressions used in processing text.

    Returns
    -------
    str
        Text with replaced separators.

    """
    replacement = r"\1" + separator + r"\2"
    result = text
    for regex in regexs:
        result = regex.sub(replacement, result)
    return result


def merge_syntactic_units(original_units, filtered_units, tags=None):
    """Process given sentences and its filtered (tokenized) copies into
    :class:`~textsemantics.textrank.syntactic_unit.SyntacticUnit`. Also adds tags if they are provided to produced units.

    Parameters
    ----------
    original_units : list
        List of original sentences.
    filtered_units : list
        List of tokenized sentences.
    tags : list of str, optional
        List of strings used as tags for each unit. None as default.

    Returns
    -------
    list of :class:~textsemantics.textrank.syntactic_unit.SyntacticUnit
        List of syntactic units (sentences).

    """
    units = []
    for i in range(len(original_units)):
        if filtered_units[i] == '':
            continue

        text = original_units[i]
        token = filtered_units[i]
        tag = tags[i][1] if tags else None
        sentence = SyntacticUnit(text, token, tag, i)

        units.append(sentence)

    return units


def join_words(words, separator=" "):
    """Concatenates `words` with `separator` between elements.

    Parameters
    ----------
    words : list of str
        Given words.
    separator : str, optional
        The separator between elements.

    Returns
    -------
    str
        String of merged words with separator between elements.

    """
    return separator.join(words)


def clean_text_by_word(text, deacc=True):
    """Tokenize a given text into words, applying filters and lemmatize them.

    Parameters
    ----------
    text : str
        Given text.
    deacc : bool, optional
        Remove accentuation if True.

    Returns
    -------
    dict
        Words as keys, :class:`~textsemantics.textrank.syntactic_unit.SyntacticUnit` as values.

    Example
    -------
    .. sourcecode:: pycon

        >>> from gensim.summarization.textcleaner import clean_text_by_word
        >>> clean_text_by_word("God helps those who help themselves")
        {'god': Original unit: 'god' *-*-*-* Processed unit: 'god',
        'help': Original unit: 'help' *-*-*-* Processed unit: 'help',
        'helps': Original unit: 'helps' *-*-*-* Processed unit: 'help'}

    """
    text_without_acronyms = replace_with_separator(text, "", [AB_ACRONYM_LETTERS])
    original_words = list(tokenize(text_without_acronyms, to_lower=True, deacc=deacc))
    filtered_words = [join_words(word_list, "") for word_list in preprocess_documents(original_words)]
    if HAS_PATTERN:
        tags = tag(join_words(original_words))  # tag needs the context of the words in the text
    else:
        tags = None
    units = merge_syntactic_units(original_words, filtered_words, tags)
    return {unit.text: unit for unit in units}


def tokenize_by_word(text, deacc):
    """Tokenize input text. Before tokenizing transforms text to lower case and removes accentuation and acronyms set
    :const:`~gensim.summarization.textcleaner.AB_ACRONYM_LETTERS`.

    Parameters
    ----------
    text : str
        Given text.

    Returns
    -------
    generator
        Generator that yields sequence words of the given text.

    Example
    -------
    .. sourcecode:: pycon

        >>> from gensim.summarization.textcleaner import tokenize_by_word
        >>> g = tokenize_by_word('Veni. Vidi. Vici.')
        >>> print(next(g))
        veni
        >>> print(next(g))
        vidi
        >>> print(next(g))
        vici

    """
    text_without_acronyms = replace_with_separator(text, "", [AB_ACRONYM_LETTERS])
    return tokenize(text_without_acronyms, to_lower=True, deacc=deacc)
