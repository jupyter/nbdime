
import copy


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


def patch_list(obj, diff):
    # The patched sequence to build and return
    newobj = []
    # Index into obj, the next item to take unless diff says otherwise
    take = 0
    for s in diff:
        action = s[0]
        index = s[1]
        assert isinstance(index, int)

        # Take values from obj not mentioned in diff, up to not including index
        newobj.extend(copy.deepcopy(value) for value in obj[take:index])

        if action == '+':
            # Append new value directly
            newobj.append(s[2])
            skip = 0
        elif action == '-':
            # Delete values obj[index] by incrementing take to skip
            skip = 1
        elif action == ':':
            # Replace value at obj[index] with s[2]
            newobj.append(s[2])
            skip = 1
        elif action == '!':
            # Patch value at obj[index] with diff s[2]
            newobj.append(patch(obj[index], s[2]))
            skip = 1
        # Experimental sequence diff actions:
        elif action == '++':
            # Extend with new values directly
            newobj.extend(s[2])
            skip = 0
        elif action == '--':
            # Delete values obj[index:index+s[2]] by incrementing take to skip
            skip = s[2]
        elif action == '::':
            # Replace values at obj[index:index+len(s[2])] with s[2]
            newobj.extend(s[2])
            skip = len(s[2])
        else:
            error_invalid_diff_entry(s)

        # Skip the specified number of elements, but never decrement take.
        take = max(take, index + skip)

    # Take values at end not mentioned in diff
    newobj.extend(copy.deepcopy(value) for value in obj[take:len(obj)])

    return newobj

def patch_str(obj, diff):
    # This can possibly be optimized for str if wanted, but
    # waiting until patch_list has been tested and debugged better
    return "".join(patch_list(list(obj), diff))

def patch_dict(obj, diff):
    newobj = {}
    keys_to_copy = set(obj.keys())
    for s in diff:
        action = s[0]
        key = s[1]
        assert isinstance(key, str)

        if action == '+':
            assert key not in keys_to_copy
            newobj[key] = s[2]
        elif action == '-':
            keys_to_copy.remove(key)
        elif action == ':':
            keys_to_copy.remove(key)
            newobj[key] = s[2]
        elif action == '!':
            keys_to_copy.remove(key)
            newobj[key] = patch(obj[key], s[2])
        else:
            error_invalid_diff_entry(s)
    # Take items not mentioned in diff
    for key in keys_to_copy:
        newobj[key] = copy.deepcopy(obj[key])
    return newobj


def patch(obj, diff):
    """Produce a patched version of obj with given hierarchial diff.

    A valid input object can be any dict or list of leaf values,
    or arbitrarily nested dict or list of valid input objects.

    Dicts are required to have string keys.

    Leaf values are any non-dict, non-list objects as far as patch
    is concerned, although the intentional use of this library
    is that values are json-serializable.
    """
    if isinstance(obj, dict):
        return patch_dict(obj, diff)
    elif isinstance(obj, list):
        return patch_list(obj, diff)
    elif isinstance(obj, str):
        return patch_str(obj, diff)
