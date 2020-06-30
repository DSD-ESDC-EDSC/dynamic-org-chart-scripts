'''
Functions to convert flat file into hierarchical file - borrowed from this
(https://stackoverflow.com/questions/43757965/convert-csv-to-json-tree-structure)
StackOverflow post - see link for more detail on how these functions work.
'''
from collections import defaultdict

def ctree():
    """ 
    One of the python gems. Making possible to have dynamic tree structure.
    """
    return defaultdict(ctree)

def build_leaf(name, leaf):
    """ 
    Recursive function to build desired custom tree structure.

    Args:
        name:
            A string containing the name that is attached to this node
            of the tree.
        leaf:
            A dict-like object.
    """
    # Only want to process names if it is a string
    if type(name) is str:
        res = {"name": name.rstrip()}
        # add children node if the leaf actually has any children
        if len(leaf.keys()) > 0:
            res["_children"] = [build_leaf(k, v) for k, v in leaf.items()]
        return res


def flat_to_hierarchical(df):
    """ 
    The main thread composed from two parts. First it's parsing the csv 
    file and builds a tree hierarchy from it. Second it's recursively iterating
    over the tree and building custom json-like structure (via dict).

    Args:
        df:
            A pandas dataframe that is formatted in such a way that there are
            no duplicates (see the body of get_org_chart() for details on how
            to do this).
    Returns:
        res:
            A dict-like object containing the org structure.
    """
    tree = ctree()
    for _, row in df.iterrows():
        # usage of python magic to construct dynamic tree structure and
        # basically grouping csv values under their parents
        leaf = tree[row[1]]
        for cid in range(1, len(row)):
            if row[cid] is None:
                break
            leaf = leaf[row[cid]]
    # building a custom tree structure
    res = []
    for name, leaf in tree.items():
        res.append(build_leaf(name, leaf))
    return res

def get_org_chart(df):
    '''
    Returns an org chart as a python dict
    '''
    chart = flat_to_hierarchical(df)
    return chart