def get_path_to_node(val, root_node):
    '''
    A recursive search function that returns the path to get to a given node
	in the tree.

	    Args:
	    	val:
	    		A string containing the name of the node that you want to get
	    		the path to.
	    	root_node:
	    		A dict that contains the root of the org structure chart

	    Returns:
	    	stack:
	    		A list containing the path to get to the target node starting
	    		from root.
    '''
    node_found = False
    stack = []
    def get_path_rec(node):
        '''
        '''
        # Important: python defaults to the innermost scope; need to explicitly
        # declare non-local variables as such
        nonlocal node_found
        #print(node_found)
        if node_found:
            pass
        if "_children" in node.keys():
            for i in range(0, len(node["_children"])):
                if not node_found:
                    stack.append(i)
                    get_path_rec(node["_children"][i])
        
        if node["name"] == val and not node_found:
            node_found = True
            pass
        elif not node_found:
            try:
                stack.pop()
            except Exception as e:
                pass
    get_path_rec(root_node)
    return stack