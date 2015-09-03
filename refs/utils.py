def fuzzymatch(n1, n2):
    """Match two numeric values.

    We adopt the convention that a numeric value of -1 means not provided,
    so here we match two quantites where either or both is not provided.
    Only return False if both numbers are provided and they are not equal;
    otherwise give the benefit of the doubt and return True.
    """
    if n1 <= 0 or n2 <= 0:
        return True
    return n1 == n2


def english_join(words):
    if len(words) == 1:
        return words[0]
    elif len(words) > 1:
        return "%s and %s" % (", ".join(words[:-1]), words[-1])
    else:
        return ""


def mogrify(s):
    """Removes punctuation marks and white space."""
    s = string.lower(s)
    s = re.sub(r"[#{}:,&$ -'\"]", "", s)
    return s
