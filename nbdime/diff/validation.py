
class NBDiffFormatError(ValueError):
    pass

def error(msg):
    raise NBDiffFormatError(msg)

def error_invalid_diff_entry(s):
    error("Invalid diff entry {}.".format(s))

def is_valid_diff(diff, deep=False):
    try:
        validate_diff(diff, deep=deep)
        result = True
    except:
        result = False
    return result

def validate_diff(diff, deep=False):
    if not isinstance(diff, list):
        error("Diff must be a list.")
    for s in diff:
        validate_diff_entry(s, deep=deep)

def validate_diff_entry(s, deep=False):
    """Check that s is a well formed diff entry.

    The diff entry format is a list
    s[0] # action (one of "+" (insert), "-" (delete), ":" (replace), "!" (patch))
    s[1] # key (str for diff of dict, int for diff of sequence (list or str))
    s[2] # action specific argument, omitted if action is "-"

    Additional experimental sequence actions "++", "--", "::" are also allowed.
    """

    # Entry is always a list with 3 items, or 2 in the special case of single item deletion
    if not isinstance(s, list):
        error("Diff entry {} is not a list.".format(s))
    n = len(s)
    if not (n == 3 or (n == 2 and s[0] == "-")):
        error("Diff entry {} has the wrong size.".format(s))

    # Check key (list or str uses int key, dict uses str key)
    is_sequence = isinstance(s[1], int)
    is_mapping = isinstance(s[1], basestring)
    if not (is_sequence or is_mapping):
        error("Diff entry key {} has type {}, expecting int or basestring.".format(s[1], type(s[1])))

    # Experimental sequence diff actions ++, --, :: are not valid for mapping diffs
    if is_mapping and len(s[0]) > 1:
        error("Diff action {} only valid in diff of sequence.".format(s[0]))

    if s[0] == "+":
        # s[2] is a single value to insert at key
        pass
    elif s[0] == "-":
        # no s[2] argument
        pass
    elif s[0] == ":":
        # s[2] is a single value to replace value at key with
        pass
    elif s[0] == "!":
        # s[2] is itself a diff, check it recursively if the 'deep' argument is true
        # (the 'deep' argument is here to avoid recursion and potential O(>n) performance pitfalls)
        if deep:
            validate_diff(s[2], deep=deep)
    # Experimental sequence diff actions
    elif s[0] == "++":
        # For sequence insert, s[2] is a list of values to insert.
        if not isinstance(s[2], list):
            error("Diff sequence insert expects list of values, not {}.".format(s[2]))
    elif s[0] == "--":
        # s[2] is the number of items to delete from sequence
        if not isinstance(s[2], int):
            error("Diff sequence delete expects integer number of values, not {}.".format(s[2]))
    elif s[0] == "::":
        # For sequence replace, s[2] is a list of values to
        # replace the next len(s[2]) values starting at key.
        if not isinstance(s[2], list):
            error("Diff sequence replace expects list of values, not {}.".format(s[2]))
    else:
        # Unknown action
        error("Unknown diff action {}.".format(s[0]))

    # Note that false positives are possible, for example
    # we're not checking the values in any way
