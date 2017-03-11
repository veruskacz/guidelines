PREFIX ="""
    PREFIX bdb: <http://vocabularies.bridgedb.org/ops#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX linkset: <http://risis.eu/linkset/>
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX alivocab: <http://risis.eu/alignment/predicate/>
    PREFIX tmpgraph: <http://risis.eu/alignment/temp-match/>
"""

def get_graph_lens():
    query = PREFIX + """
    SELECT DISTINCT ?g ?g_label ?triples ?operator
    WHERE
    {
        ?g
            rdf:type	        bdb:Lens ;
            alivocab:operator   ?operator ;
            void:triples        ?triples .
    }
    """
    return query


def get_graph_linkset():
    query = PREFIX + """
    SELECT DISTINCT ?g ?g_label ?subjectTargetURI ?subjectTarget
                    ?objectTargetURI ?objectTarget ?triples
                    ?alignsSubjects ?alignsObjects ?alignsMechanism
    WHERE
    {
        ?g
            rdf:type	 void:Linkset ;
            <http://rdfs.org/ns/void#subjectsTarget> ?subjectTargetURI;
            <http://rdfs.org/ns/void#objectsTarget> ?objectTargetURI;
            <http://rdfs.org/ns/void#triples> ?triples;
            <http://risis.eu/alignment/predicate/alignsSubjects> ?alignsSubjects;
            <http://risis.eu/alignment/predicate/alignsObjects> ?alignsObjects;
            <http://risis.eu/alignment/predicate/alignsMechanism> ?alignsMechanism.

        #FILTER regex(str(?g), 'linkset', 'i')
        BIND(strafter(str(?g),'linkset/') AS ?g_label)
        BIND(UCASE(strafter(str(?subjectTargetURI),'dataset/')) AS ?subjectTarget)
        BIND(UCASE(strafter(str(?objectTargetURI),'dataset/')) AS ?objectTarget)
    }
    """
    return query


def get_correspondences(graph_uri):

    query = """
    select distinct ?sub ?pred ?obj
    {
        GRAPH <""" + graph_uri + """> { ?sub ?pred ?obj }
        GRAPH ?g { ?pred ?p ?o }

    } limit 80
        """
    return query


def get_target_datasets(singleton_matrix):

    sample = """
    ### LINKSET WHERE A CORRESPONDENCE MIGHT HAV HAPPENED
    graph ?graph { ?sub <_#_> ?obj .
    }"""

    union = "{"
    if len(singleton_matrix) > 2:
        for i in range(1, len(singleton_matrix)):
            if i == 1:
                union += sample.replace('_#_', singleton_matrix[i][0])
            else:
                union += "\n\t     }\n\t      UNION\n\t     {" + sample.replace('_#_', singleton_matrix[i][0])
            if i == len(singleton_matrix)-1:
                union += "\n\t     }"
    else:
        union = """
        graph ?graph
        {{
            ?sub <{}> ?obj .
        }}""".format(singleton_matrix[1][0])

    query = """
    {}
    select distinct ?sub ?obj ?graph ?subjectsTarget ?objectsTarget ?alignsSubjects ?alignsObjects ?alignsMechanism
    where
    {{
        ### Initially, we have A -> B via Z
        ### Z is derived from X, Y and W
        ### So we could replaced Z with X or Y or Z and find out the graph for with the assertion holds
        {}

        ### Once we find those graphs, it means that we can extract the same source
        ### and target datasets that hold details about the entities being linked
        ?graph
           void:subjectsTarget 			?subjectsTarget ;
           void:objectsTarget  			?objectsTarget .
        OPTIONAL {{ ?graph	  alivocab:alignsMechanism  ?alignsMechanism }}
        OPTIONAL {{ ?graph    alivocab:alignsSubjects   ?alignsSubjects }}
        OPTIONAL {{ ?graph    alivocab:alignsObjects    ?alignsObjS }}

        # ### Here, we could easily have the description of the entities from
        # ### the source and target datasets
        # ### and... VOILA!!!
        # ### The only thing is that all ?graph being linksets :(
        # ### More to come on the mixed :-)
        # graph ?source
        # {{
        #    ?sub ?srcPre ?srcObj.
        # }}
        #
        # graph ?target
        # {{
        #    ?obj ?trgPre ?trgObj.
        # }}
        BIND (IF(bound(?alignsObjS), ?alignsObjS , "resource identifier") AS ?alignsObjects)
    }}
    """.format(PREFIX, union)

    # print query
    return query


def get_evidences(singleton, predicate=None):

    variable = ""
    pred = ""
    if predicate is None:
        variable = "?pred"
        pred = "?pred"
    else:
        pred = predicate

    query = """
    Select distinct ?obj {}
    {{
       GRAPH ?graph
  	   {{
            <{}> {} ?obj
       }}
    }}
    """.format(variable, singleton, pred)
    return query


def get_resource_description(graph, resource, predicate=None):

    # query = """
    # select distinct *
    # {
    #     graph <""" + graph + """>
    #     {
    #         <""" + resource + """> ?pred ?obj
    #     }
    # }
    # """
    triples = ""

    if predicate is None:
        triples = "\n\t   <{}> ?pred ?obj .".format(resource)

    elif type(predicate) is list:
        for i in range(len(predicate)):
            if predicate[i] != "resource identifier":
                triples += "\n\t   <{}> <{}> ?obj_{} .".format(resource, predicate[i], i)
        # print "TRIPLES", triples

    elif type(predicate) is str:
        if predicate != "resource identifier":
            triples += "\n\t   <{}> <{}> ?obj .".format(resource, predicate)

    query = """
    select distinct *
    {{
        graph <{}>
        {{{}
        }}
    }}
    """.format(graph, triples)
    # print query
    return query


def get_aligned_predicate_value(source, target, src_aligns, trg_aligns):

    query = """
    select distinct *
    {
        graph ?g_source
        { <""" + source + """> <""" + src_aligns + """> ?srcPredValue }

        graph ?g_target
        { <""" + target + """> <""" + trg_aligns + """> ?trgPredValue }
    }
    """
    return query