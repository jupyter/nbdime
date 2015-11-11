
def error_invalid_diff_entry(s):
    raise RuntimeError("Invalid diff entry {}.".format(s))

def is_valid_diff(diff, deep=False):
    return isinstance(diff, list) and all(is_valid_diff_entry(s, deep=deep) for s in diff)

def is_valid_diff_entry(s, deep=False):
    """Check that s is a well formed diff entry.

    The diff entry format is a list
    s[0] # action (one of "+" (insert), "-" (delete), ":" (replace), "!" (patch))
    s[1] # key (str for diff of dict, int for diff of sequence (list or str))
    s[2] # action specific argument, omitted if action is "-"

    Additional experimental sequence actions "++", "--", "::" are also allowed.
    """

    # Entry is always a list with 2 or 3 items
    if not isinstance(s, list):
        return False
    n = len(s)
    if n < 2 or n > 3:
        return False

    # Check key (list or str uses int key, dict uses str key)
    is_sequence = isinstance(s[1], int)
    is_mapping = isinstance(s[1], str)
    if not (is_sequence or is_mapping):
        return False

    # Experimental sequence diff actions ++, --, :: are not valid for mapping diffs
    if is_mapping and len(s[0]) > 1:
        return False

    if s[0] == "+":
        # s[2] is a single value to insert at key
        if n != 3:
            return False
    elif s[0] == "-":
        # no s[2] argument
        if n != 2:
            return False
    elif s[0] == ":":
        # s[2] is a single value to replace value at key with
        if n != 3:
            return False
    elif s[0] == "!":
        # s[2] is itself a diff, check it recursively if the 'deep' argument is true
        # (the 'deep' argument is here to avoid recursion and potential O(>n) performance pitfalls)
        if n != 3 or (deep and not is_valid_diff(s[2], deep=deep)):
            return False
    # Experimental sequence diff actions
    elif s[0] == "++":
        # For sequence insert, s[2] is a list of values to insert.
        if n != 3 or not isinstance(s[2], list):
            return False
    elif s[0] == "--":
        # s[2] is the number of items to delete from sequence
        if n != 3 or not isinstance(s[2], int):
            return False
    elif s[0] == "::":
        # For sequence replace, s[2] is a list of values to
        # replace the next len(s[2]) values starting at key.
        if n != 3 or not isinstance(s[2], list):
            return False
    else:
        # Unknown action
        return False

    # Note that false positives are possible, for example
    # we're not checking the values in any way
    return True
