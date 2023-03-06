"""
(c)  Copyright  [2018-2023]  OpenText  or one of its
affiliates.  Licensed  under  the   Apache  License,
Version 2.0 (the  "License"); You  may  not use this
file except in compliance with the License.

You may obtain a copy of the License at:
http://www.apache.org/licenses/LICENSE-2.0

Unless  required  by applicable  law or  agreed to in
writing, software  distributed  under the  License is
distributed on an  "AS IS" BASIS,  WITHOUT WARRANTIES
OR CONDITIONS OF ANY KIND, either express or implied.
See the  License for the specific  language governing
permissions and limitations under the License.
"""
from verticapy._utils._sql._format import quote_ident


def erase_prefix_in_name(name: str, prefix: list = []) -> str:
    """
    Excludes the input lists of prefixes from the 
    input name and returns it.
    When there is a match,  the other elements of 
    the list are ignored.

    Parameters
    ---------- 
    name: str
        Input name.
    prefix: list, optional
        List of prefixes.

    Returns
    -------
    name
        The name without the prefixes.
    """
    new_name = name
    for p in prefix:
        n = len(p)
        if p in new_name and new_name[:n] == p:
            new_name = new_name[n:]
            break
    return new_name


def erase_suffix_in_name(name: str, suffix: list = []) -> str:
    """
    Excludes the input lists of suffixes from the
    input name and returns it.
    When there is a match,  the other elements of 
    the list are ignored.

    Parameters
    ---------- 
    name: str
        Input name.
    suffix: list, optional
        List of suffixes.

    Returns
    -------
    name
        The name without the suffixes.
    """
    new_name = name
    for s in suffix:
        n = len(s)
        if s in new_name and new_name[-n:] == s:
            new_name = new_name[:-n]
            break
    return new_name


def erase_word_in_name(name: str, word: list = []) -> str:
    """
    Excludes the input lists of words from the 
    input name and returns it.
    When there is a match,  the other elements 
    of the list are ignored.

    Parameters
    ---------- 
    name: str
        Input name.
    word: list, optional
        List of words.

    Returns
    -------
    name
        The name without the input words.
    """
    for w in word:
        if w in name:
            return name.replace(w, "")
            break
    return name


def erase_in_name(
    name: str,
    suffix: list = [],
    prefix: list = [],
    word: list = [],
    order: list = ["p", "s", "w"],
) -> str:
    """
    Excludes the input lists of suffixes and 
    prefixes from the input name and returns 
    it.  When  there is a match,  the  other 
    elements of the list are ignored.

    Parameters
    ---------- 
    name: str
        Input name.
    suffix: list, optional
        List of suffixes.
    prefix: list, optional
        List of prefixes.
    word: list, optional
        List of words.
    order: list, optional
        The order of the process.
            s: suffix
            p: prefix
            w: word
        For example the list ["p", "s", "w"] will 
        start  by  excluding  the prefixes,  then 
        suffixes and finally the input words.

    Returns
    -------
    name
        The name without the prefixes, suffixes 
        and input words.
    """
    new_name = name
    f = {
        "p": (erase_prefix_in_name, prefix),
        "s": (erase_suffix_in_name, suffix),
        "w": (erase_word_in_name, word),
    }
    for x in order:
        new_name = f[x][0](new_name, f[x][1])
    return new_name


def is_similar_name(
    name1: str,
    name2: str,
    skip_suffix: list = [],
    skip_prefix: list = [],
    skip_word: list = [],
    order: list = ["p", "s", "w"],
) -> bool:
    """
    Excludes the input lists of suffixes, prefixes 
    and words from the input name and returns it.

    Parameters
    ---------- 
    name1: str
        First name to compare.
    name2: str
        Second name to compare.
    skip_suffix: list, optional
        List of suffixes to exclude.
    skip_prefix: list, optional
        List of prefixes to exclude.
    skip_word: list, optional
        List of words to exclude.
    order: list, optional
        The order of the process.
            s: suffix
            p: prefix
            w: word
        For example the list ["p", "s", "w"] will start 
        by  excluding the prefixes,  then suffixes  and 
        finally the input words.
        

    Returns
    -------
    bool
        True if the two names are similar, false 
        otherwise.
    """
    n1 = erase_in_name(
        name=name1, suffix=skip_suffix, prefix=skip_prefix, word=skip_word, order=order,
    )
    n2 = erase_in_name(
        name=name2, suffix=skip_suffix, prefix=skip_prefix, word=skip_word, order=order,
    )
    return n1 == n2


def belong_to_group(
    name: str,
    group: list,
    skip_suffix: list = [],
    skip_prefix: list = [],
    skip_word: list = [],
    order: list = ["p", "s", "w"],
) -> bool:
    """
    Excludes the input lists of suffixes, prefixes 
    and words from the  input name and looks if it 
    belongs to a specific group.

    Parameters
    ---------- 
    name: str
        Input Name.
    group: list
        List of names.
    skip_suffix: list, optional
        List of suffixes to exclude.
    skip_prefix: list, optional
        List of prefixes to exclude.
    skip_word: list, optional
        List of words to exclude.
    order: list, optional
        The order of the process.
            s: suffix
            p: prefix
            w: word
        For example the list ["p", "s", "w"] will 
        start  by excluding  the  prefixes,  then 
        suffixes and finally the input words.

    Returns
    -------
    bool
        True if the name belong to the input group, 
        false otherwise.
    """
    for name2 in group:
        if is_similar_name(
            name1=name,
            name2=name2,
            skip_suffix=skip_suffix,
            skip_prefix=skip_prefix,
            skip_word=skip_word,
            order=order,
        ):
            return True
    return False


def group_similar_names(
    colnames: list,
    skip_suffix: list = [],
    skip_prefix: list = [],
    skip_word: list = [],
    order: list = ["p", "s", "w"],
) -> dict:
    """
    Creates similar group using the input column 
    names.

    Parameters
    ---------- 
    colnames: list
        List of input names.
    skip_suffix: list, optional
        List of suffixes to exclude.
    skip_prefix: list, optional
        List of prefixes to exclude.
    skip_word: list, optional
        List of words to exclude.
    order: list, optional
        The order of the process.
            s: suffix
            p: prefix
            w: word
        For  example  the list ["p", "s", "w"] will 
        start  by   excluding  the  prefixes,  then 
        suffixes and finally the input words.

    Returns
    -------
    dict
        dictionary including the different groups.
    """
    result = {}
    for col in colnames:
        groupname = erase_in_name(
            name=col,
            suffix=skip_suffix,
            prefix=skip_prefix,
            word=skip_word,
            order=order,
        )
        if groupname not in result:
            result[groupname] = [col]
        else:
            result[groupname] += [col]
    return result


def gen_coalesce(group_dict: dict) -> str:
    """
    Generates the SQL statement to merge the 
    groups together.

    Parameters
    ---------- 
    group_dict: dict
        Dictionary  including the  different 
        groups.

    Returns
    -------
    str
        SQL statement.
    """
    result = []
    for g in group_dict:
        L = [quote_ident(elem) for elem in group_dict[g]]
        g_ident = quote_ident(g)
        if len(L) == 1:
            sql_tmp = quote_ident(group_dict[g][0])
            result += [f"{sql_tmp} AS {g_ident}"]
        else:
            sql_tmp = ", ".join(L)
            result += [f"COALESCE({sql_tmp}) AS {g_ident}"]
    return ",\n".join(result)
