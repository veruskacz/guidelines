import ast
import os
import time
import datetime
import rdflib
import traceback
import networkx as nx
import Alignments.Settings as St
import Alignments.NameSpace as Ns
import Alignments.UserActivities.ExportAlignment as Exp
from Alignments.Query import sparql_xml_to_matrix as sparql2matrix
import Alignments.Query as Qry
import Alignments.Utility as Ut
from Alignments.Utility import hasher as hash
# from Alignments.UserActivities.Plots import metric
# import cStringIO as buffer
# import Alignments.UserActivities.Plots as Plt
# _format = "%a %b %d %H:%M:%S:%f %Y"
# from Alignments.UserActivities.Plots import metric

_format = "It is %a %b %d %Y %H:%M:%S"
date = datetime.datetime.today()
_line = "--------------------------------------------------------------" \
        "--------------------------------------------------------------"


def matrix(row, column, init=0):
    # row, column = 8, 5;
    return [[init for x in range(row)] for y in range(column)]


def cluster(graph):

    count = 0
    clusters = dict()
    root = dict()

    for pair in graph:

        count += 1
        child_1 = pair[0]
        child_2 = pair[1]
        parent = ""

        # DATE CREATION
        the_date = "{}".format(datetime.datetime.today().strftime(_format))

        # CHECK WHETHER A CHILD HAS A PARENT
        has_parent_1 = True if child_1 in root else False
        has_parent_2 = True if child_2 in root else False
        print "{} Has Parents {}|{}".format(pair, has_parent_1, has_parent_2)

        if has_parent_1 is False and has_parent_2 is False:

            # GENERATE THE PARENT
            hash_value = hash(the_date + str(count) + graph)
            parent = "{}".format(str(hash_value).replace("-", "N")) if str(hash_value).startswith("-") \
                else "P{}".format(hash_value)

            # ASSIGN A PARENT TO BOTH CHILD
            root[child_1] = parent
            root[child_2] = parent

            # CREATE A CLUSTER
            if parent not in clusters:
                clusters[parent] = [child_1, child_2]

        elif has_parent_1 is True and has_parent_2 is True:

            # IF BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            if clusters[root[child_1]] == clusters[root[child_2]]:
                print "{} NOTHING TO DO\n".format(len(clusters))
                continue

            # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
            if len(clusters[root[child_1]]) >= len(clusters[root[child_2]]):
                parent = root[child_1]
                pop_parent = root[child_2]
                root[child_2] = parent

            else:
                parent = root[child_2]
                pop_parent = root[child_1]
                root[child_1] = parent

            # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
            for offspring in clusters[pop_parent]:
                root[offspring] = parent
                clusters[parent] += [offspring]

            # POP THE PARENT WITH THE LESSER CHILD
            clusters.pop(pop_parent)

        elif has_parent_1 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            parent = root[child_1]
            root[child_2] = parent
            clusters[parent] += [child_2]

        elif has_parent_2 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            parent = root[child_2]
            root[child_1] = parent
            clusters[parent] += [child_1]

        print "{} Clusters but the current is: {}\n".format(len(clusters), clusters[parent])

    return clusters


# LINKSET CLUSTERING
def cluster_triples(graph):

    count = 0
    clusters = dict()
    root = dict()

    # DOWNLOAD THE GRAPH
    print "0. DOWNLOADING THE GRAPH"
    response = Exp.export_alignment(graph)
    links = response['result']
    # print links

    # LOAD THE GRAPH
    print "1. LOADING THE GRAPH"
    g = rdflib.Graph()
    g.parse(data=links, format="turtle")

    print "2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(g))

    for subject, predicate, obj in g:

        count += 1
        child_1 = subject.n3()
        child_2 = obj.n3()
        # parent = ""

        # DATE CREATION
        the_date = "{}".format(datetime.datetime.today().strftime(_format))

        # CHECK WHETHER A CHILD HAS A PARENT
        has_parent_1 = True if child_1 in root else False
        has_parent_2 = True if child_2 in root else False
        # print "{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

        # BOTH CHILD ARE ORPHANS
        if has_parent_1 is False and has_parent_2 is False:

            # GENERATE THE PARENT
            hash_value = hash(the_date + str(count) + graph)
            parent = "{}".format(str(hash_value).replace("-", "N")) if str(hash_value).startswith("-") \
                else "P{}".format(hash_value)

            # ASSIGN A PARENT TO BOTH CHILD
            root[child_1] = parent
            root[child_2] = parent

            # CREATE A CLUSTER
            if parent not in clusters:
                clusters[parent] = [child_1, child_2]

                # MATRIX
                mx = matrix(10, 10)
                # ROW
                mx[0][1] = child_1
                mx[0][2] = child_2
                # COLUMNS
                mx[1][0] = child_1
                mx[2][0] = child_2
                # RELATION
                mx[1][2] = 1
                mx[2][1] = 1

                clusters["{}_M".format(parent)] = mx

        # BOTH CHILD HAVE A PARENT OF THEIR OWN
        elif has_parent_1 is True and has_parent_2 is True:

            # IF BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            if clusters[root[child_1]] == clusters[root[child_2]]:
                # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
                continue

            # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
            if len(clusters[root[child_1]]) >= len(clusters[root[child_2]]):
                parent = root[child_1]
                pop_parent = root[child_2]
                root[child_2] = parent

            else:
                parent = root[child_2]
                pop_parent = root[child_1]
                root[child_1] = parent

            # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
            for offspring in clusters[pop_parent]:
                root[offspring] = parent
                clusters[parent] += [offspring]

            # POP THE PARENT WITH THE LESSER CHILD
            clusters.pop(pop_parent)
            # print clusters["{}_M".format(pop_parent)]
            # print clusters["{}_M".format(parent)]

        elif has_parent_1 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            parent = root[child_1]
            root[child_2] = parent
            clusters[parent] += [child_2]

        elif has_parent_2 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            parent = root[child_2]
            root[child_1] = parent
            clusters[parent] += [child_1]

        # print "{} Clusters but the current is: {}\n".format(len(clusters), clusters[parent])

    print "3. NUMBER OF CLUSTER FOND: {}".format(len(clusters))
    return clusters


def cluster_triples2(graph, limit=0):

    count = 0
    clusters = dict()
    root = dict()

    # DOWNLOAD THE GRAPH
    print "\n0. DOWNLOADING THE GRAPH"
    response = Exp.export_alignment(graph)
    links = response['result']
    # print links

    # LOAD THE GRAPH
    print "1. LOADING THE GRAPH"
    g = rdflib.Graph()
    g.parse(data=links, format="turtle")

    print "2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(g))
    for subject, predicate, obj in g:

        count += 1
        child_1 = subject
        child_2 = obj
        # parent = ""

        # DATE CREATION
        the_date = "{}".format(datetime.datetime.today().strftime(_format))

        # CHECK WHETHER A CHILD HAS A PARENT
        has_parent_1 = True if child_1 in root else False
        has_parent_2 = True if child_2 in root else False

        # print "{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

        if has_parent_1 is False and has_parent_2 is False:

            if limit != 0 and len(clusters) > limit:
                continue
                # Do not add new clusters

            # GENERATE THE PARENT
            hash_value = hash(the_date + str(count) + graph)
            parent = "{}".format(str(hash_value).replace("-", "N")) if str(hash_value).startswith("-") \
                else "P{}".format(hash_value)

            # ASSIGN A PARENT TO BOTH CHILD
            root[child_1] = parent
            root[child_2] = parent

            # CREATE A CLUSTER
            if parent not in clusters:
                clusters[parent] = [child_1, child_2]

        elif has_parent_1 is True and has_parent_2 is True:

            # IF BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            if clusters[root[child_1]] == clusters[root[child_2]]:
                # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
                continue

            # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
            if len(clusters[root[child_1]]) >= len(clusters[root[child_2]]):
                parent = root[child_1]
                pop_parent = root[child_2]
                root[child_2] = parent

            else:
                parent = root[child_2]
                pop_parent = root[child_1]
                root[child_1] = parent

            # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
            for offspring in clusters[pop_parent]:
                root[offspring] = parent
                clusters[parent] += [offspring]

            # POP THE PARENT WITH THE LESSER CHILD
            clusters.pop(pop_parent)

        elif has_parent_1 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            parent = root[child_1]
            root[child_2] = parent
            clusters[parent] += [child_2]

        elif has_parent_2 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            parent = root[child_2]
            root[child_1] = parent
            clusters[parent] += [child_1]

        # print "{} Clusters but the current is: {}\n".format(len(clusters), clusters[parent])
    print "3. NUMBER OF CLUSTER FOND: {}".format(len(clusters))

    result = []
    for parent, in_cluster in clusters.items():
        query = Qry.linkset_aligns_prop(graph)
        response = sparql2matrix(query)
        # print response
        # get one value per cluster in order to exemplify it
        sample = ''
        if response['result'] and len(response['result']) >= 2:  # header and one line
            # print response['result']
            properties = response['result'][1][:2]
            sample_response = cluster_values2(in_cluster, properties, limit_resources=1)
            if sample_response['result'] and len(sample_response['result']) >= 2:  # header and one line
                # print sample_response['result']
                sample = sample_response['result'][1][0]
        result += [{'parent': parent, 'cluster': in_cluster, 'sample': sample}]

    return result


def cluster_dataset(dataset_uri, datatype_uri, graph_list=None):

    append = "#" if graph_list is None else ""
    values = ""

    # LIST OF GRAPHS
    if graph_list is not None:
        for alignment in graph_list:
            values += " <{}>".format(alignment)

    # QUERY FOR LINKSETS INVOLVE AND THEIR RESPECTIVE DATA SOURCE
    query = """
    PREFIX void:    <{}>
    PREFIX bdb:     <{}>
    PREFIX dataset: <{}>
    PREFIX foaf:    <{}>
    PREFIX ll:      <{}>
    PREFIX skos:    <{}>

    SELECT DISTINCT  ?linkset ?src_dataset ?trg_dataset
    {{
        bind(<{}> as ?input_dataset)
        bind(<{}> as ?input_datatype)
        {}VALUES ?linkset {{ {} }}

        graph ?input_dataset
        {{
            ?RESOURCE a ?input_datatype .
        }}

        ?linkset
            void:subjectsTarget							?src_dataset  ;
            void:objectsTarget 							?trg_dataset  ;
            void:subjectsTarget|void:objectsTarget		?input_dataset  ;
            bdb:subjectsDatatype|bdb:objectsDatatype	?input_datatype .
    }}""".format(Ns.void, Ns.bdb, Ns.dataset, Ns.foaf, Ns.alivocab, Ns.skos, dataset_uri, datatype_uri, append, values)
    response = sparql2matrix(query)

    count = 0
    clusters = dict()
    root = dict()

    if response[St.message] == "OK":

        # response = sparql_xml_to_matrix(query)
        mx = response[St.result]

        for row in range(1, len(mx)):

            graph = mx[row][0]
            # src_dataset = matrix[row][1]
            # trg_dataset = matrix[row][2]

            # DOWNLOAD THE GRAPH
            print "\n0. DOWNLOADING THE GRAPH"
            response = Exp.export_alignment(graph)
            links = response['result']
            # print links

            # LOAD THE GRAPH
            print "1. LOADING THE GRAPH"
            g = rdflib.Graph()
            g.parse(data=links, format="turtle")

            print "2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(g))
            for subject, predicate, obj in g:

                count += 1
                child_1 = subject
                child_2 = obj
                # parent = ""

                # DATE CREATION
                the_date = "{}".format(datetime.datetime.today().strftime(_format))

                # CHECK WHETHER A CHILD HAS A PARENT
                has_parent_1 = True if child_1 in root else False
                has_parent_2 = True if child_2 in root else False

                # print "{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

                if has_parent_1 is False and has_parent_2 is False:

                    # GENERATE THE PARENT
                    hash_value = hash(the_date + str(count) + dataset_uri)
                    parent = "{}".format(str(hash_value).replace("-", "N")) if str(hash_value).startswith("-") \
                        else "P{}".format(hash_value)

                    # ASSIGN A PARENT TO BOTH CHILD
                    root[child_1] = parent
                    root[child_2] = parent

                    # CREATE A CLUSTER
                    if parent not in clusters:
                        clusters[parent] = [child_1, child_2]

                elif has_parent_1 is True and has_parent_2 is True:

                    # IF BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
                    if clusters[root[child_1]] == clusters[root[child_2]]:
                        # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
                        continue

                    # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
                    if len(clusters[root[child_1]]) >= len(clusters[root[child_2]]):
                        parent = root[child_1]
                        pop_parent = root[child_2]
                        root[child_2] = parent

                    else:
                        parent = root[child_2]
                        pop_parent = root[child_1]
                        root[child_1] = parent

                    # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
                    for offspring in clusters[pop_parent]:
                        root[offspring] = parent
                        clusters[parent] += [offspring]

                    # POP THE PARENT WITH THE LESSER CHILD
                    clusters.pop(pop_parent)

                elif has_parent_1 is True:

                    # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                    parent = root[child_1]
                    root[child_2] = parent
                    clusters[parent] += [child_2]

                elif has_parent_2 is True:

                    # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                    parent = root[child_2]
                    root[child_1] = parent
                    clusters[parent] += [child_1]

            # print "{} Clusters but the current is: {}\n".format(len(clusters), clusters[parent])
            print "3. NUMBER OF CLUSTER FOND: {}".format(len(clusters))

    return clusters


def cluster_values(g_cluster, properties, display=False):

    """
    :param g_cluster: A LIST OF CLUSTERED RESOURCES
    :param properties: A LIST OF PROPERTIES OF INTEREST
    :param display: if True, display the matrix as a table
    :return: A DICTIONARY WHERE THE RESULT OF THE QUERY IS OBTAINED USING THE KEY: result
    """
    prop = ""
    union = ""
    for uri in properties:
        prop += " <{}>".format(uri.strip())

    for x in range(0, len(g_cluster)):
        if x > 0:
            append = "UNION"
        else:
            append = ""
        union += """ {}
        {{
            bind(<{}> as ?resource)
            graph ?input_dataset {{ ?resource ?property ?obj . }}
        }}""".format(append, g_cluster[x])

    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX bdb: <http://vocabularies.bridgedb.org/ops#>
    PREFIX dataset: <http://risis.eu/dataset/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX ll: <http://risis.eu/alignment/predicate/>
    PREFIX skos:        <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT  *
    {{
        values ?property {{{} }}
        {}
    }}""".format(prop, union)

    # print query
    response = sparql2matrix(query)
    if display is True:
        Qry.display_matrix(response, spacing=100, is_activated=True)
    return response


def cluster_values2(g_cluster, properties, distinct_values=True, display=False, limit_resources=100):

    """
    :param g_cluster: A LIST OF CLUSTERED RESOURCES
    :param properties: A LIST OF PROPERTIES OF INTEREST
    :param distinct_values: return distinct resources
    :param display: display the matrix as a table
    :param limit_resources: limit the number of resources to include in the cluster
    :return: A DICTIONARY WHERE THE RESULT OF THE QUERY IS OBTAINED USING THE KEY: result
    """
    prop = ""
    union = ""
    # print "\nCLUSTER SIZE: {}".format(len(g_cluster))

    for uri in properties:
        prop += " <{}>".format(uri.strip())

    for x in range(0, len(g_cluster)):
        if limit_resources != 0 and x > limit_resources:
            break
        if x > 0:
            append = "UNION"
        else:
            append = ""
        union += """ {}
        {{
            bind({} as ?resource)
            graph ?dataset {{ ?resource ?property ?value . }}
        }}""".format(append, g_cluster[x])

    if distinct_values is True:
        select = '?dataset ?value (count(distinct ?resource) as ?count)'
        group_by = 'group by ?value ?dataset order by desc(?count)'
    else:
        select = '*'
        group_by = ''

    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX bdb: <http://vocabularies.bridgedb.org/ops#>
    PREFIX dataset: <http://risis.eu/dataset/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX ll: <http://risis.eu/alignment/predicate/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT {}
    {{
        values ?property {{{} }}
        {}
    }} {} """.format(select, prop, union, group_by)

    # print query
    response = sparql2matrix(query)
    if display is True:
        Qry.display_matrix(response, spacing=50, is_activated=True)
    return response


def cluster_values_plus_old(rq_uri, g_cluster, properties, distinct_values=True, display=False, limit_resources=0):

    """
    :param rq_uri CLUSTER RESEARCH QUESTION
    :param g_cluster: CLUSTER GRAP
    :param properties:
    :param distinct_values: USED IN SPARQL QUERY TO COUNT DISTINCT OR NOT
    :param display: display the matrix as a table
    :param limit_resources: LIMITING THE NUMBER OF RESOURCES TO INCLUDE
    """

    prop = ""
    union = ""
    # print "\nCLUSTER SIZE: {}".format(len(g_cluster))

    for uri in properties:
        prop += " <{}>".format(uri.strip())

    for x in range(0, len(g_cluster)):
        if limit_resources != 0 and x > limit_resources:
            break
        if x > 0:
            append = "UNION"
        else:
            append = ""
        union += """ {}
        {{
            bind({} as ?resource)
            graph ?dataset {{ ?resource ?property ?value . }}
        }}""".format(append, g_cluster[x])

    if distinct_values is True:
        select = '?dataset ?value (count(distinct ?resource) as ?count)'
        group_by = 'group by ?value ?dataset order by desc(?count)'
    else:
        select = '?dataset ?resource (GROUP_CONCAT(?property; SEPARATOR=" | ") ' \
                 'as ?properties) (concat("[", ?temp ,"]") as ?values) (GROUP_CONCAT(?value; SEPARATOR="] [") as ?temp)'
        group_by = 'group by ?dataset ?resource order by ?dataset ?resource '

    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX bdb: <http://vocabularies.bridgedb.org/ops#>
    PREFIX dataset: <http://risis.eu/dataset/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX ll: <http://risis.eu/alignment/predicate/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT {}
    {{
        values ?property {{{} }}
        {}
        {{
            graph <{}>
            {{
                ?idea   ll:selected ?dataset .
                ?dataset a <http://risis.eu/class/Dataset> ;
            }}
        }}
    }} {} """.format(select, prop, union, rq_uri, group_by)

    # print query
    response = sparql2matrix(query)
    if display is True:
        Qry.display_matrix(response, spacing=50, is_activated=True)
    return response


def cluster_values_plus(rq_uri, g_cluster, targets, distinct_values=True, display=False, limit_resources=250):

    """
    :param rq_uri: CLUSTER RESEARCH QUESTION
    :param g_cluster: CLUSTER GRAP
    :param targets: CLUSTER TARGETS
    :param distinct_values: USED IN SPARQL QUERY TO COUNT DISTINCT OR NOT
    :param display: display the matrix as a table
    :param limit_resources: LIMITING THE NUMBER OF RESOURCES TO INCLUDE
    """

    # print "\nCLUSTER SIZE: {}".format(len(g_cluster))

    if (limit_resources > 0) and (len(g_cluster) > limit_resources):
        query_body = Ut.get_resource_value(g_cluster[0:limit_resources], targets)
    else:
        query_body = Ut.get_resource_value(g_cluster, targets)

    if distinct_values is True:
        select = '?dataset ?value (count(distinct ?resource) as ?count)'
        group_by = 'group by ?value ?dataset order by desc(?count)'
    else:
        select = '?dataset ?resource (GROUP_CONCAT(?property; SEPARATOR=" | ") ' \
                 'as ?properties) (concat("[", ?temp ,"]") as ?values) (GROUP_CONCAT(?value; SEPARATOR="] [") as ?temp)'
        group_by = 'group by ?dataset ?resource order by ?dataset ?resource '

    if rq_uri:
        query_rq = """
        {{
            graph <{}>
            {{
                ?idea   ll:selected ?dataset .
                ?dataset a <http://risis.eu/class/Dataset> ;
            }}
        }}
        """.format(rq_uri)
    else:
        query_rq = ''

    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX bdb: <http://vocabularies.bridgedb.org/ops#>
    PREFIX dataset: <http://risis.eu/dataset/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX ll: <http://risis.eu/alignment/predicate/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT {}
    {{
        {}
        {}
    }} {} """.format(select, query_body, query_rq, group_by)

    # print query
    response = sparql2matrix(query)
    # Qry.display_matrix(response, spacing=50, is_activated=True)
    # exit()
    if display is True:
        Qry.display_matrix(response, spacing=50, is_activated=True)
    return response


def linkset_from_cluster():

    query = """
    # DATASETS
    {{
        # CLUSTER
        GRAPH <{}>
        {{
            
        }}
    }}
    """
    print query


# WORKING ONE
def cluster_links(graph, limit=1000):

    count = 0
    matrix_size = 240
    clusters = dict()
    root = dict()

    # DOWNLOAD THE GRAPH
    print "\n0. DOWNLOADING THE GRAPH"
    response = Exp.export_alignment(graph, limit=limit)
    links = response['result']
    # print links

    # LOAD THE GRAPH3
    print "1. LOADING THE GRAPH"
    g = rdflib.Graph()
    g.parse(data=links, format="turtle")
    # g = [
    #     ("<http://grid.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://orgref.2>"),
    #     ("<http://leiden.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://grid.2>"),
    #     ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://orgreg.2>"),
    #     ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/sameAs>", "<http://h2020.2> "),
    #     ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://eter.2>"),
    #     ("<http://eter.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://leiden.2>"),
    # ]
    #
    # g = [
    #     ("<http://grid.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://orgref.2>"),
    #     ("<http://eter.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://leiden.2>"),
    #     ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/sameAs>", "<http://h2020.2> "),
    #     ("<http://leiden.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://grid.2>"),
    #     ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://orgreg.2>"),
    #     ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/sameAs>", "<http://eter.2>")]

    # g = [
    #     ("<http://risis.eu/leidenRanking_2015/resource/884>", "<http://risis.eu/alignment/predicate/sameAs>",
    #      "<http://www.grid.ac/institutes/grid.10493.3f>"),
    #     ("<http://risis.eu/leidenRanking_2015/resource/884>", "<http://risis.eu/alignment/predicate/sameAs>",
    #      "<http://risis.eu/eter_2014/resource/DE0056>"),
    #     ("<http://www.grid.ac/institutes/grid.10493.3f> ", "<http://risis.eu/alignment/predicate/sameAs>",
    #      "<http://risis.eu/eter_2014/resource/DE0056> ") ]

    def merge_matrices(parent, pop_parent):

        # COPYING LESSER MATRIX TO BIGGER MATRIX

        index = parent[St.row]
        pop_row = pop_parent[St.row]
        cur_mx = parent[St.matrix]
        pop_mx = pop_parent[St.matrix]

        # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
        # print "\tADD VALUE: {}".format(position_add)

        # COPY MATRIX
        # print "\tPOP HEADER: {}".format(pop_mx[0][:])
        for row in range(1, pop_row):

            # ADD HEADER IF NOT ALREADY IN
            # print "\tCURRENT HEADER ADDED: {}".format(cur_mx[0:])
            if pop_mx[row][0] not in cur_mx[0:]:
                pop_item_row = pop_mx[row][0]
                cur_mx[index][0] = pop_item_row
                cur_mx[0][index] = pop_item_row
                index += 1
                parent[St.row] = index
                # print "\tHEADER ADDED: {}".format(pop_item_row)

                # FOR THAT HEADER, COPY THE SUB-MATRIX
                for col in range(1, pop_row):

                    # THE HEADER ARE ALREADY IN THERE
                    if pop_mx[row][col] != 0:
                        # find header in current matrix
                        for col_item in range(1, len(cur_mx[1:-1])):
                            if cur_mx[0][col_item] == pop_mx[0][col]:
                                # print "\tIN2 ({}, {})".format(index - 1, col_item)
                                cur_mx[index - 1][col_item] = 1

    def cluster_helper(counter):

        counter += 1
        # parent = None
        # child_1 = subject.n3().strip()
        # child_2 = obj.n3().strip()
        child_1 = subject.strip()
        child_2 = obj.strip()

        # DATE CREATION
        the_date = "{}".format(datetime.datetime.today().strftime(_format))

        # CHECK WHETHER A CHILD HAS A PARENT
        has_parent_1 = True if child_1 in root else False
        has_parent_2 = True if child_2 in root else False
        # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

        # 1. START BOTH CHILD ARE ORPHANS
        if has_parent_1 is False and has_parent_2 is False:

            # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            # GENERATE THE PARENT
            hash_value = hash(the_date + str(count) + graph)
            parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                hash_value).startswith("-") \
                else "P{}".format(hash_value)

            # ASSIGN A PARENT TO BOTH CHILD
            root[child_1] = parent
            root[child_2] = parent

            # CREATE A CLUSTER
            if parent not in clusters:
                # MATRIX
                mx = matrix(matrix_size, matrix_size)
                # ROW
                mx[0][1] = child_1
                mx[0][2] = child_2

                # COLUMNS
                mx[1][0] = child_1
                mx[2][0] = child_2

                # RELATION
                # mx[1][2] = 1
                mx[2][1] = 1
                # mxd[(2, 1)] = 1

                clusters[parent] = {St.children: [child_1, child_2], St.matrix: mx, St.row: 3}
                clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

            # print "\tPOSITION: {}".format(3)
            # print "\tIT WILL BE PRINTED AT: ({}, {})".format(2, 1)

        # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
        elif has_parent_1 is True and has_parent_2 is True:

            # 2.1 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            if root[child_1] == root[child_2]:
                # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
                # print "\nSAME PARENTS {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
                cur_mx = clusters[root[child_1]][St.matrix]

                row_1 = 0
                row_2 = 0

                # FIND ROW
                # row_1 = clusters[root[child_1]][St.row]
                for row in range(1, clusters[root[child_1]][St.row]):
                    if cur_mx[row][0] == child_1:
                        row_1 = row

                for col in range(1, clusters[root[child_1]][St.row]):
                    if cur_mx[0][col] == child_2:
                        row_2 = col

                # row_2 = clusters[root[child_2]][St.row]

                # print "\tPOSITIONS: {} | {}".format(row_2, row_1)
                cur_mx[row_2][row_1] = 1
                clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1, child_2)

                # COPY THE SUB-MATRIX

                # for col in range(1, row_1):
                #     if cur_mx[0][col] == child_2:
                #         print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                #         print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
                #         cur_mx[row_1 - 1][col] = 1

                # continue
                return counter

            # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
            # fFETCHING THE RESOURCES IN THE CLUSTER (CHILDREN)
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            children_1 = (clusters[root[child_1]])[St.children]
            children_2 = (clusters[root[child_2]])[St.children]

            # 2.2 CHOOSE A PARENT
            if len(children_1) >= len(children_2):
                # print "\tPARENT 1"
                parent = root[child_1]
                pop_parent = root[child_2]
                # root[child_2] = parent

            else:
                # print "\tPARENT 2"
                parent = root[child_2]
                pop_parent = root[child_1]
                # root[child_1] = parent

            # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
            for offspring in clusters[pop_parent][St.children]:
                root[offspring] = parent
                clusters[parent][St.children] += [offspring]

            # MERGE CURRENT WITH LESSER (CHILDREN) MATRICES, ANNOTATE AND POOP LESSER (CHILDREN) MATRICES
            # print '1\n', clusters[parent]
            merge_matrices(clusters[parent], clusters[pop_parent])
            # print '2\n', clusters[parent]
            clusters[parent][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
            cluster_helper(count)
            # cluster_helper(count)

            # COPYING LESSER MATRIX TO BIGGER MATRIX
            # index = clusters[parent][St.row]
            # pop_row = clusters[pop_parent][St.row]
            # cur_mx = clusters[parent][St.matrix]
            # pop_mx = clusters[pop_parent][St.matrix]
            # # position_add = clusters[parent][St.row] - 1
            #
            # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
            # # print "\tADD VALUE: {}".format(position_add)
            #
            # # # ADD HEADER
            # # for x in range(1, pop_index):
            # #     cur_mx[0][index - 1 + x] = pop_mx[0][x]
            # #     cur_mx[index - 1 + x][0] = pop_mx[0][x]
            # #     clusters[parent][St.row] += 1
            #
            # # COPY MATRIX
            # print "\tPOP HEADER: {}".format(pop_mx[0][:])
            # for row in range(1, pop_row):
            #
            #     # ADD HEADER IF NOT ALREADY IN
            #     # print "\tCURREENT HEADER ADDED: {}".format(cur_mx[0:])
            #     if pop_mx[row][0] not in cur_mx[0:]:
            #         pop_item_row = pop_mx[row][0]
            #         cur_mx[index][0] = pop_item_row
            #         cur_mx[0][index] = pop_item_row
            #         index += 1
            #         clusters[parent][St.row] = index
            #         print "\tHEADER ADDED: {}".format(pop_item_row)
            #
            #
            #         # FOR THAT HEADER, COPY THE SUB-MATRIX
            #         for col in range(1, pop_row):
            #
            #             # THE HEADER IS NOT IN
            #             if pop_mx[row][col] != 0 and pop_mx[row][0] not in cur_mx[1:-1]:
            #                 print "\tIN ({}, {})".format(index-1, col )
            #                 # index += 1
            #                 # clusters[parent][St.row] = index
            #
            #             # THE HEADER ARE ALREADY IN THERE
            #             if pop_mx[row][col] != 0:
            #                 # find header in current matrix
            #                 for col_item in range(1, len(cur_mx[1:-1])):
            #                     if cur_mx[0][col_item] == pop_mx[0][col]:
            #                         print "\tIN2 ({}, {})".format(index-1, col_item)
            # cur_mx[row + position_add][col + position_add] = pop_mx[row][col]

            # cur_mx[0][position_add+ row] = pop_mx[row][0]

            # cur_mx[y + position_add][x + position_add] = pop_mx[y][x]

            # POP THE PARENT WITH THE LESSER CHILD

            clusters[parent][St.annotate] += clusters[pop_parent][St.annotate]
            clusters.pop(pop_parent)

        elif has_parent_1 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_1]
            root[child_2] = parent
            clusters[parent][St.children] += [child_2]
            # print "\t>>> {} is in root {}".format(child_2, child_2 in root)

            cur_mx = clusters[parent][St.matrix]
            row_1 = clusters[parent][St.row]

            # ADD HEADER
            cur_mx[row_1][0] = child_2
            cur_mx[0][row_1] = child_2

            # INCREMENT POSITION
            row_1 += 1
            # print "\tPOSITION: {}".format(row_1)
            clusters[parent][St.row] = row_1

            # COPY MATRIX
            for col in range(1, row_1):
                # print cur_mx[0][x], child_1
                if cur_mx[0][col] == child_1:
                    # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                    # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
                    # cur_mx[position_1 - 1][x] = 1
                    cur_mx[row_1 - 1][col] = 1
                    clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                        child_1, child_2)

        elif has_parent_2 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_2]
            root[child_1] = parent
            clusters[parent][St.children] += [child_1]
            # print "\t>>> {} is in root {}".format(child_1, child_1 in root)

            cur_mx = clusters[parent][St.matrix]
            row_2 = clusters[parent][St.row]

            # ADD HEADER
            # print row_2
            cur_mx[row_2][0] = child_1
            cur_mx[0][row_2] = child_1

            # INCREMENT POSITION
            row_2 += 1
            # print "\tPOSITION: {}".format(row_2)
            clusters[parent][St.row] = row_2

            # COPY MATRIX
            for col in range(1, row_2):
                # print cur_mx[0][x], child_1
                if cur_mx[0][col] == child_2:
                    # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                    # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_2 - 1, col)
                    # cur_mx[position_2 - 1][x] = 1
                    cur_mx[row_2 - 1][col] = 1
                    clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                        child_2, child_1)

        return counter

    print "2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(g))

    standard = 10
    check = 1
    iteration = 1
    for subject, predicate, obj in g:
        print "\tRESOURCE {:>4}: {} {}".format(count, subject.n3(), obj)

        count = cluster_helper(count)
        if iteration == check:
            print "1- ", count
            check += standard
        iteration += 1

    print "3. NUMBER OF CLUSTER FOUND: {}".format(len(clusters))
    return clusters


# QUERY TO HELP DISAMBIGUATING A NETWORK OF RESOURCES
def disambiguate_network(linkset, resource_list, output=True):

    # GATHER SOME DATA ABOUT THE LINKSET
    metadata_query = """
    PREFIX ll:  <{1}>
    SELECT ?target ?aligns
    {{
        <{0}> ll:hasAlignmentTarget ?alignmentTarget .
        ?alignmentTarget
            ll:hasTarget 	?target ;
            ll:aligns		?aligns .
    }} order by ?alignmentTarget
    """.format(linkset, Ns.alivocab)
    # print metadata_query
    uri_size = 0

    response = Qry.sparql_xml_to_matrix(metadata_query)
    result = response[St.result]
    # print result

    if result:
        dataset = ""
        bind = ""
        property_or = ""
        dataset_count = 0
        resources = ""
        for resource in resource_list:
            use = "<{}>".format(resource) if Ut.is_nt_format(resource) is not True else resource
            resources += "\n\t\t{}".format(use)
            if len(resource) > uri_size:
                uri_size = len(resource)

        for i in range(1, len(result)):
            if dataset != result[i][0]:
                dataset_count += 1
                union = "UNION " if dataset_count > 1 else ""
                dataset = result[i][0]
                bind += """\n\tBIND(IRI("{}") as ?dataset_{})""".format(
                    dataset, str(dataset_count))

                prop_1 = "<{}>".format(result[i][1]) if Ut.is_nt_format(result[i][1]) is not True else result[i][1]
                property_or += "\n\t{}{{\n\t\tGRAPH ?dataset_{}\n\t\t{{\n\t\t\t?subject {}".format(
                    union, dataset_count, prop_1)
                for j in range(i + 1, len(result)):
                    if dataset == result[i][0]:
                        prop_2 = "<{}>".format(result[i][1]) if Ut.is_nt_format(result[i][1]) is not True \
                            else result[i][1]
                        property_or += "\n\t\t\t\t| {}".format(prop_2)
                        i = j
                property_or += "  ?object .\n\t\t}\n\t}"

        final_query = "SELECT DISTINCT ?subject ?object\n{{\n\tVALUES ?subject {{{}\n\t}}{}{}\n}}".format(
            resources, bind, property_or)
        # print final_query
        response = Qry.sparql_xml_to_matrix(final_query)

        if output is False:
            return response[St.result]

        return Qry.display_matrix(response, spacing=uri_size, output=output, line_feed='.', is_activated=True)

    print "\t>>> NO RESULT FOR THE QUERY BECAUSE NO METADATA COULD BE EXTRACTED FOR THE PROVIDED LINKSET..."
    print metadata_query
    return "NO RESULT FOR THE QUERY..."


# QUERY TO HELP DISAMBIGUATING A NETWORK OF RESOURCES
def disambiguate_network_2(lookup_resource_list, targets, output=True):

    # GATHER SOME DATA ABOUT THE LINKSET

    # print metadata_query
    uri_size = 0
    dataset = ""
    bind = ""
    property_or = ""
    dataset_count = 0
    resources = ""

    for resource in lookup_resource_list:
        use = "<{}>".format(resource) if Ut.is_nt_format(resource) is not True else resource
        resources += "\n\t\t{}".format(use)
        if len(resource) > uri_size:
            uri_size = len(resource)

    for i in range(len(targets)):
        if dataset != targets[i][St.graph]:
            dataset_count += 1
            union = "UNION " if dataset_count > 1 else ""
            dataset = targets[i][St.graph]
            bind += """\n\tBIND(IRI("{}") as ?dataset_{})""".format(
                dataset, str(dataset_count))
            data = targets[i][St.data]

            for dt_dic in data:
                properties = dt_dic[St.properties]
                for index in range(len(properties)):
                    if index == 0:
                        prop_1 = "<{}>".format(properties[index]) if Ut.is_nt_format(properties[index]) is not True \
                            else properties[index]
                        property_or += "\n\t{}{{\n\t\tGRAPH ?dataset_{}\n\t\t{{\n\t\t\t?subject {}".format(
                            union, dataset_count, prop_1)
                    else:

                        prop_2 = "<{}>".format(properties[index]) if Ut.is_nt_format(properties[index]) is not True \
                            else properties[index]
                        property_or += "\n\t\t\t\t| {}".format(prop_2)

            property_or += "  ?object .\n\t\t}\n\t}"

    final_query = "SELECT DISTINCT ?subject ?object\n{{\n\tVALUES ?subject {{{}\n\t}}{}{}\n}}".format(
        resources, bind, property_or)
    # print final_query
    response = Qry.sparql_xml_to_matrix(final_query)
    # print "RESPONSE", response
    if output is False:
        return response[St.result]

    return Qry.display_matrix(response, spacing=uri_size, output=output, line_feed='.', is_activated=True)

    # print "\t>>> NO RESULT FOR THE QUERY BECAUSE NO METADATA COULD BE EXTRACTED FOR THE PROVIDED LINKSET..."
    # print metadata_query
    # return "NO RESULT FOR THE QUERY..."


def links_clustering_matrix(graph, limit=1000):

    count = 0
    clusters = dict()

    # ROOT = KEY:CHILD VALUE:PARENT
    root = dict()

    # DOWNLOAD THE GRAPH
    print "\n0. DOWNLOADING THE GRAPH FROM THE TRIPLE STORE"
    response = Exp.export_alignment(graph, limit=limit)
    links = response['result']

    # LOAD THE GRAPH
    print "1. LOADING THE GRAPH USING RDFLIB"
    g = rdflib.Graph()
    g.parse(data=links, format="turtle")

    # g = [
    #     ("<http://grid.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgref.2>"),
    #     ("<http://leiden.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://grid.2>"),
    #     ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgreg.2>"),
    #     ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://h2020.2> "),
    #     ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://eter.2>"),
    #     ("<http://eter.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://leiden.2>"),
    # ]

    # g = [
    #     ( "<http://grid.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgref.2>"),
    #     ( "<http://eter.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://leiden.2>"),
    #     ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://h2020.2> "),
    #     ( "<http://leiden.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://grid.2>"),
    #     ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgreg.2>"),
    #     ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://eter.2>"),
    # ]

    # g = [
    #     ("<http://risis.eu/leidenRanking_2015/resource/884>", "<http://risis.eu/alignment/predicate/SAMEAS>",
    #      "<http://www.grid.ac/institutes/grid.10493.3f>"),
    #     ("<http://risis.eu/leidenRanking_2015/resource/884>", "<http://risis.eu/alignment/predicate/SAMEAS>",
    #      "<http://risis.eu/eter_2014/resource/DE0056>"),
    #     ("<http://www.grid.ac/institutes/grid.10493.3f> ", "<http://risis.eu/alignment/predicate/SAMEAS>",
    #      "<http://risis.eu/eter_2014/resource/DE0056> ") ]

    def merge_d_matrices(parent, pop_parent):

        # COPYING LESSER MATRIX TO BIGGER MATRIX

        index = parent[St.row]
        pop_row = pop_parent[St.row]
        cur_mxd = parent[St.matrix_d]
        pop_mxd = pop_parent[St.matrix_d]
        # position_add = clusters[parent][St.row] - 1

        # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
        # print "\tADD VALUE: {}".format(position_add)

        # COPY MATRIX
        # print "\tPOP HEADER: {}".format(pop_mx[0][:])
        for row in range(1, pop_row):

            # ADD HEADER IF NOT ALREADY IN
            # print "\tCURRENT HEADER ADDED: {}".format(cur_mx[0:])
            if pop_mxd[(row, 0)] not in cur_mxd:
                pop_item_row = pop_mxd[(row, 0)]
                cur_mxd[(index, 0)] = pop_item_row
                cur_mxd[(0, index)] = pop_item_row
                index += 1
                parent[St.row] = index
                # print "\tHEADER ADDED: {}".format(pop_item_row)

                # FOR THAT HEADER, COPY THE SUB-MATRIX
                for col in range(1, pop_row):

                    # THE HEADER ARE ALREADY IN THERE
                    if (row, col) in pop_mxd and pop_mxd[(row, col)] != 0:
                        # find header in current matrix
                        for col_item in range(1, len(cur_mxd)):
                            if (0, col_item) in cur_mxd and (0, col) in pop_mxd and \
                                            cur_mxd[(0, col_item)] == pop_mxd[(0, col)]:
                                # print "\tIN2 ({}, {})".format(index - 1, col_item)
                                cur_mxd[(index - 1, col_item)] = 1

    def cluster_helper(counter, annotate=False):

        counter += 1
        child_1 = subject.n3().strip()
        child_2 = obj.n3().strip()
        # child_1 = subject.strip()
        # child_2 = obj.strip()

        # DATE CREATION
        # date = "{}".format(datetime.datetime.today().strftime(_format))

        # CHECK WHETHER A CHILD HAS A PARENT
        has_parent_1 = True if child_1 in root else False
        has_parent_2 = True if child_2 in root else False
        # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

        # 1. START BOTH CHILD ARE ORPHANS
        if has_parent_1 is False and has_parent_2 is False:

            # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            # GENERATE THE PARENT
            # hash_value = hash(date + str(count) + graph)
            hash_value = hash(child_1 + child_2 + graph)
            parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                hash_value).startswith("-") \
                else "P{}".format(hash_value)

            # ASSIGN A PARENT TO BOTH CHILD
            root[child_1] = parent
            root[child_2] = parent

            # CREATE A CLUSTER
            if parent not in clusters:
                # MATRIX
                # mx = matrix(matrix_size, matrix_size)
                mxd = dict()
                # ROW
                # mx[0][1] = child_1
                # mx[0][2] = child_2

                mxd[(0, 1)] = child_1
                mxd[(0, 2)] = child_2

                # COLUMNS
                # mx[1][0] = child_1
                # mx[2][0] = child_2

                mxd[(1, 0)] = child_1
                mxd[(2, 0)] = child_2

                # RELATION
                # mx[1][2] = 1
                # mx[2][1] = 1
                mxd[(2, 1)] = 1

                clusters[parent] = {St.children: [child_1, child_2], St.matrix: None, St.row: 3, St.matrix_d: mxd}
                if annotate:
                    clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

            # print "\tPOSITION: {}".format(3)
            # print "\tIT WILL BE PRINTED AT: ({}, {})".format(2, 1)

        # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
        elif has_parent_1 is True and has_parent_2 is True:

            # 2.1 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            if root[child_1] == root[child_2]:
                # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
                # print "\nSAME PARENTS {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
                # cur_mx = clusters[root[child_1]][St.matrix]
                cur_mxd = clusters[root[child_1]][St.matrix_d]

                row_1 = 0
                row_2 = 0

                # FIND ROW
                # row_1 = clusters[root[child_1]][St.row]
                # for row in range(1, clusters[root[child_1]][St.row]):
                #     if cur_mx[row][0] == child_1:
                #         row_1 = row
                #
                # for col in range(1, clusters[root[child_1]][St.row]):
                #     if cur_mx[0][col] == child_2:
                #         row_2 = col

                for row in range(1, clusters[root[child_1]][St.row]):
                    if (row, 0) in cur_mxd and cur_mxd[(row, 0)] == child_1:
                        row_1 = row

                for col in range(1, clusters[root[child_1]][St.row]):
                    if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                        row_2 = col

                # row_2 = clusters[root[child_2]][St.row]

                # print "\tPOSITIONS: {} | {}".format(row_2, row_1)
                # cur_mx[row_2][row_1] = 1
                cur_mxd[(row_2, row_1)] = 1

                if annotate:
                    clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1, child_2)

                # COPY THE SUB-MATRIX
                # for col in range(1, row_1):
                #     if cur_mx[0][col] == child_2:
                #         print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                #         print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
                #         cur_mx[row_1 - 1][col] = 1

                # continue
                return counter

            # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
            # fFETCHING THE RESOURCES IN THE CLUSTER (CHILDREN)
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            children_1 = (clusters[root[child_1]])[St.children]
            children_2 = (clusters[root[child_2]])[St.children]

            # 2.2 CHOOSE A PARENT
            if len(children_1) >= len(children_2):
                # print "\tPARENT 1"
                parent = root[child_1]
                pop_parent = root[child_2]
                # root[child_2] = parent

            else:
                # print "\tPARENT 2"
                parent = root[child_2]
                pop_parent = root[child_1]
                # root[child_1] = parent

            # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
            for offspring in clusters[pop_parent][St.children]:
                root[offspring] = parent
                clusters[parent][St.children] += [offspring]

            # MERGE CURRENT WITH LESSER (CHILDREN) MATRICES, ANNOTATE AND POOP LESSER (CHILDREN) MATRICES
            merge_d_matrices(clusters[parent], clusters[pop_parent])

            if annotate:
                clusters[parent][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
            cluster_helper(count)
            # cluster_helper(count)

            # COPYING LESSER MATRIX TO BIGGER MATRIX
            # index = clusters[parent][St.row]
            # pop_row = clusters[pop_parent][St.row]
            # cur_mx = clusters[parent][St.matrix]
            # pop_mx = clusters[pop_parent][St.matrix]
            # # position_add = clusters[parent][St.row] - 1
            #
            # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
            # # print "\tADD VALUE: {}".format(position_add)
            #
            # # # ADD HEADER
            # # for x in range(1, pop_index):
            # #     cur_mx[0][index - 1 + x] = pop_mx[0][x]
            # #     cur_mx[index - 1 + x][0] = pop_mx[0][x]
            # #     clusters[parent][St.row] += 1
            #
            # # COPY MATRIX
            # print "\tPOP HEADER: {}".format(pop_mx[0][:])
            # for row in range(1, pop_row):
            #
            #     # ADD HEADER IF NOT ALREADY IN
            #     # print "\tCURREENT HEADER ADDED: {}".format(cur_mx[0:])
            #     if pop_mx[row][0] not in cur_mx[0:]:
            #         pop_item_row = pop_mx[row][0]
            #         cur_mx[index][0] = pop_item_row
            #         cur_mx[0][index] = pop_item_row
            #         index += 1
            #         clusters[parent][St.row] = index
            #         print "\tHEADER ADDED: {}".format(pop_item_row)
            #
            #
            #         # FOR THAT HEADER, COPY THE SUB-MATRIX
            #         for col in range(1, pop_row):
            #
            #             # THE HEADER IS NOT IN
            #             if pop_mx[row][col] != 0 and pop_mx[row][0] not in cur_mx[1:-1]:
            #                 print "\tIN ({}, {})".format(index-1, col )
            #                 # index += 1
            #                 # clusters[parent][St.row] = index
            #
            #             # THE HEADER ARE ALREADY IN THERE
            #             if pop_mx[row][col] != 0:
            #                 # find header in current matrix
            #                 for col_item in range(1, len(cur_mx[1:-1])):
            #                     if cur_mx[0][col_item] == pop_mx[0][col]:
            #                         print "\tIN2 ({}, {})".format(index-1, col_item)
            # cur_mx[row + position_add][col + position_add] = pop_mx[row][col]

            # cur_mx[0][position_add+ row] = pop_mx[row][0]

            # cur_mx[y + position_add][x + position_add] = pop_mx[y][x]

            # POP THE PARENT WITH THE LESSER CHILD

            if annotate:
                clusters[parent][St.annotate] += clusters[pop_parent][St.annotate]
            clusters.pop(pop_parent)

        # 3. ONE CHILD [CHILD 1] HAVE A PARENT OF HIS OWN
        elif has_parent_1 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_1]
            root[child_2] = parent
            clusters[parent][St.children] += [child_2]
            # print "\t>>> {} is in root {}".format(child_2, child_2 in root)

            # cur_mx = clusters[parent][St.matrix]
            cur_mxd = clusters[parent][St.matrix_d]
            row_1 = clusters[parent][St.row]

            # ADD HEADER
            # cur_mx[row_1][0] = child_2
            # cur_mx[0][row_1] = child_2

            cur_mxd[(row_1, 0)] = child_2
            cur_mxd[(0, row_1)] = child_2

            # INCREMENT POSITION
            row_1 += 1
            # print "\tPOSITION: {}".format(row_1)
            clusters[parent][St.row] = row_1

            # COPY MATRIX
            # for col in range(1, row_1):
            #     # print cur_mx[0][x], child_1
            #     if cur_mx[0][col] == child_1:
            #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
            #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
            #         # cur_mx[position_1 - 1][x] = 1
            #         cur_mx[row_1 - 1][col] = 1
            #         clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
            #             child_1, child_2)

            for col in range(1, row_1):
                if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_1:
                    cur_mxd[(row_1 - 1, col)] = 1
                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                            child_1, child_2)

        # 4. ONE CHILD [CHILD 2] HAVE A PARENT OF HIS OWN
        elif has_parent_2 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_2]
            root[child_1] = parent
            clusters[parent][St.children] += [child_1]
            # print "\t>>> {} is in root {}".format(child_1, child_1 in root)

            # cur_mx = clusters[parent][St.matrix]
            cur_mxd = clusters[parent][St.matrix_d]
            row_2 = clusters[parent][St.row]

            # ADD HEADER
            # print row_2
            # cur_mx[row_2][0] = child_1
            # cur_mx[0][row_2] = child_1

            cur_mxd[(row_2, 0)] = child_1
            cur_mxd[(0, row_2)] = child_1

            # INCREMENT POSITION
            row_2 += 1
            # print "\tPOSITION: {}".format(row_2)
            clusters[parent][St.row] = row_2

            # COPY MATRIX
            # for col in range(1, row_2):
            #     # print cur_mx[0][x], child_1
            #     if cur_mx[0][col] == child_2:
            #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
            #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_2 - 1, col)
            #         # cur_mx[position_2 - 1][x] = 1
            #         cur_mx[row_2 - 1][col] = 1
            #         clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
            #             child_2, child_1)

            for col in range(1, row_2):
                if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                    cur_mxd[(row_2 - 1, col)] = 1
                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                            child_2, child_1)

        return counter

    print "2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(g))

    standard = 50000
    check = 1
    iteration = 1

    for subject, predicate, obj in g:

        count = cluster_helper(count, annotate=False)
        if iteration == check:
            print "\tRESOURCE {:>10}:   {} {}".format(count, subject.n3(), obj)
            check += standard
        iteration += 1

    print "3. NUMBER OF CLUSTER FOUND: {}".format(len(clusters))
    return clusters


def resource_stat(alignment, dataset, resource_type=None, output=True, activated=False):

    # OUTPUT FALSE RETURNS THE MATRIX WHILE OUTPUT TRUE RETURNS THE DISPLAY MATRIX IN A TABLE FORMAT

    print "\nCOMPUTING STATISTICS ON ALIGNMENT"
    if activated is False:
        print "\tTHE FUNCTION I NOT ACTIVATED"
        return [None, None]
    print "\tSTATISTICS FOR {}".format(alignment)
    message = "\tSTATISTICS FOR {}\n".format(alignment)

    # STATS ON DISCOVERED RESOURCES
    matched = dict()
    matched_resp = resources_matched(alignment, dataset, resource_type=resource_type, matched=True, stat=True)
    matched_res = matched_resp["result"]
    for r in range(1, len(matched_res)):
        for c in range(len(matched_res[r])):
            matched[matched_res[0][c]] = matched_res[r][c]

    print ">>> DISCOVERED"
    message += ">>> DISCOVERED\n"
    for key, value in matched.items():
        print "\t{:21} : {}".format(key, value)
        message += "\t{:21} : {}\n".format(key, value)

    # STATS ON RESOURCES NOT DISCOVERED
    lost = dict()
    lost_rep = resources_matched(alignment, dataset, resource_type=resource_type, matched=False, stat=True)
    lost_res = lost_rep["result"]
    for r in range(1, len(lost_res)):
        for c in range(len(lost_res[r])):
            lost[lost_res[0][c]] = lost_res[r][c]

    lost_resources = resources_matched(alignment, dataset, resource_type=resource_type, matched=False, stat=False)
    lost_result = []
    for i in range(1, len(lost_resources["result"])):
        lost_result += [lost_resources["result"][i][0]]

    lost["Resources not matched"] = disambiguate_network(alignment, lost_result, output=output)
    # print matched
    # print lost
    # print [matched, lost]

    print ">>> NOT DISCOVERED"
    message += ">>> NOT DISCOVERED\n"
    for key, value in lost.items():
        print "\t{:21} : {}".format(key, value)
        message += "\t{:21} : {}\n".format(key, value)

    return [matched, lost, message]


def resources_matched(alignment, dataset, resource_type=None, matched=True, stat=True):

    # ALIGNMENT                 : IS THE SET OF CORRESPONDENCES
    # DATASET                   : THE DATASET UNDER SCRUTINY
    # RESOURCE TYPE             : IF NOT PROVIDED, THEN THE ANALYSIS APPLIED TO ALL RESOURCES MATCHED/NO FOUND
    # STAT SET TO [TRUE]        : PROVIDES STATISTICS ON THE RESOURCES
    # MATCHED SET TO [TRUE]     : ANY DISPLAYED DATA APPLIES TO THE MATCHED RESOURCES
    # MATCHED SET TO [FALSE]    : ANY DISPLAYED DATA APPLIES TO THE NOT FOUND RESOURCES

    if resource_type:
        comment_type = ""
        comment_type_opp = "#"
    else:
        comment_type = "#"
        comment_type_opp = ""

    matched_comment = ""
    term = "lost"
    if matched:
        matched_comment = "#"
        term = 'matched'

    stat_comment = ""
    stat_comment_opp = "#"
    if stat is not True:
        stat_comment = "#"
        stat_comment_opp = ""

    query = """
    {6}select (count (distinct ?subject) as ?{8}) ?total ( (?{8}/?total)*100 as ?percentage_{8})
    {7}select distinct ?subject
    {{

        {{
            select (count (distinct ?s) as ?total)
            {{
                GRAPH <{1}>
                {{
                    {2}?s a <{3}>.

                    ### ANY TRIPLE
                    {4}?s ?pred ?obj.
                }}
            }}
        }}

        {5}{{
        {5}    GRAPH <{1}>
        {5}    {{
        {5}        ### SPECIFIC TYPE OF TRIPLE
        {5}        {2}?subject a <{3}>.

        {5}        ### ANY TRIPLE
        {5}        {4}?subject ?pred ?obj.
        {5}    }}
        {5}}} MINUS

        {{
            GRAPH <{0}>
            {{
                {{ ?subject ?predicate ?object . }} UNION
                {{ ?object ?predicate ?subject . }}

                GRAPH <{1}>
                {{
                    ### SPECIFIC TYPE OF TRIPLE
                    {2}?subject a <{3}>.

                    ### ANY TRIPLE
                    {4}?subject ?pred ?obj.
                }}
            }}
        }}
    }} {6}GROUP BY ?total

    """.format(alignment, dataset, comment_type, resource_type, comment_type_opp,
               matched_comment, stat_comment, stat_comment_opp, term)
    # print query
    # print Qry.sparql_xml_to_matrix(query)
    return Qry.sparql_xml_to_matrix(query)


def links_clustering_bug(graph):

    count = 0
    clusters = dict()

    # ROOT = KEY:CHILD VALUE:PARENT
    root = dict()

    # DOWNLOAD THE GRAPH
    print "\n0. DOWNLOADING THE GRAPH FROM THE TRIPLE STORE"
    # response = Exp.export_alignment(graph, limit=limit)
    # links = response['result']
    # # print links
    #
    # # LOAD THE GRAPH
    # print "1. LOADING THE GRAPH USING RDFLIB"
    # g = rdflib.Graph()
    # g.parse(data=links, format="turtle")
    # g = [
    #     ("<http://grid.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgref.2>"),
    #     ("<http://leiden.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://grid.2>"),
    #     ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgreg.2>"),
    #     ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://h2020.2> "),
    #     ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://eter.2>"),
    #     ("<http://eter.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://leiden.2>"),
    # ]

    g = [
        ("<http://grid.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgref.2>"),
        ("<http://eter.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://leiden.2>"),
        ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://h2020.2>"),
        ("<http://leiden.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://grid.2>"),
        ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgreg.2>"),
        ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://eter.2>"),
    ]

    # g = [
    #     ("<http://risis.eu/leidenRanking_2015/resource/884>", "<http://risis.eu/alignment/predicate/SAMEAS>",
    #      "<http://www.grid.ac/institutes/grid.10493.3f>"),
    #     ("<http://risis.eu/leidenRanking_2015/resource/884>", "<http://risis.eu/alignment/predicate/SAMEAS>",
    #      "<http://risis.eu/eter_2014/resource/DE0056>"),
    #     ("<http://www.grid.ac/institutes/grid.10493.3f> ", "<http://risis.eu/alignment/predicate/SAMEAS>",
    #      "<http://risis.eu/eter_2014/resource/DE0056> ") ]

    def merge_d_matrices(parent, pop_parent):

        print "\t\t\tMERGING"

        # COPYING LESSER MATRIX TO BIGGER MATRIX

        index = parent[St.row]
        pop_row = pop_parent[St.row]
        cur_mxd = parent[St.matrix_d]
        pop_mxd = pop_parent[St.matrix_d]
        # position_add = clusters[parent][St.row] - 1

        # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
        # print "\tADD VALUE: {}".format(position_add)

        # COPY MATRIX
        # print "\tPOP HEADER: {}".format(pop_mx[0][:])
        for row in range(1, pop_row):

            # ADD HEADER IF NOT ALREADY IN
            # print "\tCURRENT HEADER ADDED: {}".format(cur_mx[0:])
            if pop_mxd[(row, 0)] not in cur_mxd:
                pop_item_row = pop_mxd[(row, 0)]
                cur_mxd[(index, 0)] = pop_item_row
                cur_mxd[(0, index)] = pop_item_row
                index += 1
                parent[St.row] = index
                # print "\tHEADER ADDED: {}".format(pop_item_row)

                # FOR THAT HEADER, COPY THE SUB-MATRIX
                for col in range(1, pop_row):

                    # THE HEADER ARE ALREADY IN THERE
                    if (row, col) in pop_mxd and pop_mxd[(row, col)] != 0:
                        # find header in current matrix
                        for col_item in range(1, len(cur_mxd)):
                            if (0, col_item) in cur_mxd and (0, col) in pop_mxd and \
                                            cur_mxd[(0, col_item)] == pop_mxd[(0, col)]:
                                # print "\tIN2 ({}, {})".format(index - 1, col_item)
                                cur_mxd[(index - 1, col_item)] = 1

    def cluster_helper(counter, annotate=False):

        counter += 1
        # child_1 = subject.n3().strip()
        # child_2 = obj.n3().strip()
        child_1 = subject.strip()
        child_2 = obj.strip()

        # DATE CREATION
        # date = "{}".format(datetime.datetime.today().strftime(_format))

        # CHECK WHETHER A CHILD HAS A PARENT
        has_parent_1 = True if child_1 in root else False
        has_parent_2 = True if child_2 in root else False
        # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

        # 1. START BOTH CHILD ARE ORPHANS
        if has_parent_1 is False and has_parent_2 is False:

            # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            # GENERATE THE PARENT
            # hash_value = hash(date + str(count) + graph)
            hash_value = hash(child_1 + child_2 + graph)
            parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                hash_value).startswith("-") \
                else "P{}".format(hash_value)

            # ASSIGN A PARENT TO BOTH CHILD
            root[child_1] = parent
            root[child_2] = parent

            # CREATE A CLUSTER
            if parent not in clusters:
                # MATRIX
                # mx = matrix(matrix_size, matrix_size)
                mxd = dict()
                # ROW
                # mx[0][1] = child_1
                # mx[0][2] = child_2

                mxd[(0, 1)] = child_1
                mxd[(0, 2)] = child_2

                # COLUMNS
                # mx[1][0] = child_1
                # mx[2][0] = child_2

                mxd[(1, 0)] = child_1
                mxd[(2, 0)] = child_2

                # RELATION
                # mx[1][2] = 1
                # mx[2][1] = 1
                mxd[(2, 1)] = 1

                clusters[parent] = {St.children: [child_1, child_2], St.matrix: None, St.row: 3, St.matrix_d: mxd}
                if annotate:
                    clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

            # print "\tPOSITION: {}".format(3)
            # print "\tIT WILL BE PRINTED AT: ({}, {})".format(2, 1)

        # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
        elif has_parent_1 is True and has_parent_2 is True:

            # 2.1 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            if root[child_1] == root[child_2]:
                # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
                # print "\nSAME PARENTS {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
                # cur_mx = clusters[root[child_1]][St.matrix]
                cur_mxd = clusters[root[child_1]][St.matrix_d]

                row_1 = 0
                row_2 = 0

                # FIND ROW
                # row_1 = clusters[root[child_1]][St.row]
                # for row in range(1, clusters[root[child_1]][St.row]):
                #     if cur_mx[row][0] == child_1:
                #         row_1 = row
                #
                # for col in range(1, clusters[root[child_1]][St.row]):
                #     if cur_mx[0][col] == child_2:
                #         row_2 = col

                for row in range(1, clusters[root[child_1]][St.row]):
                    if (row, 0) in cur_mxd and cur_mxd[(row, 0)] == child_1:
                        row_1 = row

                for col in range(1, clusters[root[child_1]][St.row]):
                    if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                        row_2 = col

                # row_2 = clusters[root[child_2]][St.row]

                # print "\tPOSITIONS: {} | {}".format(row_2, row_1)
                # cur_mx[row_2][row_1] = 1
                cur_mxd[(row_2, row_1)] = 1

                if annotate:
                    clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1, child_2)

                # COPY THE SUB-MATRIX
                # for col in range(1, row_1):
                #     if cur_mx[0][col] == child_2:
                #         print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                #         print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
                #         cur_mx[row_1 - 1][col] = 1

                # continue
                return counter

            # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
            # fFETCHING THE RESOURCES IN THE CLUSTER (CHILDREN)
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            children_1 = (clusters[root[child_1]])[St.children]
            children_2 = (clusters[root[child_2]])[St.children]

            # 2.2 CHOOSE A PARENT
            if len(children_1) >= len(children_2):
                # print "\tPARENT 1"
                parent = root[child_1]
                pop_parent = root[child_2]
                # root[child_2] = parent

            else:
                # print "\tPARENT 2"
                parent = root[child_2]
                pop_parent = root[child_1]
                # root[child_1] = parent

            # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
            for offspring in clusters[pop_parent][St.children]:
                root[offspring] = parent
                clusters[parent][St.children] += [offspring]

            # MERGE CURRENT WITH LESSER (CHILDREN) MATRICES, ANNOTATE AND POOP LESSER (CHILDREN) MATRICES
            merge_d_matrices(clusters[parent], clusters[pop_parent])

            if annotate:
                clusters[parent][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
            cluster_helper(count)
            # cluster_helper(count)

            # COPYING LESSER MATRIX TO BIGGER MATRIX
            # index = clusters[parent][St.row]
            # pop_row = clusters[pop_parent][St.row]
            # cur_mx = clusters[parent][St.matrix]
            # pop_mx = clusters[pop_parent][St.matrix]
            # # position_add = clusters[parent][St.row] - 1
            #
            # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
            # # print "\tADD VALUE: {}".format(position_add)
            #
            # # # ADD HEADER
            # # for x in range(1, pop_index):
            # #     cur_mx[0][index - 1 + x] = pop_mx[0][x]
            # #     cur_mx[index - 1 + x][0] = pop_mx[0][x]
            # #     clusters[parent][St.row] += 1
            #
            # # COPY MATRIX
            # print "\tPOP HEADER: {}".format(pop_mx[0][:])
            # for row in range(1, pop_row):
            #
            #     # ADD HEADER IF NOT ALREADY IN
            #     # print "\tCURREENT HEADER ADDED: {}".format(cur_mx[0:])
            #     if pop_mx[row][0] not in cur_mx[0:]:
            #         pop_item_row = pop_mx[row][0]
            #         cur_mx[index][0] = pop_item_row
            #         cur_mx[0][index] = pop_item_row
            #         index += 1
            #         clusters[parent][St.row] = index
            #         print "\tHEADER ADDED: {}".format(pop_item_row)
            #
            #
            #         # FOR THAT HEADER, COPY THE SUB-MATRIX
            #         for col in range(1, pop_row):
            #
            #             # THE HEADER IS NOT IN
            #             if pop_mx[row][col] != 0 and pop_mx[row][0] not in cur_mx[1:-1]:
            #                 print "\tIN ({}, {})".format(index-1, col )
            #                 # index += 1
            #                 # clusters[parent][St.row] = index
            #
            #             # THE HEADER ARE ALREADY IN THERE
            #             if pop_mx[row][col] != 0:
            #                 # find header in current matrix
            #                 for col_item in range(1, len(cur_mx[1:-1])):
            #                     if cur_mx[0][col_item] == pop_mx[0][col]:
            #                         print "\tIN2 ({}, {})".format(index-1, col_item)
            # cur_mx[row + position_add][col + position_add] = pop_mx[row][col]

            # cur_mx[0][position_add+ row] = pop_mx[row][0]

            # cur_mx[y + position_add][x + position_add] = pop_mx[y][x]

            # POP THE PARENT WITH THE LESSER CHILD

            if annotate:
                clusters[parent][St.annotate] += clusters[pop_parent][St.annotate]
            clusters.pop(pop_parent)

        # 3. ONE CHILD [CHILD 1] HAVE A PARENT OF HIS OWN
        elif has_parent_1 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_1]
            root[child_2] = parent
            clusters[parent][St.children] += [child_2]
            # print "\t>>> {} is in root {}".format(child_2, child_2 in root)

            # cur_mx = clusters[parent][St.matrix]
            cur_mxd = clusters[parent][St.matrix_d]
            row_1 = clusters[parent][St.row]

            # ADD HEADER
            # cur_mx[row_1][0] = child_2
            # cur_mx[0][row_1] = child_2

            cur_mxd[(row_1, 0)] = child_2
            cur_mxd[(0, row_1)] = child_2

            # INCREMENT POSITION
            row_1 += 1
            # print "\tPOSITION: {}".format(row_1)
            clusters[parent][St.row] = row_1

            # COPY MATRIX
            # for col in range(1, row_1):
            #     # print cur_mx[0][x], child_1
            #     if cur_mx[0][col] == child_1:
            #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
            #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
            #         # cur_mx[position_1 - 1][x] = 1
            #         cur_mx[row_1 - 1][col] = 1
            #         clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
            #             child_1, child_2)

            for col in range(1, row_1):
                if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_1:
                    cur_mxd[(row_1 - 1, col)] = 1
                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                            child_1, child_2)

        # 4. ONE CHILD [CHILD 2] HAVE A PARENT OF HIS OWN
        elif has_parent_2 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_2]
            root[child_1] = parent
            clusters[parent][St.children] += [child_1]
            # print "\t>>> {} is in root {}".format(child_1, child_1 in root)

            # cur_mx = clusters[parent][St.matrix]
            cur_mxd = clusters[parent][St.matrix_d]
            row_2 = clusters[parent][St.row]

            # ADD HEADER
            # print row_2
            # cur_mx[row_2][0] = child_1
            # cur_mx[0][row_2] = child_1

            cur_mxd[(row_2, 0)] = child_1
            cur_mxd[(0, row_2)] = child_1

            # INCREMENT POSITION
            row_2 += 1
            # print "\tPOSITION: {}".format(row_2)
            clusters[parent][St.row] = row_2

            # COPY MATRIX
            # for col in range(1, row_2):
            #     # print cur_mx[0][x], child_1
            #     if cur_mx[0][col] == child_2:
            #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
            #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_2 - 1, col)
            #         # cur_mx[position_2 - 1][x] = 1
            #         cur_mx[row_2 - 1][col] = 1
            #         clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
            #             child_2, child_1)

            for col in range(1, row_2):
                if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                    cur_mxd[(row_2 - 1, col)] = 1
                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                            child_2, child_1)

        return counter

    print "2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(g))

    standard = 50000
    check = 1
    iteration = 1

    for subject, predicate, obj in g:

        print "\tRESOURCE {:>7}:   {} {}".format(count, subject, obj)
        count = cluster_helper(count, annotate=False)
        # data = "\tRESOURCE {:>7}:   {} {}".format(count, subject.n3(), obj)

        for key, value in clusters.items():
            print "\t\t", key
            print "\t\t", value
        if iteration == check:
            # print "\tRESOURCE {:>10}:   {} {}".format(count, subject.n3(), obj)
            check += standard
        iteration += 1

    print "3. NUMBER OF CLUSTER FOUND: {}".format(len(clusters))
    return clusters


# USING SET
def links_clustering_improved(graph, limit=1000):

    # ROOT = KEY:CHILD VALUE:PARENT
    root = dict()
    count = 0
    clusters = dict()

    root_mtx = {}
    # count_mtx = 0
    clusters_mtx = {}

    # DOWNLOAD THE GRAPH
    print "\n0. DOWNLOADING THE GRAPH FROM THE TRIPLE STORE"
    response = Exp.export_alignment(graph, limit=limit)
    links = response['result']

    # LOAD THE GRAPH
    print "1. LOADING THE GRAPH USING RDFLIB"
    g = rdflib.Graph()
    g.parse(data=links, format="turtle")

    # g = [
    #     ("<http://grid.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgref.2>"),
    #     ("<http://leiden.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://grid.2>"),
    #     ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgreg.2>"),
    #     ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://h2020.2> "),
    #     ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://eter.2>"),
    #     ("<http://eter.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://leiden.2>"),
    # ]

    # g = [
    #     ( "<http://grid.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgref.2>"),
    #     ( "<http://eter.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://leiden.2>"),
    #     ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://h2020.2> "),
    #     ( "<http://leiden.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://grid.2>"),
    #     ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgreg.2>"),
    #     ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://eter.2>"),
    # ]

    # g = [
    #     ("<http://risis.eu/leidenRanking_2015/resource/884>", "<http://risis.eu/alignment/predicate/SAMEAS>",
    #      "<http://www.grid.ac/institutes/grid.10493.3f>"),
    #     ("<http://risis.eu/leidenRanking_2015/resource/884>", "<http://risis.eu/alignment/predicate/SAMEAS>",
    #      "<http://risis.eu/eter_2014/resource/DE0056>"),
    #     ("<http://www.grid.ac/institutes/grid.10493.3f> ", "<http://risis.eu/alignment/predicate/SAMEAS>",
    #      "<http://risis.eu/eter_2014/resource/DE0056> ") ]

    def merge_d_matrices(parent, pop_parent):

        # COPYING LESSER MATRIX TO BIGGER MATRIX

        index = parent[St.row]
        pop_row = pop_parent[St.row]
        cur_mxd = parent[St.matrix_d]
        pop_mxd = pop_parent[St.matrix_d]
        # position_add = clusters[parent][St.row] - 1

        # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
        # print "\tADD VALUE: {}".format(position_add)

        # COPY MATRIX
        # print "\tPOP HEADER: {}".format(pop_mx[0][:])
        for row in range(1, pop_row):

            # ADD HEADER IF NOT ALREADY IN
            # print "\tCURRENT HEADER ADDED: {}".format(cur_mx[0:])
            if pop_mxd[(row, 0)] not in cur_mxd:
                pop_item_row = pop_mxd[(row, 0)]
                cur_mxd[(index, 0)] = pop_item_row
                cur_mxd[(0, index)] = pop_item_row
                index += 1
                parent[St.row] = index
                # print "\tHEADER ADDED: {}".format(pop_item_row)

                # FOR THAT HEADER, COPY THE SUB-MATRIX
                for col in range(1, pop_row):

                    # THE HEADER ARE ALREADY IN THERE
                    if (row, col) in pop_mxd and pop_mxd[(row, col)] != 0:
                        # find header in current matrix
                        for col_item in range(1, len(cur_mxd)):
                            if (0, col_item) in cur_mxd and (0, col) in pop_mxd and \
                                            cur_mxd[(0, col_item)] == pop_mxd[(0, col)]:
                                # print "\tIN2 ({}, {})".format(index - 1, col_item)
                                cur_mxd[(index - 1, col_item)] = 1

    def cluster_helper_mtx(counter, annotate=False):

        counter += 1
        child_1 = subject.n3().strip()
        child_2 = obj.n3().strip()
        # child_1 = subject.strip()
        # child_2 = obj.strip()

        # DATE CREATION
        # date = "{}".format(datetime.datetime.today().strftime(_format))

        # CHECK WHETHER A CHILD HAS A PARENT
        has_parent_1 = True if child_1 in root_mtx else False
        has_parent_2 = True if child_2 in root_mtx else False
        # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

        # 1. START BOTH CHILD ARE ORPHANS
        if has_parent_1 is False and has_parent_2 is False:

            # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            # GENERATE THE PARENT
            # hash_value = hash(date + str(count) + graph)
            hash_value = hash(child_1 + child_2 + graph)
            parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                hash_value).startswith("-") \
                else "P{}".format(hash_value)

            # ASSIGN A PARENT TO BOTH CHILD
            root[child_1] = parent
            root[child_2] = parent

            # CREATE A CLUSTER
            if parent not in clusters:
                # MATRIX
                # mx = matrix(matrix_size, matrix_size)
                mxd = dict()
                # ROW
                # mx[0][1] = child_1
                # mx[0][2] = child_2

                mxd[(0, 1)] = child_1
                mxd[(0, 2)] = child_2

                # COLUMNS
                # mx[1][0] = child_1
                # mx[2][0] = child_2

                mxd[(1, 0)] = child_1
                mxd[(2, 0)] = child_2

                # RELATION
                # mx[1][2] = 1
                # mx[2][1] = 1
                mxd[(2, 1)] = 1

                clusters[parent] = {St.children: [child_1, child_2], St.matrix: None, St.row: 3, St.matrix_d: mxd}
                if annotate:
                    clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

            # print "\tPOSITION: {}".format(3)
            # print "\tIT WILL BE PRINTED AT: ({}, {})".format(2, 1)

        # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
        elif has_parent_1 is True and has_parent_2 is True:

            # 2.1 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            if root_mtx[child_1] == root_mtx[child_2]:
                # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
                # print "\nSAME PARENTS {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
                # cur_mx = clusters[root[child_1]][St.matrix]
                cur_mxd = clusters[root[child_1]][St.matrix_d]

                row_1 = 0
                row_2 = 0

                # FIND ROW
                # row_1 = clusters[root[child_1]][St.row]
                # for row in range(1, clusters[root[child_1]][St.row]):
                #     if cur_mx[row][0] == child_1:
                #         row_1 = row
                #
                # for col in range(1, clusters[root[child_1]][St.row]):
                #     if cur_mx[0][col] == child_2:
                #         row_2 = col

                for row in range(1, clusters[root[child_1]][St.row]):
                    if (row, 0) in cur_mxd and cur_mxd[(row, 0)] == child_1:
                        row_1 = row

                for col in range(1, clusters[root[child_1]][St.row]):
                    if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                        row_2 = col

                # row_2 = clusters[root[child_2]][St.row]

                # print "\tPOSITIONS: {} | {}".format(row_2, row_1)
                # cur_mx[row_2][row_1] = 1
                cur_mxd[(row_2, row_1)] = 1

                if annotate:
                    clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1, child_2)

                # COPY THE SUB-MATRIX
                # for col in range(1, row_1):
                #     if cur_mx[0][col] == child_2:
                #         print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                #         print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
                #         cur_mx[row_1 - 1][col] = 1

                # continue
                return counter

            # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
            # fFETCHING THE RESOURCES IN THE CLUSTER (CHILDREN)
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            children_1 = (clusters_mtx[root_mtx[child_1]])[St.children]
            children_2 = (clusters_mtx[root_mtx[child_2]])[St.children]

            # 2.2 CHOOSE A PARENT
            if len(children_1) >= len(children_2):
                # print "\tPARENT 1"
                parent = root_mtx[child_1]
                pop_parent = root_mtx[child_2]
                # root[child_2] = parent

            else:
                # print "\tPARENT 2"
                parent = root_mtx[child_2]
                pop_parent = root_mtx[child_1]
                # root[child_1] = parent

            # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
            for offspring in clusters_mtx[pop_parent][St.children]:
                root_mtx[offspring] = parent
                clusters_mtx[parent][St.children] += [offspring]

            # MERGE CURRENT WITH LESSER (CHILDREN) MATRICES, ANNOTATE AND POOP LESSER (CHILDREN) MATRICES
            merge_d_matrices(clusters_mtx[parent], clusters_mtx[pop_parent])

            if annotate:
                clusters_mtx[parent][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
            cluster_helper_mtx(count)
            # cluster_helper(count)

            # COPYING LESSER MATRIX TO BIGGER MATRIX
            # index = clusters[parent][St.row]
            # pop_row = clusters[pop_parent][St.row]
            # cur_mx = clusters[parent][St.matrix]
            # pop_mx = clusters[pop_parent][St.matrix]
            # # position_add = clusters[parent][St.row] - 1
            #
            # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
            # # print "\tADD VALUE: {}".format(position_add)
            #
            # # # ADD HEADER
            # # for x in range(1, pop_index):
            # #     cur_mx[0][index - 1 + x] = pop_mx[0][x]
            # #     cur_mx[index - 1 + x][0] = pop_mx[0][x]
            # #     clusters[parent][St.row] += 1
            #
            # # COPY MATRIX
            # print "\tPOP HEADER: {}".format(pop_mx[0][:])
            # for row in range(1, pop_row):
            #
            #     # ADD HEADER IF NOT ALREADY IN
            #     # print "\tCURREENT HEADER ADDED: {}".format(cur_mx[0:])
            #     if pop_mx[row][0] not in cur_mx[0:]:
            #         pop_item_row = pop_mx[row][0]
            #         cur_mx[index][0] = pop_item_row
            #         cur_mx[0][index] = pop_item_row
            #         index += 1
            #         clusters[parent][St.row] = index
            #         print "\tHEADER ADDED: {}".format(pop_item_row)
            #
            #
            #         # FOR THAT HEADER, COPY THE SUB-MATRIX
            #         for col in range(1, pop_row):
            #
            #             # THE HEADER IS NOT IN
            #             if pop_mx[row][col] != 0 and pop_mx[row][0] not in cur_mx[1:-1]:
            #                 print "\tIN ({}, {})".format(index-1, col )
            #                 # index += 1
            #                 # clusters[parent][St.row] = index
            #
            #             # THE HEADER ARE ALREADY IN THERE
            #             if pop_mx[row][col] != 0:
            #                 # find header in current matrix
            #                 for col_item in range(1, len(cur_mx[1:-1])):
            #                     if cur_mx[0][col_item] == pop_mx[0][col]:
            #                         print "\tIN2 ({}, {})".format(index-1, col_item)
            # cur_mx[row + position_add][col + position_add] = pop_mx[row][col]

            # cur_mx[0][position_add+ row] = pop_mx[row][0]

            # cur_mx[y + position_add][x + position_add] = pop_mx[y][x]

            # POP THE PARENT WITH THE LESSER CHILD

            if annotate:
                clusters_mtx[parent][St.annotate] += clusters_mtx[pop_parent][St.annotate]
            clusters_mtx.pop(pop_parent)

        # 3. ONE CHILD [CHILD 1] HAVE A PARENT OF HIS OWN
        elif has_parent_1 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_1]
            root[child_2] = parent
            clusters[parent][St.children] += [child_2]
            # print "\t>>> {} is in root {}".format(child_2, child_2 in root)

            # cur_mx = clusters[parent][St.matrix]
            cur_mxd = clusters[parent][St.matrix_d]
            row_1 = clusters[parent][St.row]

            # ADD HEADER
            # cur_mx[row_1][0] = child_2
            # cur_mx[0][row_1] = child_2

            cur_mxd[(row_1, 0)] = child_2
            cur_mxd[(0, row_1)] = child_2

            # INCREMENT POSITION
            row_1 += 1
            # print "\tPOSITION: {}".format(row_1)
            clusters[parent][St.row] = row_1

            # COPY MATRIX
            # for col in range(1, row_1):
            #     # print cur_mx[0][x], child_1
            #     if cur_mx[0][col] == child_1:
            #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
            #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
            #         # cur_mx[position_1 - 1][x] = 1
            #         cur_mx[row_1 - 1][col] = 1
            #         clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
            #             child_1, child_2)

            for col in range(1, row_1):
                if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_1:
                    cur_mxd[(row_1 - 1, col)] = 1
                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                            child_1, child_2)

        # 4. ONE CHILD [CHILD 2] HAVE A PARENT OF HIS OWN
        elif has_parent_2 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_2]
            root[child_1] = parent
            clusters[parent][St.children] += [child_1]
            # print "\t>>> {} is in root {}".format(child_1, child_1 in root)

            # cur_mx = clusters[parent][St.matrix]
            cur_mxd = clusters[parent][St.matrix_d]
            row_2 = clusters[parent][St.row]

            # ADD HEADER
            # print row_2
            # cur_mx[row_2][0] = child_1
            # cur_mx[0][row_2] = child_1

            cur_mxd[(row_2, 0)] = child_1
            cur_mxd[(0, row_2)] = child_1

            # INCREMENT POSITION
            row_2 += 1
            # print "\tPOSITION: {}".format(row_2)
            clusters[parent][St.row] = row_2

            # COPY MATRIX
            # for col in range(1, row_2):
            #     # print cur_mx[0][x], child_1
            #     if cur_mx[0][col] == child_2:
            #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
            #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_2 - 1, col)
            #         # cur_mx[position_2 - 1][x] = 1
            #         cur_mx[row_2 - 1][col] = 1
            #         clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
            #             child_2, child_1)

            for col in range(1, row_2):
                if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                    cur_mxd[(row_2 - 1, col)] = 1
                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                            child_2, child_1)

        return counter

    def cluster_helper_set(counter, annotate=False):

        counter += 1
        # child_1 = subject.strip()
        # child_2 = obj.strip()

        child_1 = subject.n3().strip()
        child_2 = obj.n3().strip()

        # DATE CREATION
        the_date = "{}".format(datetime.datetime.today().strftime(_format))

        # CHECK WHETHER A CHILD HAS A PARENT
        has_parent_1 = True if child_1 in root else False
        has_parent_2 = True if child_2 in root else False
        # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

        # 1. START BOTH CHILD ARE ORPHANS
        if has_parent_1 is False and has_parent_2 is False:

            # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            # GENERATE THE PARENT
            hash_value = hash(the_date + str(count) + graph)
            parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                hash_value).startswith("-") \
                else "P{}".format(hash_value)

            # ASSIGN A PARENT TO BOTH CHILD
            root[child_1] = parent
            root[child_2] = parent

            link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
            clusters[parent] = {'nodes': set([child_1, child_2]), 'links': set([link])}

            # print parent, child_1, child_2
            if annotate:
                clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

        # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
        elif has_parent_1 is True and has_parent_2 is True:

            # 2.1 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            if root[child_1] != root[child_2]:

                parent1 = root[child_1]
                parent2 = root[child_2]
                # root2[child_2] = parent1

                if annotate:
                    clusters[parent1][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
                # print parent1, parent2

                if parent2 in clusters:
                    # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
                    # check this
                    for child in clusters[parent2]['nodes']:
                        root[child] = parent1

                    # print 'before', clusters2[parent1]['nodes']
                    clusters[parent1]['nodes'] = clusters[parent1]['nodes'].union(clusters[parent2]['nodes'])
                    clusters[parent1]['links'] = clusters[parent1]['links'].union(clusters[parent2]['links'])
                    # print 'after', clusters2[parent1]['nodes']

                    # add the current link (child_1, child_2)
                    # check this
                    link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                    clusters[parent1]['links'].add(link)

                    clusters.pop(parent2)
            else:
                parent = root[child_1]
                link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                clusters[parent]['links'].add(link)
                if annotate:
                    clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1, child_2)

        elif has_parent_1 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_1]
            root[child_2] = parent

            link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
            clusters[parent]['links'].add(link)
            clusters[parent]['nodes'].add(child_2)

            if annotate:
                clusters[parent][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                            child_1, child_2)

        elif has_parent_2 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_2]
            root[child_1] = parent

            link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
            clusters[parent]['links'].add(link)
            clusters[parent]['nodes'].add(child_1)

            if annotate:
                clusters[parent][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                            child_2, child_1)

        return counter

    print "2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(g))

    standard = 50000
    check = 1
    iteration = 1

    # COMPARING HELPERS
    for subject, predicate, obj in g:

        count = cluster_helper_set(count, annotate=False)
        # count_mtx = cluster_helper_mtx(count_mtx)
        if iteration == check:
            print "\tRESOURCE {:>10}:   {} {}".format(count, subject.n3(), obj)
            check += standard
        iteration += 1

    # sizes = set()
    # sizes2 = set()
    # for p, c in clusters.items():
    #     # {St.children: [child_1, child_2], St.matrix: None, St.row: 3, St.matrix_d: mxd}
    #     # print c
    #     mdx = c[St.matrix_d]
    #     countLinks = 0
    #     for x, y in mdx.items():
    #         if y == 1:
    #             countLinks += 1
    #     sizes.add((len(c[St.children]), countLinks))
    # for p, c in clusters2.items():
    #     sizes2.add((len(c['nodes']), len(c['links'])))
    #
    # sizes = sorted(sizes)
    # sizes2 = sorted(sizes2)
    # print 'Clusters sizes:', '\n', sizes, '\n', sizes2

    print "3. NUMBER OF CLUSTER FOUND: {}".format(len(clusters))
    return clusters


# ****************************************************
# ****************************************************
# USING
#   - [SET]
#   - [TABLE OF RESOURCES] AND THEIR
#   - [STRENGTHS]
# ****************************************************
# ****************************************************

def links_clustering(graph, serialisation_dir, cluster2extend_id=None,
                     related_linkset=None, reset=False, limit=10000, stop_at=None):

    # THIS FUNCTION CLUSTERS NODE OF A GRAPH BASED ON THE ASSUMPTION THAT THE NODE ARE "SAME AS".
    # ONCE THE CLUSTER IS COMPUTED, THE IDEA IS TO SERIALISE IT SO THAT IT WOULD NOT NEED TO BE
    # RECOMPUTED AGAIN WHEN REQUESTED FOR. THE SERIALISED CLUSTER IS LINKED TO THE GENERIC METADATA
    # OF THE GRAPH

    if related_linkset is None:
        print Ut.headings("LINK CLUSTERING...")
    else:
        print Ut.headings("LINK CLUSTERING EXTENSION...")

    print "\nSERIALISATION DIRECTORY:", serialisation_dir

    if os.path.isdir(serialisation_dir) is False:
        os.mkdir(serialisation_dir)

    clusters = {}
    extension_dict = {}

    if reset is True:
        print "DELETING THE SERIALISED DATA FROM: {}".format(graph)
        delete_serialised_clusters(graph)

    # **************************************************************************************************
    # 0. CHECK IF THE ALIGNMENT HAS A TRIPLE DOCUMENTING WHETHER THE CLUSTER WAS SERIALISED
    # **************************************************************************************************
    is_serialised = "ASK {{ <{}>  <{}serialisedClusters> ?dictionary .}}".format(graph, Ns.alivocab)

    # **************************************************************************************************
    # 1. THE CLUSTER HAS ALREADY BEEN SERIALIZED => IT JUST NEED TO BE DE-SERIALISED
    # **************************************************************************************************
    if Qry.boolean_endpoint_response(is_serialised) == "true":

        print ">>> THE CLUSTER HAS ALREADY BEEN SERIALISED, WAIT A SEC WHILE WE FETCH IT."

        # QUERY FOR THE SERIALISATION
        s_query = """SELECT *
        {{
            <{0}>   <{1}serialisedClusters>   ?serialised .
            <{0}>   <{1}numberOfClusters>     ?numberOfClusters .
        }}""".format(graph, Ns.alivocab)
        start = time.time()

        # FETCH THE SERIALISATION
        s_query_result = Qry.sparql_xml_to_matrix(s_query)[St.result]

        # Qry.display_result(s_query, is_activated=True)
        diff = datetime.timedelta(seconds=time.time() - start)
        print "\tLOADED in {}".format(diff)

        # GET THE SERIALISED CLUSTERS
        if s_query_result is not None:

            # EXTRACTING THE NUMBER OF CLUSTERS ABD THE SERIALISED FILE NAME
            serialised_hash = s_query_result[1][0]
            cluster_count = s_query_result[1][1]
            print "\t{} CLUSTERS FOUND AND DATA SAVED IN THE FILE [{}].TXT".format(cluster_count, serialised_hash)

            # *************************************************
            # EXTRACTING DATA FROM THE HASHED DICTIONARY FILE
            # reconciled-
            # *************************************************

            try:

                # DE-SERIALISING THE MAIN DICTIONARY OF CLUSTER
                print "\n\tREADING FROM SERIALISED FILE 1..."
                clusters = Ut.de_serialise_dict(
                    serialised_directory_path=serialisation_dir, name="Serialized_{}-1.txt".format(serialised_hash))

                # DE-SERIALISING THE ROOT DICTIONARY SUPPORTING THE MAIN DICTIONARY OF CLUSTERS
                print "\tREADING FROM SERIALISED FILE 2..."
                node2cluster_id = Ut.de_serialise_dict(
                    serialised_directory_path=serialisation_dir, name="Serialized_{}-2.txt".format(serialised_hash))

            except (IOError, ValueError):
                print "\nRE-RUNNING IT ALL BECAUSE THE SERIALISED FILE [{}].txt COULD NOT BE FOUND.".format(
                    serialised_hash)
                # traceback.print_exc()
                return links_clustering(
                    graph, serialisation_dir, cluster2extend_id=cluster2extend_id,
                    related_linkset=related_linkset, reset=True, limit=limit, stop_at=stop_at)

            # DE-SERIALISE THE SERIALISED
            start = time.time()
            # de_serialised = {'clusters': clusters,
            #                  'node2cluster_id': ast.literal_eval(serialised_node2cluster_id)}
            de_serialised = {'clusters': clusters, 'node2cluster_id': node2cluster_id}

            diff = datetime.timedelta(seconds=time.time() - start)

            print "\tDe-serialised in {}".format(diff)
            clusters = de_serialised['clusters']
            root = de_serialised['node2cluster_id']

            # CALCULATE THE CLUSTERS THAT EXTEND GIVEN A RELATED LINKSET
            if cluster2extend_id is None and related_linkset is not None:
                return clusters, list_extended_clusters(
                    graph, reconciled_name=serialised_hash, clusters_dictionary=de_serialised,
                    related_linkset=related_linkset, serialisation_dir=serialisation_dir)

            # EXTEND THE GIVEN CLUSTER(WHEN THE UI WANT TO SEE A CLUSTER WITH EXTENSION)
            elif cluster2extend_id is not None and related_linkset is not None:
                if cluster2extend_id in clusters:
                    """
                    # {'links': links, 'extensions': list(set(extension))}
                    # LINKS         : LIST OF TUPLE OF THE TYPE (NODE, PAIRED)
                    # EXTENSIONS    : UNIQUE LIST OF CLUSTER ID THAT EXTENT THE ORIGINAL CLUSTER USING PAIRED
                    """
                    print "\n>>> EXTENDING THE CLUSTER ID"
                    extension_dict = cluster_extension(
                        nodes=clusters[cluster2extend_id]['nodes'], node2cluster=root, linkset=related_linkset)
                    all_extensions = list_extended_clusters(
                        graph, serialised_hash, de_serialised, related_linkset, serialisation_dir)

                    corroborated_dict = {}
                    if 'cycle_paths' in all_extensions:
                        if cluster2extend_id in all_extensions['cycle_paths']:
                            corroborated_links = all_extensions['cycle_paths'][cluster2extend_id]
                            print corroborated_links

                            for node1, node2, strength in corroborated_links:
                                key = "key_{}".format(str(hash((node1, node2))).replace("-", "N"))
                                if key not in corroborated_dict:
                                    corroborated_dict[key] = [strength]
                                else:
                                    corroborated_dict[key] += [strength]

                    extension_dict['corroborated_dict'] = corroborated_dict

                else:
                    print "THE CLUSTER ID DOES NOT EXIST."

                # RETURNING THE CLUSTER EXTENSION FOR PLOT
                clusters_subset = {}
                is_subset = False
                nodes_extension = []
                print "\n\tSUBSET...?"
                for cluster_id in extension_dict['extensions']:
                    if cluster_id != cluster2extend_id:
                        is_subset = True
                        clusters_subset[cluster_id] = clusters[cluster_id]
                        print "\t", clusters[cluster_id]
                        nodes_extension += clusters[cluster_id]['nodes']
                if is_subset is False:
                    print "\tNO SUBSET FOUND"

                # ADD THE CLUSTER SUBSET TO THE RETURNED DICTIONARY
                extension_dict['clusters_subset'] = clusters_subset

                links = cluster_links_between_extension(nodes_extension, related_linkset)
                extension_dict['links'] += links

                # THIS ASSUMES THAT THE USER HAS THE CLUSTERS
                # BUT REQUEST FOR A SPECIFIC CLUSTER EXTENSION
                return extension_dict

        # THIS ASSUMES THAT YOU REQUEST THE CLUSTER
        return clusters

    # **************************************************************************************************
    # 2. THE CLUSTER HAS NOT BEEN SERIALIZED YET
    # RUN THE CLUSTER FUNCTION AND SERIALISED IT IN THE GENERIC METADATA
    # **************************************************************************************************
    else:

        print "\n>>> THE CLUSTER HAS NEVER BEEN SERIALISED, WAIT WHILE WE CREATE IT. " \
              "\n>>> *** MAYBE TIME FOR A COFFEE?. ***"

        count = 0
        # THE ROOT KEEPS TRACK OF THE CLUSTER A PARTICULAR NODE BELONGS TOO
        root = dict()
        # THE CLUSTERS DICTIONARY
        clusters = dict()
        # THE DICTIONARY MAPPING EACH NODE TO ITS CLUSTER
        root_mtx = {}
        clusters_mtx = {}

        # EXAMPLE
        #   P1832892825 	{
        #       'nodes': set(['<http://www.grid.ac/institutes/grid.449957.2>',
        #                     '<http://risis.eu/eter_2014/resource/NL0028>']),

        #       'strengths': {('<http://risis.eu/eter_2014/resource/NL0028>',
        #                  '<http://www.grid.ac/institutes/grid.449957.2>'): ['1', '1']},

        #       'links': set([('<http://risis.eu/eter_2014/resource/NL0028>',
        #                  '<http://www.grid.ac/institutes/grid.449957.2>')])
        # }

        # **************************************************************************************************
        # HELPER FUNCTIONS
        # **************************************************************************************************
        def merge_d_matrices(parent, pop_parent):

            # COPYING LESSER MATRIX TO BIGGER MATRIX

            index = parent[St.row]
            pop_row = pop_parent[St.row]
            cur_mxd = parent[St.matrix_d]
            pop_mxd = pop_parent[St.matrix_d]
            # position_add = clusters[parent][St.row] - 1

            # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
            # print "\tADD VALUE: {}".format(position_add)

            # COPY MATRIX
            # print "\tPOP HEADER: {}".format(pop_mx[0][:])
            for row in range(1, pop_row):

                # ADD HEADER IF NOT ALREADY IN
                # print "\tCURRENT HEADER ADDED: {}".format(cur_mx[0:])
                if pop_mxd[(row, 0)] not in cur_mxd:
                    pop_item_row = pop_mxd[(row, 0)]
                    cur_mxd[(index, 0)] = pop_item_row
                    cur_mxd[(0, index)] = pop_item_row
                    index += 1
                    parent[St.row] = index
                    # print "\tHEADER ADDED: {}".format(pop_item_row)

                    # FOR THAT HEADER, COPY THE SUB-MATRIX
                    for col in range(1, pop_row):

                        # THE HEADER ARE ALREADY IN THERE
                        if (row, col) in pop_mxd and pop_mxd[(row, col)] != 0:
                            # find header in current matrix
                            for col_item in range(1, len(cur_mxd)):
                                if (0, col_item) in cur_mxd and (0, col) in pop_mxd and \
                                                cur_mxd[(0, col_item)] == pop_mxd[(0, col)]:
                                    # print "\tIN2 ({}, {})".format(index - 1, col_item)
                                    cur_mxd[(index - 1, col_item)] = 1

        def cluster_helper_mtx(counter, annotate=False):

            counter += 1
            # child_1 = subject.n3().strip()
            # child_2 = obj.n3().strip()
            child_1 = subject.strip()
            child_2 = t_object.strip()

            # DATE CREATION
            # date = "{}".format(datetime.datetime.today().strftime(_format))

            # CHECK WHETHER A CHILD HAS A PARENT
            has_parent_1 = True if child_1 in root_mtx else False
            has_parent_2 = True if child_2 in root_mtx else False
            # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

            # 1. START BOTH CHILD ARE ORPHANS
            if has_parent_1 is False and has_parent_2 is False:

                # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                # GENERATE THE PARENT
                # hash_value = hash(date + str(count) + graph)
                hash_value = hash(child_1 + child_2 + graph)
                parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                    hash_value).startswith("-") \
                    else "P{}".format(hash_value)

                # ASSIGN A PARENT TO BOTH CHILD
                root[child_1] = parent
                root[child_2] = parent

                # CREATE A CLUSTER
                if parent not in clusters:
                    # MATRIX
                    # mx = matrix(matrix_size, matrix_size)
                    mxd = dict()
                    # ROW
                    # mx[0][1] = child_1
                    # mx[0][2] = child_2

                    mxd[(0, 1)] = child_1
                    mxd[(0, 2)] = child_2

                    # COLUMNS
                    # mx[1][0] = child_1
                    # mx[2][0] = child_2

                    mxd[(1, 0)] = child_1
                    mxd[(2, 0)] = child_2

                    # RELATION
                    # mx[1][2] = 1
                    # mx[2][1] = 1
                    mxd[(2, 1)] = 1

                    clusters[parent] = {St.children: [child_1, child_2], St.matrix: None, St.row: 3, St.matrix_d: mxd}
                    if annotate:
                        clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

                # print "\tPOSITION: {}".format(3)
                # print "\tIT WILL BE PRINTED AT: ({}, {})".format(2, 1)

            # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
            elif has_parent_1 is True and has_parent_2 is True:

                # 2.1 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
                if root_mtx[child_1] == root_mtx[child_2]:
                    # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
                    # print "\nSAME PARENTS {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
                    # cur_mx = clusters[root[child_1]][St.matrix]
                    cur_mxd = clusters[root[child_1]][St.matrix_d]

                    row_1 = 0
                    row_2 = 0

                    # FIND ROW
                    # row_1 = clusters[root[child_1]][St.row]
                    # for row in range(1, clusters[root[child_1]][St.row]):
                    #     if cur_mx[row][0] == child_1:
                    #         row_1 = row
                    #
                    # for col in range(1, clusters[root[child_1]][St.row]):
                    #     if cur_mx[0][col] == child_2:
                    #         row_2 = col

                    for row in range(1, clusters[root[child_1]][St.row]):
                        if (row, 0) in cur_mxd and cur_mxd[(row, 0)] == child_1:
                            row_1 = row

                    for col in range(1, clusters[root[child_1]][St.row]):
                        if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                            row_2 = col

                    # row_2 = clusters[root[child_2]][St.row]

                    # print "\tPOSITIONS: {} | {}".format(row_2, row_1)
                    # cur_mx[row_2][row_1] = 1
                    cur_mxd[(row_2, row_1)] = 1

                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1, child_2)

                    # COPY THE SUB-MATRIX
                    # for col in range(1, row_1):
                    #     if cur_mx[0][col] == child_2:
                    #         print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                    #         print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
                    #         cur_mx[row_1 - 1][col] = 1

                    # continue
                    return counter

                # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
                # fFETCHING THE RESOURCES IN THE CLUSTER (CHILDREN)
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                children_1 = (clusters_mtx[root_mtx[child_1]])[St.children]
                children_2 = (clusters_mtx[root_mtx[child_2]])[St.children]

                # 2.2 CHOOSE A PARENT
                if len(children_1) >= len(children_2):
                    # print "\tPARENT 1"
                    parent = root_mtx[child_1]
                    pop_parent = root_mtx[child_2]
                    # root[child_2] = parent

                else:
                    # print "\tPARENT 2"
                    parent = root_mtx[child_2]
                    pop_parent = root_mtx[child_1]
                    # root[child_1] = parent

                # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
                for offspring in clusters_mtx[pop_parent][St.children]:
                    root_mtx[offspring] = parent
                    clusters_mtx[parent][St.children] += [offspring]

                # MERGE CURRENT WITH LESSER (CHILDREN) MATRICES, ANNOTATE AND POOP LESSER (CHILDREN) MATRICES
                merge_d_matrices(clusters_mtx[parent], clusters_mtx[pop_parent])

                if annotate:
                    clusters_mtx[parent][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
                cluster_helper_mtx(count)
                # cluster_helper(count)

                # COPYING LESSER MATRIX TO BIGGER MATRIX
                # index = clusters[parent][St.row]
                # pop_row = clusters[pop_parent][St.row]
                # cur_mx = clusters[parent][St.matrix]
                # pop_mx = clusters[pop_parent][St.matrix]
                # # position_add = clusters[parent][St.row] - 1
                #
                # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
                # # print "\tADD VALUE: {}".format(position_add)
                #
                # # # ADD HEADER
                # # for x in range(1, pop_index):
                # #     cur_mx[0][index - 1 + x] = pop_mx[0][x]
                # #     cur_mx[index - 1 + x][0] = pop_mx[0][x]
                # #     clusters[parent][St.row] += 1
                #
                # # COPY MATRIX
                # print "\tPOP HEADER: {}".format(pop_mx[0][:])
                # for row in range(1, pop_row):
                #
                #     # ADD HEADER IF NOT ALREADY IN
                #     # print "\tCURREENT HEADER ADDED: {}".format(cur_mx[0:])
                #     if pop_mx[row][0] not in cur_mx[0:]:
                #         pop_item_row = pop_mx[row][0]
                #         cur_mx[index][0] = pop_item_row
                #         cur_mx[0][index] = pop_item_row
                #         index += 1
                #         clusters[parent][St.row] = index
                #         print "\tHEADER ADDED: {}".format(pop_item_row)
                #
                #
                #         # FOR THAT HEADER, COPY THE SUB-MATRIX
                #         for col in range(1, pop_row):
                #
                #             # THE HEADER IS NOT IN
                #             if pop_mx[row][col] != 0 and pop_mx[row][0] not in cur_mx[1:-1]:
                #                 print "\tIN ({}, {})".format(index-1, col )
                #                 # index += 1
                #                 # clusters[parent][St.row] = index
                #
                #             # THE HEADER ARE ALREADY IN THERE
                #             if pop_mx[row][col] != 0:
                #                 # find header in current matrix
                #                 for col_item in range(1, len(cur_mx[1:-1])):
                #                     if cur_mx[0][col_item] == pop_mx[0][col]:
                #                         print "\tIN2 ({}, {})".format(index-1, col_item)
                # cur_mx[row + position_add][col + position_add] = pop_mx[row][col]

                # cur_mx[0][position_add+ row] = pop_mx[row][0]

                # cur_mx[y + position_add][x + position_add] = pop_mx[y][x]

                # POP THE PARENT WITH THE LESSER CHILD

                if annotate:
                    clusters_mtx[parent][St.annotate] += clusters_mtx[pop_parent][St.annotate]
                clusters_mtx.pop(pop_parent)

            # 3. ONE CHILD [CHILD 1] HAVE A PARENT OF HIS OWN
            elif has_parent_1 is True:

                # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                parent = root[child_1]
                root[child_2] = parent
                clusters[parent][St.children] += [child_2]
                # print "\t>>> {} is in root {}".format(child_2, child_2 in root)

                # cur_mx = clusters[parent][St.matrix]
                cur_mxd = clusters[parent][St.matrix_d]
                row_1 = clusters[parent][St.row]

                # ADD HEADER
                # cur_mx[row_1][0] = child_2
                # cur_mx[0][row_1] = child_2

                cur_mxd[(row_1, 0)] = child_2
                cur_mxd[(0, row_1)] = child_2

                # INCREMENT POSITION
                row_1 += 1
                # print "\tPOSITION: {}".format(row_1)
                clusters[parent][St.row] = row_1

                # COPY MATRIX
                # for col in range(1, row_1):
                #     # print cur_mx[0][x], child_1
                #     if cur_mx[0][col] == child_1:
                #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
                #         # cur_mx[position_1 - 1][x] = 1
                #         cur_mx[row_1 - 1][col] = 1
                #         clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                #             child_1, child_2)

                for col in range(1, row_1):
                    if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_1:
                        cur_mxd[(row_1 - 1, col)] = 1
                        if annotate:
                            clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                                child_1, child_2)

            # 4. ONE CHILD [CHILD 2] HAVE A PARENT OF HIS OWN
            elif has_parent_2 is True:

                # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                parent = root[child_2]
                root[child_1] = parent
                clusters[parent][St.children] += [child_1]
                # print "\t>>> {} is in root {}".format(child_1, child_1 in root)

                # cur_mx = clusters[parent][St.matrix]
                cur_mxd = clusters[parent][St.matrix_d]
                row_2 = clusters[parent][St.row]

                # ADD HEADER
                # print row_2
                # cur_mx[row_2][0] = child_1
                # cur_mx[0][row_2] = child_1

                cur_mxd[(row_2, 0)] = child_1
                cur_mxd[(0, row_2)] = child_1

                # INCREMENT POSITION
                row_2 += 1
                # print "\tPOSITION: {}".format(row_2)
                clusters[parent][St.row] = row_2

                # COPY MATRIX
                # for col in range(1, row_2):
                #     # print cur_mx[0][x], child_1
                #     if cur_mx[0][col] == child_2:
                #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_2 - 1, col)
                #         # cur_mx[position_2 - 1][x] = 1
                #         cur_mx[row_2 - 1][col] = 1
                #         clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                #             child_2, child_1)

                for col in range(1, row_2):
                    if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                        cur_mxd[(row_2 - 1, col)] = 1
                        if annotate:
                            clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                                child_2, child_1)

            return counter

        def cluster_helper_set(counter, annotate=False):

            counter += 1
            # child_1 = subject.strip()
            # child_2 = obj.strip()

            child_1 = subject.strip()
            child_2 = t_object.strip()
            child_1 = child_1 if Ut.is_nt_format(child_1) else "<{}>".format(child_1)
            child_2 = child_2 if Ut.is_nt_format(child_2) else "<{}>".format(child_2)

            # DATE CREATION
            the_date = "{}".format(datetime.datetime.today().strftime(_format))

            # CHECK WHETHER A CHILD HAS A PARENT
            has_parent_1 = True if child_1 in root else False
            has_parent_2 = True if child_2 in root else False
            # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

            # *******************************************
            # 1. START BOTH CHILD ARE ORPHANS
            # *******************************************
            if has_parent_1 is False and has_parent_2 is False:

                # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                # GENERATE THE PARENT
                hash_value = hash(the_date + str(count) + graph)
                parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                    hash_value).startswith("-") \
                    else "P{}".format(hash_value)

                # ASSIGN A PARENT TO BOTH CHILD
                root[child_1] = parent
                root[child_2] = parent

                # THE SUBJECT AND OBJECT LINK
                link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)

                # THE CLUSTER COMPOSED OF NODES, LINKS AND STRENGTHS
                key_1 = "key_{}".format(str(hash(link)).replace("-", "N"))
                clusters[parent] = {
                    'nodes': set([child_1, child_2]), 'links': set([link]), 'strengths': {key_1: strength}}
                # print "1",clusters[parent]

                # print parent, child_1, child_2
                if annotate:
                    clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

            # *******************************************
            # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
            # *******************************************
            elif has_parent_1 is True and has_parent_2 is True:

                # 2.1 BOTH CHILD DO NOT HAVE THE SAME PARENT
                if root[child_1] != root[child_2]:

                    parent1 = root[child_1]
                    parent2 = root[child_2]
                    # root2[child_2] = parent1

                    if annotate:
                        clusters[parent1][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
                    # print parent1, parent2

                    if parent2 in clusters:

                        # check this
                        # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
                        for child in clusters[parent2]['nodes']:
                            root[child] = parent1

                        # print 'before', clusters2[parent1]['nodes']
                        # RE-ASSIGNING THE NODES OF CHILD 2
                        clusters[parent1]['nodes'] = clusters[parent1]['nodes'].union(clusters[parent2]['nodes'])

                        # RE-ASSIGNING THE LINKS OF CHILD 2
                        clusters[parent1]['links'] = clusters[parent1]['links'].union(clusters[parent2]['links'])

                        # RE-ASSIGNING THE STRENGTHS OF CHILD 2
                        for i_key, link_strengths in clusters[parent2]['strengths'].items():
                            if i_key not in clusters[parent1]['strengths']:
                                clusters[parent1]['strengths'][i_key] = link_strengths
                            else:
                                clusters[parent1]['strengths'][i_key] += link_strengths

                        # print 'after', clusters2[parent1]['nodes']

                        # add the current link (child_1, child_2)
                        link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                        clusters[parent1]['links'].add(link)

                        # link_hash = str(hash(link))
                        link_hash = "key_{}".format(str(hash(link)).replace("-", "N"))
                        if link_hash in clusters[parent1]['strengths']:
                            clusters[parent1]['strengths'][link_hash] += strength
                        else:
                            clusters[parent1]['strengths'][link_hash] = strength

                        clusters.pop(parent2)

                # 2.2 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
                else:
                    parent = root[child_1]
                    link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                    clusters[parent]['links'].add(link)

                    # link_hash = str(hash(link))
                    link_hash = "key_{}".format(str(hash(link)).replace("-", "N"))
                    if link_hash in clusters[parent]['strengths']:
                        clusters[parent]['strengths'][link_hash] += strength
                    else:
                        clusters[parent]['strengths'][link_hash] = strength

                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1, child_2)

            # *******************************************
            # 3. BOTH CHILD HAVE DIFFERENT PARENTS
            # *******************************************
            elif has_parent_1 is True:

                # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                parent = root[child_1]
                root[child_2] = parent

                link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                clusters[parent]['links'].add(link)
                clusters[parent]['nodes'].add(child_2)

                # link_hash = str(hash(link))
                link_hash = "key_{}".format(str(hash(link)).replace("-", "N"))
                if link_hash in clusters[parent]['strengths']:
                    clusters[parent]['strengths'][link_hash] += strength
                else:
                    clusters[parent]['strengths'][link_hash] = strength

                if annotate:
                    clusters[parent][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                                child_1, child_2)

            # *******************************************
            # 4. BOTH CHILD HAVE DIFFERENT PARENTS
            # *******************************************
            elif has_parent_2 is True:

                # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                parent = root[child_2]
                root[child_1] = parent

                link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                clusters[parent]['links'].add(link)
                clusters[parent]['nodes'].add(child_1)

                # link_hash = str(hash(link))
                link_hash = "key_{}".format(str(hash(link)).replace("-", "N"))
                if link_hash in clusters[parent]['strengths']:
                    clusters[parent]['strengths'][link_hash] += strength
                else:
                    clusters[parent]['strengths'][link_hash] = strength

                if annotate:
                    clusters[parent][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                                child_2, child_1)

            return counter

        # **************************************************************************************************
        # RUNNING THE LINK CLUSTER ALGORITHM
        # **************************************************************************************************
        try:

            standard = 50000
            check = 1
            iteration = 1
            size = Qry.get_namedgraph_size(graph)

            # **************************************************************************************************
            print "\n1. DOWNLOADING THE GRAPH FROM THE TRIPLE STORE:\n\t{} of {} triples".format(graph, size)
            # **************************************************************************************************
            start = time.time()
            data = Qry.get_cluster_rsc_strengths(resources=None, alignments=graph, limit=limit, stop_at=stop_at)
            diff = datetime.timedelta(seconds=time.time() - start)
            print "\t{} triples downloaded in {}".format(size, diff)

            if len(data) == 0:
                print "\n\t>>> NO ITERATION AS THE GRAPH IS EMPTY OR STARDOG IS OFF!!!"
                return {}

            # **************************************************************************************************
            # BACKING UP THE GRAPH DATA
            # **************************************************************************************************
            # with open(os.path.join(serialisation_dir, "data.txt"), "wb") as graph_data:
            #     counter = 1000000
            #     counting = 0
            #     data_segment = {}
            #
            #     for key, value in data.items():
            #         counting += 1
            #         data_segment[key] = value
            #
            #         if counting == counter:
            #             graph_data.write(data_segment.__str__() + "\n")
            #             sub_cluster = {}
            #             counting = 0
            #
            #     if counting != 0:
            #         graph_data.write(data_segment.__str__() + "\n")


            # **************************************************************************************************
            print "\n2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(data))
            # **************************************************************************************************
            start = time.time()
            for (subject, t_object), strength in data.items():

                # CALLING THE MAIN HELPER FUNCTION
                count = cluster_helper_set(count, annotate=False)

                # PRINT EVERY STANDARD (X) ITERATION THE CREATED CLUSTERS ON THE SERVER SCREEN EVERY STANDARD ITERATIONS
                if iteration == check:
                    print "\tRESOURCE {:>10}:   {}    =    {}".format(count, subject, t_object)
                    check += standard
                iteration += 1
                # print strength
                # break
            diff = datetime.timedelta(seconds=time.time() - start)
            print "\t{} triples clustered in {}".format(size, diff)
            # COMPARING HELPERS
            # for subject, predicate, obj in g:
            #
            #     count = cluster_helper_set(count, annotate=False)
            #     # count_mtx = cluster_helper_mtx(count_mtx)
            #     if iteration == check:
            #         print "\tRESOURCE {:>10}:   {} {}".format(count, subject.n3(), obj)
            #         check = check + standard
            #     iteration += 1

            # sizes = set()
            # sizes2 = set()
            # for p, c in clusters.items():
            #     # {St.children: [child_1, child_2], St.matrix: None, St.row: 3, St.matrix_d: mxd}
            #     # print c
            #     mdx = c[St.matrix_d]
            #     countLinks = 0
            #     for x, y in mdx.items():
            #         if y == 1:
            #             countLinks += 1
            #     sizes.add((len(c[St.children]), countLinks))
            # for p, c in clusters2.items():
            #     sizes2.add((len(c['nodes']), len(c['links'])))
            #
            # sizes = sorted(sizes)
            # sizes2 = sorted(sizes2)
            # print 'Clusters sizes:', '\n', sizes, '\n', sizes2
            # **************************************************************************************************
            print "\n3. NUMBER OF CLUSTER FOUND: {}".format(len(clusters))
            # **************************************************************************************************

            # for (key, val) in clusters.items():
            #     print key, "\t", val

            # for (key, val) in root.items():
            #     print key, "\t", val

            # **************************************************************************************************
            print "\n4. PROCESSING THE CLUSTERS FOR UNIQUE ID AND PREPARING FOR SERIALISATION"
            # **************************************************************************************************
            new_clusters = dict()
            start = time.time()
            for (key, data) in clusters.items():

                # RESETTING THE CLUSTER ID
                smallest_hash = ""
                for node in data['nodes']:
                    # CREATE THE HASHED ID AS THE CLUSTER NAME
                    hashed = hash(node)
                    if hashed <= smallest_hash:
                        smallest_hash = hashed

                # CREATE A NEW KEY
                new_key = "{}".format(str(smallest_hash).replace("-", "N")) if str(
                    smallest_hash).startswith("-") else "P{}".format(smallest_hash)

                # CONVERTING SET TO LIST AS AST OR JASON DO NOT DEAL WITH SET
                new_clusters[new_key] = {'nodes': [], 'strengths': [], 'links': []}
                new_clusters[new_key]['nodes'] = list(data['nodes'])
                new_clusters[new_key]['strengths'] = data['strengths']
                new_clusters[new_key]['links'] = list(data['links'])

                # UPDATE THE ROOT WITH THE NEW KEY
                for node in data['nodes']:
                    root[node] = new_key

            returned = {'clusters': new_clusters, 'node2cluster_id': root}
            returned_hashed = str(hash(returned.__str__()))
            returned_hashed = returned_hashed.replace("-", "Cluster_N") if returned_hashed.startswith("-")\
                else "Cluster_P{}".format(returned_hashed)

            # **************************************************************************************************
            print "\n5. SERIALISING THE DICTIONARIES..."
            # **************************************************************************************************
            if len(new_clusters) != 0 and len(root) != 0:

                # SERIALISATION
                s_file_1 = "{}-1.txt".format(returned_hashed)
                s_file_2 = "{}-2.txt".format(returned_hashed)

                # SERIALISING THE CLUSTERS
                Ut.serialize_dict(
                    directory=serialisation_dir, dictionary=new_clusters, name=s_file_1, cluster_limit=1000)

                # SERIALISING THE CLUSTER ROOT
                Ut.serialize_dict(
                    directory=serialisation_dir,
                    dictionary=returned['node2cluster_id'], name=s_file_2, cluster_limit=1000)

                # s_file_1 = os.path.join(serialisation_dir, "{}-1.txt".format(returned_hashed))
                # s_file_2 = os.path.join(serialisation_dir, "{}-2.txt".format(returned_hashed))
                # with open(s_file_1, 'wb') as writer:
                #
                #     cluster_limit = 1000
                #     counting = 0
                #     sub_cluster = {}
                #
                #     for key, value in new_clusters.items():
                #         counting += 1
                #         sub_cluster[key] = value
                #
                #         if counting == cluster_limit:
                #             writer.write(sub_cluster.__str__() + "\n")
                #             sub_cluster = {}
                #             counting = 0
                #
                #     if counting != 0:
                #         writer.write(sub_cluster.__str__() + "\n")
                #
                # with open(s_file_2, 'wb') as writer:
                #     writer.write(returned['node2cluster_id'].__str__())

                # **************************************************************************************************
                print "\n6. SAVING THE HASH OF CLUSTERS TO THE TRIPLE STORE AS: {}".format(returned_hashed)
                # **************************************************************************************************
                Qry.endpoint("""INSERT DATA {{
                    <{0}> <{1}serialisedClusters> '''{2}''' .
                    <{0}> <{1}numberOfClusters> {3} .
                }}""".format(graph, Ns.alivocab, returned_hashed, len(clusters)))

                # **************************************************************************************************
                print "\n7. SERIALISATION IS COMPLETED..."
                # **************************************************************************************************
                diff = datetime.timedelta(seconds=time.time() - start)
                print "\t{} triples serialised in {}".format(size, diff)

                print "\nJOB DONE!!!\nDATA RETURNED TO THE CLIENT SIDE TO BE PROCESSED FOR DISPLAY\n"

            else:
                print "THE RETURNED DICTIONARY IS EMPTY."

            # print clusters
            # print new_clusters

            return new_clusters

        except Exception as err:
            traceback.print_exc()
            print err.message
            return clusters


# CLUSTERING A LIST OF TUPLES (NODE-1, NODE-1, STRENGTH) INSTEAD OF THE GRAPH DOWNLOADED FROM STARDOG
def links_list_clustering(data, serialisation_dir, reconciled_name=None, stop_at=None):

    # THIS FUNCTION CLUSTERS NODE OF A GRAPH BASED ON THE ASSUMPTION THAT THE NODE ARE "SAME AS".
    # ONCE THE CLUSTER IS COMPUTED, THE IDEA IS TO SERIALISE IT SO THAT IT WOULD NOT NEED TO BE
    # RECOMPUTED AGAIN WHEN REQUESTED FOR. THE SERIALISED CLUSTER IS LINKED TO THE GENERIC METADATA
    # OF THE GRAPH

    print Ut.headings("LINK LIST CLUSTERING...")

    if os.path.isdir(serialisation_dir) is False:
        os.mkdir(serialisation_dir)

    clusters = {}
    extension_dict = {}

    # **************************************************************************************************
    # 0. CHECK IF THE ALIGNMENT HAS A TRIPLE DOCUMENTING WHETHER IT CLUSTER WAS SERIALISED
    # **************************************************************************************************

    # **************************************************************************************************
    # 1. THE CLUSTER HAS ALREADY BEEN SERIALIZED => IT JUST NEED TO BE DE-SERIALISED
    # **************************************************************************************************

    # **************************************************************************************************
    # 2. THE CLUSTER HAS NOT BEEN SERIALIZED YET
    # RUN THE CLUSTER FUNCTION AND SERIALISED IT IN THE GENERIC METADATA
    # **************************************************************************************************

    if True:

        print "\n>>> THE CLUSTER HAS NEVER BEEN SERIALISED, WAIT WHILE WE CREATE IT. " \
              "\n>>> *** MAYBE TIME FOR A COFFEE?. ***"

        count = 0
        # THE ROOT KEEPS TRACK OF THE CLUSTER A PARTICULAR NODE BELONGS TOO
        root = dict()
        # THE CLUSTERS DICTIONARY
        clusters = dict()
        # THE DICTIONARY MAPPING EACH NODE TO ITS CLUSTER
        root_mtx = {}
        clusters_mtx = {}

        hashed_name = data.__str__()

        # EXAMPLE
        #   P1832892825 	{
        #       'nodes': set(['<http://www.grid.ac/institutes/grid.449957.2>',
        #                     '<http://risis.eu/eter_2014/resource/NL0028>']),

        #       'strengths': {('<http://risis.eu/eter_2014/resource/NL0028>',
        #                  '<http://www.grid.ac/institutes/grid.449957.2>'): ['1', '1']},

        #       'links': set([('<http://risis.eu/eter_2014/resource/NL0028>',
        #                  '<http://www.grid.ac/institutes/grid.449957.2>')])
        # }

        # **************************************************************************************************
        # HELPER FUNCTIONS
        # **************************************************************************************************
        def merge_d_matrices(parent, pop_parent):

            # COPYING LESSER MATRIX TO BIGGER MATRIX

            index = parent[St.row]
            pop_row = pop_parent[St.row]
            cur_mxd = parent[St.matrix_d]
            pop_mxd = pop_parent[St.matrix_d]
            # position_add = clusters[parent][St.row] - 1

            # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
            # print "\tADD VALUE: {}".format(position_add)

            # COPY MATRIX
            # print "\tPOP HEADER: {}".format(pop_mx[0][:])
            for row in range(1, pop_row):

                # ADD HEADER IF NOT ALREADY IN
                # print "\tCURRENT HEADER ADDED: {}".format(cur_mx[0:])
                if pop_mxd[(row, 0)] not in cur_mxd:
                    pop_item_row = pop_mxd[(row, 0)]
                    cur_mxd[(index, 0)] = pop_item_row
                    cur_mxd[(0, index)] = pop_item_row
                    index += 1
                    parent[St.row] = index
                    # print "\tHEADER ADDED: {}".format(pop_item_row)

                    # FOR THAT HEADER, COPY THE SUB-MATRIX
                    for col in range(1, pop_row):

                        # THE HEADER ARE ALREADY IN THERE
                        if (row, col) in pop_mxd and pop_mxd[(row, col)] != 0:
                            # find header in current matrix
                            for col_item in range(1, len(cur_mxd)):
                                if (0, col_item) in cur_mxd and (0, col) in pop_mxd and \
                                                cur_mxd[(0, col_item)] == pop_mxd[(0, col)]:
                                    # print "\tIN2 ({}, {})".format(index - 1, col_item)
                                    cur_mxd[(index - 1, col_item)] = 1

        def cluster_helper_mtx(counter, annotate=False):

            counter += 1
            # child_1 = subject.n3().strip()
            # child_2 = obj.n3().strip()
            child_1 = subject.strip()
            child_2 = t_object.strip()

            # DATE CREATION
            # date = "{}".format(datetime.datetime.today().strftime(_format))

            # CHECK WHETHER A CHILD HAS A PARENT
            has_parent_1 = True if child_1 in root_mtx else False
            has_parent_2 = True if child_2 in root_mtx else False
            # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

            # 1. START BOTH CHILD ARE ORPHANS
            if has_parent_1 is False and has_parent_2 is False:

                # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                # GENERATE THE PARENT
                # hash_value = hash(date + str(count) + graph)
                hash_value = hash(child_1 + child_2 + hashed_name)
                parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                    hash_value).startswith("-") \
                    else "P{}".format(hash_value)

                # ASSIGN A PARENT TO BOTH CHILD
                root[child_1] = parent
                root[child_2] = parent

                # CREATE A CLUSTER
                if parent not in clusters:
                    # MATRIX
                    # mx = matrix(matrix_size, matrix_size)
                    mxd = dict()
                    # ROW
                    # mx[0][1] = child_1
                    # mx[0][2] = child_2

                    mxd[(0, 1)] = child_1
                    mxd[(0, 2)] = child_2

                    # COLUMNS
                    # mx[1][0] = child_1
                    # mx[2][0] = child_2

                    mxd[(1, 0)] = child_1
                    mxd[(2, 0)] = child_2

                    # RELATION
                    # mx[1][2] = 1
                    # mx[2][1] = 1
                    mxd[(2, 1)] = 1

                    clusters[parent] = {St.children: [child_1, child_2], St.matrix: None, St.row: 3,
                                        St.matrix_d: mxd}
                    if annotate:
                        clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

                        # print "\tPOSITION: {}".format(3)
                        # print "\tIT WILL BE PRINTED AT: ({}, {})".format(2, 1)

            # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
            elif has_parent_1 is True and has_parent_2 is True:

                # 2.1 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
                if root_mtx[child_1] == root_mtx[child_2]:
                    # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
                    # print "\nSAME PARENTS {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
                    # cur_mx = clusters[root[child_1]][St.matrix]
                    cur_mxd = clusters[root[child_1]][St.matrix_d]

                    row_1 = 0
                    row_2 = 0

                    # FIND ROW
                    # row_1 = clusters[root[child_1]][St.row]
                    # for row in range(1, clusters[root[child_1]][St.row]):
                    #     if cur_mx[row][0] == child_1:
                    #         row_1 = row
                    #
                    # for col in range(1, clusters[root[child_1]][St.row]):
                    #     if cur_mx[0][col] == child_2:
                    #         row_2 = col

                    for row in range(1, clusters[root[child_1]][St.row]):
                        if (row, 0) in cur_mxd and cur_mxd[(row, 0)] == child_1:
                            row_1 = row

                    for col in range(1, clusters[root[child_1]][St.row]):
                        if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                            row_2 = col

                    # row_2 = clusters[root[child_2]][St.row]

                    # print "\tPOSITIONS: {} | {}".format(row_2, row_1)
                    # cur_mx[row_2][row_1] = 1
                    cur_mxd[(row_2, row_1)] = 1

                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1,
                                                                                                  child_2)

                    # COPY THE SUB-MATRIX
                    # for col in range(1, row_1):
                    #     if cur_mx[0][col] == child_2:
                    #         print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                    #         print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
                    #         cur_mx[row_1 - 1][col] = 1

                    # continue
                    return counter

                # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
                # fFETCHING THE RESOURCES IN THE CLUSTER (CHILDREN)
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                children_1 = (clusters_mtx[root_mtx[child_1]])[St.children]
                children_2 = (clusters_mtx[root_mtx[child_2]])[St.children]

                # 2.2 CHOOSE A PARENT
                if len(children_1) >= len(children_2):
                    # print "\tPARENT 1"
                    parent = root_mtx[child_1]
                    pop_parent = root_mtx[child_2]
                    # root[child_2] = parent

                else:
                    # print "\tPARENT 2"
                    parent = root_mtx[child_2]
                    pop_parent = root_mtx[child_1]
                    # root[child_1] = parent

                # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
                for offspring in clusters_mtx[pop_parent][St.children]:
                    root_mtx[offspring] = parent
                    clusters_mtx[parent][St.children] += [offspring]

                # MERGE CURRENT WITH LESSER (CHILDREN) MATRICES, ANNOTATE AND POOP LESSER (CHILDREN) MATRICES
                merge_d_matrices(clusters_mtx[parent], clusters_mtx[pop_parent])

                if annotate:
                    clusters_mtx[parent][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
                cluster_helper_mtx(count)
                # cluster_helper(count)

                # COPYING LESSER MATRIX TO BIGGER MATRIX
                # index = clusters[parent][St.row]
                # pop_row = clusters[pop_parent][St.row]
                # cur_mx = clusters[parent][St.matrix]
                # pop_mx = clusters[pop_parent][St.matrix]
                # # position_add = clusters[parent][St.row] - 1
                #
                # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
                # # print "\tADD VALUE: {}".format(position_add)
                #
                # # # ADD HEADER
                # # for x in range(1, pop_index):
                # #     cur_mx[0][index - 1 + x] = pop_mx[0][x]
                # #     cur_mx[index - 1 + x][0] = pop_mx[0][x]
                # #     clusters[parent][St.row] += 1
                #
                # # COPY MATRIX
                # print "\tPOP HEADER: {}".format(pop_mx[0][:])
                # for row in range(1, pop_row):
                #
                #     # ADD HEADER IF NOT ALREADY IN
                #     # print "\tCURREENT HEADER ADDED: {}".format(cur_mx[0:])
                #     if pop_mx[row][0] not in cur_mx[0:]:
                #         pop_item_row = pop_mx[row][0]
                #         cur_mx[index][0] = pop_item_row
                #         cur_mx[0][index] = pop_item_row
                #         index += 1
                #         clusters[parent][St.row] = index
                #         print "\tHEADER ADDED: {}".format(pop_item_row)
                #
                #
                #         # FOR THAT HEADER, COPY THE SUB-MATRIX
                #         for col in range(1, pop_row):
                #
                #             # THE HEADER IS NOT IN
                #             if pop_mx[row][col] != 0 and pop_mx[row][0] not in cur_mx[1:-1]:
                #                 print "\tIN ({}, {})".format(index-1, col )
                #                 # index += 1
                #                 # clusters[parent][St.row] = index
                #
                #             # THE HEADER ARE ALREADY IN THERE
                #             if pop_mx[row][col] != 0:
                #                 # find header in current matrix
                #                 for col_item in range(1, len(cur_mx[1:-1])):
                #                     if cur_mx[0][col_item] == pop_mx[0][col]:
                #                         print "\tIN2 ({}, {})".format(index-1, col_item)
                # cur_mx[row + position_add][col + position_add] = pop_mx[row][col]

                # cur_mx[0][position_add+ row] = pop_mx[row][0]

                # cur_mx[y + position_add][x + position_add] = pop_mx[y][x]

                # POP THE PARENT WITH THE LESSER CHILD

                if annotate:
                    clusters_mtx[parent][St.annotate] += clusters_mtx[pop_parent][St.annotate]
                clusters_mtx.pop(pop_parent)

            # 3. ONE CHILD [CHILD 1] HAVE A PARENT OF HIS OWN
            elif has_parent_1 is True:

                # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                parent = root[child_1]
                root[child_2] = parent
                clusters[parent][St.children] += [child_2]
                # print "\t>>> {} is in root {}".format(child_2, child_2 in root)

                # cur_mx = clusters[parent][St.matrix]
                cur_mxd = clusters[parent][St.matrix_d]
                row_1 = clusters[parent][St.row]

                # ADD HEADER
                # cur_mx[row_1][0] = child_2
                # cur_mx[0][row_1] = child_2

                cur_mxd[(row_1, 0)] = child_2
                cur_mxd[(0, row_1)] = child_2

                # INCREMENT POSITION
                row_1 += 1
                # print "\tPOSITION: {}".format(row_1)
                clusters[parent][St.row] = row_1

                # COPY MATRIX
                # for col in range(1, row_1):
                #     # print cur_mx[0][x], child_1
                #     if cur_mx[0][col] == child_1:
                #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
                #         # cur_mx[position_1 - 1][x] = 1
                #         cur_mx[row_1 - 1][col] = 1
                #         clusters[root[child_1]][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                #             child_1, child_2)

                for col in range(1, row_1):
                    if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_1:
                        cur_mxd[(row_1 - 1, col)] = 1
                        if annotate:
                            clusters[root[child_1]][
                                St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                                child_1, child_2)

            # 4. ONE CHILD [CHILD 2] HAVE A PARENT OF HIS OWN
            elif has_parent_2 is True:

                # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                parent = root[child_2]
                root[child_1] = parent
                clusters[parent][St.children] += [child_1]
                # print "\t>>> {} is in root {}".format(child_1, child_1 in root)

                # cur_mx = clusters[parent][St.matrix]
                cur_mxd = clusters[parent][St.matrix_d]
                row_2 = clusters[parent][St.row]

                # ADD HEADER
                # print row_2
                # cur_mx[row_2][0] = child_1
                # cur_mx[0][row_2] = child_1

                cur_mxd[(row_2, 0)] = child_1
                cur_mxd[(0, row_2)] = child_1

                # INCREMENT POSITION
                row_2 += 1
                # print "\tPOSITION: {}".format(row_2)
                clusters[parent][St.row] = row_2

                # COPY MATRIX
                # for col in range(1, row_2):
                #     # print cur_mx[0][x], child_1
                #     if cur_mx[0][col] == child_2:
                #         # print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
                #         # print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_2 - 1, col)
                #         # cur_mx[position_2 - 1][x] = 1
                #         cur_mx[row_2 - 1][col] = 1
                #         clusters[root[child_1]][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                #             child_2, child_1)

                for col in range(1, row_2):
                    if (0, col) in cur_mxd and cur_mxd[(0, col)] == child_2:
                        cur_mxd[(row_2 - 1, col)] = 1
                        if annotate:
                            clusters[root[child_1]][
                                St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                                child_2, child_1)

            return counter

        def cluster_helper_set(counter, annotate=False):

            counter += 1
            # child_1 = subject.strip()
            # child_2 = obj.strip()

            child_1 = subject.strip()
            child_2 = t_object.strip()
            child_1 = child_1 if Ut.is_nt_format(child_1) else "<{}>".format(child_1)
            child_2 = child_2 if Ut.is_nt_format(child_2) else "<{}>".format(child_2)

            # DATE CREATION
            the_date = "{}".format(datetime.datetime.today().strftime(_format))

            # CHECK WHETHER A CHILD HAS A PARENT
            has_parent_1 = True if child_1 in root else False
            has_parent_2 = True if child_2 in root else False
            # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

            # *******************************************
            # 1. START BOTH CHILD ARE ORPHANS
            # *******************************************
            if has_parent_1 is False and has_parent_2 is False:

                # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                # GENERATE THE PARENT
                hash_value = hash(the_date + str(count) + hashed_name)
                parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                    hash_value).startswith("-") \
                    else "P{}".format(hash_value)

                # ASSIGN A PARENT TO BOTH CHILD
                root[child_1] = parent
                root[child_2] = parent

                # THE SUBJECT AND OBJECT LINK
                link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)

                # THE CLUSTER COMPOSED OF NODES, LINKS AND STRENGTHS
                key_1 = "key_{}".format(str(hash(link)).replace("-", "N"))
                clusters[parent] = {
                    'nodes': set([child_1, child_2]), 'links': set([link]), 'strengths': {key_1: strength}}
                # print "1",clusters[parent]

                # print parent, child_1, child_2
                if annotate:
                    clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

            # *******************************************
            # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
            # *******************************************
            elif has_parent_1 is True and has_parent_2 is True:

                # 2.1 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
                if root[child_1] != root[child_2]:

                    parent1 = root[child_1]
                    parent2 = root[child_2]
                    # root2[child_2] = parent1

                    if annotate:
                        clusters[parent1][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
                    # print parent1, parent2

                    if parent2 in clusters:
                        # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
                        # check this
                        for child in clusters[parent2]['nodes']:
                            root[child] = parent1

                        # print 'before', clusters2[parent1]['nodes']
                        # RE-ASSIGNING THE NODES OF CHILD 2
                        clusters[parent1]['nodes'] = clusters[parent1]['nodes'].union(
                            clusters[parent2]['nodes'])
                        # RE-ASSIGNING THE LINKS OF CHILD 2

                        clusters[parent1]['links'] = clusters[parent1]['links'].union(
                            clusters[parent2]['links'])

                        # RE-ASSIGNING THE STRENGTHS OF CHILD 2
                        for i_key, link_strengths in clusters[parent2]['strengths'].items():
                            if i_key not in clusters[parent1]['strengths']:
                                clusters[parent1]['strengths'][i_key] = link_strengths
                            else:
                                clusters[parent1]['strengths'][i_key] += link_strengths

                        # print 'after', clusters2[parent1]['nodes']

                        # add the current link (child_1, child_2)
                        link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                        clusters[parent1]['links'].add(link)

                        # link_hash = str(hash(link))
                        link_hash = "key_{}".format(str(hash(link)).replace("-", "N"))
                        if link_hash in clusters[parent1]['strengths']:
                            clusters[parent1]['strengths'][link_hash] += strength
                        else:
                            clusters[parent1]['strengths'][link_hash] = strength

                        clusters.pop(parent2)
                else:
                    parent = root[child_1]
                    link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                    clusters[parent]['links'].add(link)

                    # link_hash = str(hash(link))
                    link_hash = "key_{}".format(str(hash(link)).replace("-", "N"))
                    if link_hash in clusters[parent]['strengths']:
                        clusters[parent]['strengths'][link_hash] += strength
                    else:
                        clusters[parent]['strengths'][link_hash] = strength

                    if annotate:
                        clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1,
                                                                                                  child_2)

            # *******************************************
            # 3. BOTH CHILD HAVE DIFFERENT PARENTS
            # *******************************************
            elif has_parent_1 is True:

                # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                parent = root[child_1]
                root[child_2] = parent

                link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                clusters[parent]['links'].add(link)
                clusters[parent]['nodes'].add(child_2)

                # link_hash = str(hash(link))
                link_hash = "key_{}".format(str(hash(link)).replace("-", "N"))
                if link_hash in clusters[parent]['strengths']:
                    clusters[parent]['strengths'][link_hash] += strength
                else:
                    clusters[parent]['strengths'][link_hash] = strength

                if annotate:
                    clusters[parent][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                        child_1, child_2)

            # *******************************************
            # 4. BOTH CHILD HAVE DIFFERENT PARENTS
            # *******************************************
            elif has_parent_2 is True:

                # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
                # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

                parent = root[child_2]
                root[child_1] = parent

                link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                clusters[parent]['links'].add(link)
                clusters[parent]['nodes'].add(child_1)

                # link_hash = str(hash(link))
                link_hash = "key_{}".format(str(hash(link)).replace("-", "N"))
                if link_hash in clusters[parent]['strengths']:
                    clusters[parent]['strengths'][link_hash] += strength
                else:
                    clusters[parent]['strengths'][link_hash] = strength

                if annotate:
                    clusters[parent][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                        child_2, child_1)

            return counter

        # **************************************************************************************************
        # RUNNING THE LINK CLUSTER ALGORITHM
        # **************************************************************************************************
        try:

            standard = 50000
            check = 1
            iteration = 1
            size = len(data)

            # **************************************************************************************************
            print "\n1. THE GRAPH IS OF {} LINKS".format(size)
            # **************************************************************************************************
            if len(data) == 0:
                print "\n\t>>> NO ITERATION AS THE GRAPH IS EMPTY OR STARDOG IS OFF!!!"
                return {}

            # **************************************************************************************************
            print "\n2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(data))
            # **************************************************************************************************
            start = time.time()
            for connection in data:

                subject, t_object, strength = connection[0], connection[1], connection[2]

                # CALLING THE MAIN HELPER FUNCTION
                count = cluster_helper_set(count, annotate=False)

                # PRINTING THE CREATED CLUSTERS ON THE SERVER SCREEN EVERY STANDARD ITERATIONS
                if iteration == check:
                    print "\tRESOURCE {:>10}:   {}    =    {}".format(count, subject, t_object)
                    check += standard
                iteration += 1
                # print strength
                # break
            diff = datetime.timedelta(seconds=time.time() - start)
            print "\t{} triples clustered in {}".format(size, diff)
            # COMPARING HELPERS
            # for subject, predicate, obj in g:
            #
            #     count = cluster_helper_set(count, annotate=False)
            #     # count_mtx = cluster_helper_mtx(count_mtx)
            #     if iteration == check:
            #         print "\tRESOURCE {:>10}:   {} {}".format(count, subject.n3(), obj)
            #         check = check + standard
            #     iteration += 1

            # sizes = set()
            # sizes2 = set()
            # for p, c in clusters.items():
            #     # {St.children: [child_1, child_2], St.matrix: None, St.row: 3, St.matrix_d: mxd}
            #     # print c
            #     mdx = c[St.matrix_d]
            #     countLinks = 0
            #     for x, y in mdx.items():
            #         if y == 1:
            #             countLinks += 1
            #     sizes.add((len(c[St.children]), countLinks))
            # for p, c in clusters2.items():
            #     sizes2.add((len(c['nodes']), len(c['links'])))
            #
            # sizes = sorted(sizes)
            # sizes2 = sorted(sizes2)
            # print 'Clusters sizes:', '\n', sizes, '\n', sizes2
            # **************************************************************************************************
            print "\n3. NUMBER OF CLUSTER FOUND: {}".format(len(clusters))
            # **************************************************************************************************

            # for (key, val) in clusters.items():
            #     print key, "\t", val

            # for (key, val) in root.items():
            #     print key, "\t", val

            # **************************************************************************************************
            print "\n4. PROCESSING THE CLUSTERS FOR UNIQUE ID AND PREPARING FOR SERIALISATION"
            # **************************************************************************************************
            new_clusters = dict()
            start = time.time()
            for (key, data) in clusters.items():

                # RESETTING THE CLUSTER ID
                smallest_hash = ""
                for node in data['nodes']:
                    # CREATE THE HASHED ID AS THE CLUSTER NAME
                    hashed = hash(node)
                    if hashed <= smallest_hash:
                        smallest_hash = hashed

                # CREATE A NE KEY
                new_key = "{}".format(str(smallest_hash).replace("-", "N")) if str(
                    smallest_hash).startswith("-") else "P{}".format(smallest_hash)

                # CONVERTING SET TO LIST AS AST OR JASON DO NOT DEAL WITH SET
                new_clusters[new_key] = {'nodes': [], 'strengths': [], 'links': []}
                new_clusters[new_key]['nodes'] = list(data['nodes'])
                new_clusters[new_key]['strengths'] = data['strengths']
                new_clusters[new_key]['links'] = list(data['links'])

                # UPDATE THE ROOT WITH THE NEW KEY
                for node in data['nodes']:
                    root[node] = new_key

            returned = {'clusters': new_clusters, 'node2cluster_id': root}
            # returned_hashed = str(hash(returned.__str__()))
            # returned_hashed = returned_hashed.replace("-", "Cluster_N") if returned_hashed.startswith("-")\
            #     else "Cluster_P{}".format(returned_hashed)

            if len(new_clusters) != 0 and len(root) != 0:

                # SERIALISATION
                # **************************************************************************************************
                print "\n5. SERIALISING THE DICTIONARIES..."
                # **************************************************************************************************
                s_file_1 = os.path.join(serialisation_dir, "{}-reconciled-1.txt".format(reconciled_name))
                s_file_2 = os.path.join(serialisation_dir, "{}-reconciled-2.txt".format(reconciled_name))
                with open(s_file_1, 'wb') as writer:

                    cluster_limit = 1000
                    counting = 0
                    sub_cluster = {}

                    for key, value in new_clusters.items():
                        counting += 1
                        sub_cluster[key] = value

                        if counting == cluster_limit:
                            writer.write(sub_cluster.__str__() + "\n")
                            sub_cluster = {}
                            counting = 0

                    if counting != 0:
                        writer.write(sub_cluster.__str__() + "\n")

                with open(s_file_2, 'wb') as writer:
                    writer.write(returned['node2cluster_id'].__str__())

                # **************************************************************************************************
                print "\n6. SAVING THE HASH OF CLUSTERS TO THE TRIPLE STORE AS: {}".format(reconciled_name)
                # **************************************************************************************************


                # **************************************************************************************************
                print "\n7. SERIALISATION IS COMPLETED..."
                # **************************************************************************************************
                diff = datetime.timedelta(seconds=time.time() - start)
                print "\t{} triples serialised in {}".format(size, diff)

                print "\nJOB DONE!!!\nDATA RETURNED TO THE CLIENT SIDE TO BE PROCESSED FOR DISPLAY\n"

            else:
                print "THE RETURNED DICTIONARY IS EMPTY."

            # print clusters
            # print new_clusters

            return new_clusters

        except Exception as err:
            traceback.print_exc()
            print err.message
            return clusters


# ****************************************************
# BASED ON ASSOCIATION RELATIONSHIPS [related_linkset]
# THIS FUNCTION EXTENDS A GRAPH
# ****************************************************
def list_extended_clusters(
        graph, reconciled_name, clusters_dictionary, related_linkset, serialisation_dir, reset=False):

    print "\n>>> RUNNING THE FUNCTION [list_extended_clusters]"
    # 1. DOCUMENTING START AND END OF PATHS IN A CYCLE
    # 2. AND CALCULATING THE WEIGHT OF THE LINKS IN THE PATH

    def cycle_helper(src_node, trg_node, source_cluster, target_cluster, detail=False):

        # print '\n Starting helper for'
        # print '\t Source:', source_cluster, src_node
        # print '\t Target:', target_cluster, trg_node

        old = False

        # CHECK WHETHER THE PAIR OF CLUSTERS IS IN A CYCLE.
        # THIS IS THE CASE IF THE PAIR OF CLUSTER HAS AT LEAST TWO RELATED LINKS
        list_of_related = dict_clusters_pairs[(source_cluster, target_cluster)]

        # DOCUMENTING THE CYCLE START AND END FOR THIS SPECIFIC ORDER
        # if list_of_related >= 2:

        for related_nodes in list_of_related:

            # 1.1 COMPUTE THE SHORTEST PATH SIZE (DIAMETER) FOR THESE START AND END NODES (SUBJECT)
            sub_link_network = clusters[source_cluster]['links']
            sub_strengths = clusters[source_cluster]['strengths']

            # 1.2 COMPUTE THE SHORTEST PATH SIZE FOR T(DIAMETER) THESE START AND END NODES (TARGET)
            obj_link_network = clusters[target_cluster]['links']
            obj_strengths = clusters[target_cluster]['strengths']

            # 2.1 GET THE DIAMETER AND WEIGHTED DIAMETER OF THE SUBJECT
            # print "\n\tGETTING THE DIAMETER AND WEIGHTED DIAMETER OF THE SUBJECT CLUSTER FOR START AND END NODES:"
            # print "\t\t\v ", related_nodes[0], "AND", src_node
            sub_diameter_weighted_diameter = shortest_paths_lite(
                sub_link_network, start_node=related_nodes[0], end_node=src_node, strengths=sub_strengths)

            # 2.2 GET THE DIAMETER AND WEIGHTED DIAMETER OF THE OBJECT
            # print "\tGETTING THE DIAMETER AND WEIGHTED DIAMETER OF THE OBJECT CLUSTER FOR START AND END NODES:"
            # print "\t\t\v ", related_nodes[1], "AND", trg_node
            obj_diameter_weighted_diameter = shortest_paths_lite(
                obj_link_network, start_node=related_nodes[1], end_node=trg_node, strengths=obj_strengths)

            # 3.1 [SOURCE] FETCH THE STRENGTH OF THE RECONCILED NODES IF THE LINK EXISTS
            link_1 = (related_nodes[0], src_node) if related_nodes[0] < src_node else (src_node, related_nodes[0])
            key_1 = "key_{}".format(str(hash(link_1)).replace("-", "N"))
            if key_1 in sub_strengths:
                sub_strength = max(sub_strengths[key_1])
            else:
                # print "\nNO KEY FOR: {}\n\t{}".format(key_1, link)
                sub_strength = 0

            # 3.2 [TARGET] FETCH THE STRENGTH OF THE RECONCILED NODES IF THE LINK EXISTS
            link_2 = (related_nodes[1], trg_node) if related_nodes[1] < trg_node else (trg_node, related_nodes[1])
            key_2 = "key_{}".format(str(hash(link_2)).replace("-", "N"))
            if key_2 in obj_strengths:
                obj_strength = max(obj_strengths[key_2])
            else:
                # print "\nNO KEY FOR: {}\n\t{}".format(key_2, link)
                obj_strength = 0

            # 4.1 COMPUTE THE EVIDENCE'S STRENGTH OF THE SUBJECT
            # print "\t", "COMPUTING THE EVIDENCE'S STRENGTH OF THE SUBJECT CLUSTER FOR START AND END NODES:"
            # print "\t\t>>> SIM DATA:", "sim = ", "ev_diameter = ", obj_diameter_weighted_diameter, \
            #     "ev_W_diameter = ", obj_diameter_weighted_diameter
            subj_r_strength = reconciliation_strength(
                sub_strength, ev_diameter=obj_diameter_weighted_diameter[0],
                ev_w_diameter=obj_diameter_weighted_diameter[1], c_penalty=10)
            # print "\t\t>>> RECONCILED:", 0 if strength < 0 else strength

            # 4.2 COMPUTE THE EVIDENCE'S STRENGTH OF THE OBJECT
            # print "\t", "COMPUTING THE EVIDENCE'S STRENGTH OF THE OBJECT CLUSTER FOR START AND END NODES:"
            # print "\t\t>>> SIM DATA:", "sim = ", "ev_diameter = ", sub_diameter_weighted_diameter, \
            #     "ev_W_diameter = ", sub_diameter_weighted_diameter
            obj_r_strength = reconciliation_strength(
                obj_strength, ev_diameter=sub_diameter_weighted_diameter[0],
                ev_w_diameter=sub_diameter_weighted_diameter[1], c_penalty=10)
            # print "\t\t>>> RECONCILED:", 0 if strength < 0 else strength

            # BUILDING THE NETWORKS FOR RECONCILED NODES
            key_1 = Ut.get_key(related_nodes[0], src_node)
            key_2 = Ut.get_key(related_nodes[1], trg_node)
            if source_cluster not in reconciled_nodes:
                reconciled_nodes[source_cluster] = {"links": [(related_nodes[0], src_node, "R")],
                                                    "strengths": {key_1: [subj_r_strength]}}
            else:
                if "links" not in reconciled_nodes[source_cluster]:
                    reconciled_nodes[source_cluster]["links"] = [(related_nodes[0], src_node, "R")]
                    reconciled_nodes[source_cluster]["strengths"] = {key_1: [subj_r_strength]}
                else:
                    reconciled_nodes[source_cluster]["links"] += [(related_nodes[0], src_node, "R")]

                    if key_1 in reconciled_nodes[source_cluster]["strengths"]:
                        reconciled_nodes[source_cluster]["strengths"][key_1] += [subj_r_strength]
                    else:
                        reconciled_nodes[source_cluster]["strengths"][key_1] = [subj_r_strength]

            # BUILDING THE  NETWORKS
            if target_cluster not in reconciled_nodes:
                reconciled_nodes[target_cluster] = {"links": [(related_nodes[1], trg_node, "R")],
                                                    "strengths": {key_2: [obj_r_strength]}}
            else:
                if "links" not in reconciled_nodes[target_cluster]:
                    reconciled_nodes[target_cluster]["links"] = [(related_nodes[1], trg_node, "R")]
                    reconciled_nodes[target_cluster]["strengths"] = {key_2: [obj_r_strength]}
                else:
                    reconciled_nodes[target_cluster]["links"] += [(related_nodes[1], trg_node, "R")]

                    if key_2 in reconciled_nodes[target_cluster]["strengths"]:
                        reconciled_nodes[target_cluster]["strengths"][key_2] += [obj_r_strength]
                    else:
                        reconciled_nodes[target_cluster]["strengths"][key_2] = [obj_r_strength]

            if detail:

                # ****************************************************************************************************
                # PROCESS COMMENT FOR SUBJECT CLUSTER
                # ****************************************************************************************************
                print "\n\tGETTING THE DIAMETER AND WEIGHTED DIAMETER OF THE SUBJECT CLUSTER FOR START AND END NODES:"
                print "\t\t\v {} AND {}".format(related_nodes[0], src_node)
                print "\t", "COMPUTING THE EVIDENCE'S STRENGTH OF THE SUBJECT CLUSTER FOR START AND END NODES:"
                print "\t\t>>> SIM DATA: sim={} ev_diameter={} ev_W_diameter={}\n\t\t>>> RECONCILED: {}".format(
                    sub_strength, sub_diameter_weighted_diameter[0], sub_diameter_weighted_diameter[1], subj_r_strength)

                # ****************************************************************************************************
                # PROCESS COMMENT FOR OBJECT CLUSTER
                # ****************************************************************************************************
                print "\n\tGETTING THE DIAMETER AND WEIGHTED DIAMETER OF THE OBJECT CLUSTER FOR START AND END NODES:"
                print "\t\t\v {} AND {}".format(related_nodes[1], trg_node)
                print "\t", "COMPUTING THE EVIDENCE'S STRENGTH OF THE OBJECT CLUSTER FOR START AND END NODES:"
                print "\t\t>>> SIM DATA: sim={} ev_diameter={} ev_W_diameter={}\n\t\t>>> RECONCILED: {}".format(
                    obj_strength, sub_diameter_weighted_diameter[0], sub_diameter_weighted_diameter[1], obj_r_strength)

            if old:
                sub_diameter = shortest_paths_lite_size(
                    sub_link_network, start_node=related_nodes[0], end_node=src_node)

                obj_diameter = shortest_paths_lite_size(
                    obj_link_network, start_node=related_nodes[1], end_node=trg_node)

                # COMPUTE THE EVIDENCE'S STRENGTH OF THE SUBJECT
                subj_r_strength = evidence_penalty(
                    investigated_diameter=sub_diameter, evidence_diameter=obj_diameter)

                # COMPUTE THE EVIDENCE'S STRENGTH OF THE OBJECT
                obj_r_strength = evidence_penalty(
                    investigated_diameter=obj_diameter, evidence_diameter=sub_diameter)

            # print '\n\t Computed strengths:'
            # print '\t\t Source start_node={}, end_node={}, strength={}'.format(
            #   related_nodes[0], src_node, subj_strength)
            # print '\t\t Target start_node={}, end_node={}, strength={}'.format(
            #   related_nodes[1], trg_node, obj_strength)

            # MAKING SURE WE HAVE THE HIGHEST WEIGHT FOR THE LINKS IN THE SHORTEST PATH
            if source_cluster not in cycle_paths or len(cycle_paths[source_cluster]) == 0:
                cycle_paths[source_cluster] = [(related_nodes[0], src_node, subj_r_strength)]
                # print '\n\t\tThe was no path-strength at all for {}, adding ({}, {}, {})'.format(
                #     source_cluster, related_nodes[0], src_node, subj_strength)

            else:
                # print '\t\tThe was some path-strengths there, ',
                add = True
                for start_n, end_n, strength in cycle_paths[source_cluster]:

                    # UPDATING AN EXISTING PATH-STRENGTH
                    if (start_n, end_n) == (related_nodes[0], src_node):

                        # THE DISCOVERED PATH IS UPDATED FOR ITS STRENGTH IS SMALLER
                        if strength < subj_r_strength:
                            list(cycle_paths[source_cluster]).remove((start_n, end_n, strength))
                            # print 'and there was this particular one with smaller strength, removing... '

                        # THE DISCOVERED PATH IS NOT UPDATED FOR ITS STRENGTH IS BIGGER OR EQUAL
                        else:
                            add = False
                            # print 'and there was this particular one with bigger or equal strength, let it there... '

                # WE REACH THIS POINT IF THE PATH WAS NOT THERE OR IF THE STRENGTH IS SMALLER AND NEEDS UPDATE
                if add is True:
                    # print 'adding new path-strength for {}, adding ({}, {}, {})'.format(
                    #   source_cluster, related_nodes[0], src_node, subj_strength)
                    cycle_paths[source_cluster] += [(related_nodes[0], src_node, subj_r_strength)]

            if target_cluster not in cycle_paths or len(cycle_paths[target_cluster]) == 0:
                # print '\n\t\tThe was no path-strength at all for {}, adding ({}, {}, {})'.format(
                #   target_cluster, related_nodes[1], trg_node, obj_strength)
                cycle_paths[target_cluster] = [(related_nodes[1], trg_node, obj_r_strength)]

            else:
                # print '\t\tThe was some path-strengths there, ',
                add = True
                for start_n, end_n, strength in cycle_paths[target_cluster]:

                    # UPDATING AN EXISTING PATH-STRENGTH
                    if (start_n, end_n) == (related_nodes[1], trg_node):

                        # THE DISCOVERED PATH IS UPDATED FOR ITS STRENGTH IS SMALLER
                        if strength < obj_r_strength:
                            list(cycle_paths[target_cluster]).remove((start_n, end_n, strength))
                            # print 'and there was this particular one with smaller strength, removing... '

                        # THE DISCOVERED PATH IS NOT UPDATED FOR ITS STRENGTH IS BIGGER OR EQUAL
                        else:
                            add = False
                            # print 'and there was this particular one with bigger or equal strength, let it there... '

                # WE REACH THIS POINT IF THE PATH WAS NOT THERE OR IF THE STRENGTH IS SMALLER AND NEEDS UPDATE
                if add is True:
                    cycle_paths[target_cluster] += [(related_nodes[1], trg_node, obj_r_strength)]
                    # print 'adding new path-strength for {}, adding ({}, {}, {})'.format(
                    # target_cluster, related_nodes[1], trg_node, obj_strength)

    # **************************************************************************************************
    # END OF HELPER CODE
    # **************************************************************************************************

    def derive_reconciliation(cluster_id, detail=False):

        print "CLUSTER: {}".format(cluster_id)
        temp = []
        investigated = reconciled_nodes[cluster_id]

        if 'links' not in investigated:
            return

        # POSSIBLE CONNECTIONS IN A DIRECTED GRAPH
        combinations = Ut.ordered_combinations(list(investigated["nodes"]))
        # NETWORK OF ALL POSSIBLE LINKS BASED ON ALL NODE RECONCILED
        network = nx.DiGraph(Ut.full_combinations(list(investigated["nodes"])))
        # print Ut.print_dict(dict_clusters_pairs)
        # print Ut.print_dict(reconciled_nodes)

        # test = nx.DiGraph(investigated["links"])
        # nx.draw(test)
        # plt.show()

        while True:
            remain = 0

            for c1, c2 in combinations:

                # THIS IS A RECONCILED LINK
                if (c1, c2, "R") in investigated["links"] or (c1, c2, "D") in investigated["links"]:
                    if detail:
                        print "\tIN: ", (c1, c2, "R/D")

                # THIS HAS NOT BEEN RECONCILED BUT CAN BE DERIVED
                else:

                    if detail:
                        print "\tOUT:", (c1, c2, "R")

                    # FIND ALL BASE CYCLE FROM THE FULLY CONNECTED GRAPH
                    base_cycles = filter(lambda x: len(x) == 3, list(nx.all_simple_paths(network, c1, c2, cutoff=2)))
                    # if len(base_cycles) > 0:
                    #     remain += 1

                    for base_cycle in base_cycles:

                        if detail:
                            print "CYCLE BASE", base_cycle

                        key_1 = Ut.get_key(base_cycle[0], base_cycle[1])
                        key_2 = Ut.get_key(base_cycle[1], base_cycle[2])

                        if key_1 in investigated["strengths"]:

                            if key_2 in investigated["strengths"]:
                                remain += 1
                                strength = max(investigated["strengths"][key_2]) * max(
                                    investigated["strengths"][key_1])
                                
                                if detail:
                                    print "\t>> Keys {} * {} = {}".format(
                                        investigated["strengths"][key_1], investigated["strengths"][key_2], strength)
                                temp += [(c1, c2, Ut.get_key(c1, c2), strength)]

                            # else:
                            #     remain = 0 if remain - 1 < 0 else remain - 1

                        # else:
                        #     remain = 0 if remain - 1 < 0 else remain - 1
            if detail:
                print "\n\t******************************************************************************\n"

            if remain == 0:
                break

            for node1, node2, link_key, strength in temp:

                # NEW LINK
                if (node1, node2, "D") not in investigated["links"]:
                    investigated["links"] += [(node1, node2, "D")]

                # NEW STRENGTH
                if link_key in investigated["strengths"]:
                    investigated["strengths"][link_key] += [strength]
                else:
                    investigated["strengths"][link_key] = [strength]
            temp = []

        if "strengths" in investigated:
            for inv_key, inv_value in investigated["strengths"].items():
                if len(inv_value) > 1:
                    investigated["strengths"][inv_key] = [max(inv_value)]

        # if detail:
        #     Ut.print_list(investigated["links"], comment="LINKS")
        #     Ut.print_dict(investigated["strengths"], comment="STRENGTHS")
            # print metric(investigated["links"], investigated["strengths"])

    # 1. FETCH THE PAIRED NODES
    # size = Qry.get_namedgraph_size(graph)
    reconciled_nodes = {}                   # ABOUT THE RECONCILED NODES
                                            # ==> BUILDING A DICT WITH NODES - LINKS - STRENGTHS
    extended_clusters = set()               # LIST OF ALL CLUSTERS THAT EXTEND
    list_extended_clusters_cycle = set()    # LIST OF ALL CLUSTERS THAT EXTENDS AND CONTAIN A CYCLES
    dict_clusters_pairs = {}
    start = time.time()

    clusters = clusters_dictionary['clusters']
    node2cluster = clusters_dictionary['node2cluster_id']
    data = {'extended_clusters': None, 'list_extended_clusters_cycle': None}
    print "\tCOMPUTING THE EXTENDED CLUSTERS DICTIONARIES AND THE LIST OF CLUSTERS IN A CYCLE..."

    if reset is True:
        print "DELETING THE SERIALISED DATA FROM: {}".format(graph)
        delete_serialised_extended_clusters(graph)

    # **************************************************************************************************
    # 1. CHECK IF THE ALIGNMENT HAS ALREADY BEEN EXTENDED
    # **************************************************************************************************
    ask = "ASK {{ <{}>  <{}extendedClusters> ?dictionary .}}".format(graph, Ns.alivocab)
    if Qry.boolean_endpoint_response(ask) == "true":

        print "\n>>> THE CLUSTER EXTENSION HAS ALREADY BEEN SERIALISED, WAIT A SEC WHILE WE FETCH IT."

        # QUERY FOR THE SERIALISATION
        s_query = """SELECT *
        {{
            <{0}>   <{1}extendedClusters>   ?serialised .
        }}""".format(graph, Ns.alivocab)
        start = time.time()

        # FETCH THE SERIALISATION
        s_query_result = Qry.sparql_xml_to_matrix(s_query)[St.result]

        # Qry.display_result(s_query, is_activated=True)
        diff = datetime.timedelta(seconds=time.time() - start)
        print "\tLOADED in {}".format(diff)

        # GET THE SERIALISED CLUSTERS
        # serialised = ""
        if s_query_result is not None:

            # EXTRACTING THE NUMBER OF CLUSTERS ABD THE SERIALISED FILE NAME
            serialised_hash = s_query_result[1][0]
            print "\tEXTENDED CLUSTERS FOUND AND DATA SAVED IN THE FILE \n\t\v [{}.txt]\n".format(serialised_hash)

            # EXTRACTING DATA FROM THE HASHED DICTIONARY FILE
            start = time.time()

            # DE-SERIALISE THE SERIALISED
            try:
                de_serialised = {'cycle_paths': {}, 'reconciled': {}}
                s_file = os.path.join(serialisation_dir, "{}".format(serialised_hash)) + "-{}.txt"

                with open(s_file.format(1), 'rb') as writer:
                    start_de = time.time()
                    de_serialised['extended_clusters'] = ast.literal_eval(writer.read())
                    print "DONE DE-SERIALISING ['extended_clusters'] in {}".format(
                        datetime.timedelta(seconds=time.time() - start_de))

                with open(s_file.format(2), 'rb') as writer:
                    start_de = time.time()
                    de_serialised['list_extended_clusters_cycle'] = ast.literal_eval(writer.read())
                    print "DONE DE-SERIALISING ['list_extended_clusters_cycle'] in {}".format(
                        datetime.timedelta(seconds=time.time() - start_de))

                with open(s_file.format(3), 'rb') as reader:
                    start_de = time.time()
                    count_line = 0
                    for line in reader:
                        count_line += 1
                        start_de_2 = time.time()
                        de_serialised['cycle_paths'].update(ast.literal_eval(line))
                        print "> CYCLE PATHS LINE {} DE-SERIALISED IN {}".format(
                            count_line, datetime.timedelta(seconds=time.time() - start_de_2))
                    print "\tDONE DE-SERIALISING ['cycle_paths'] in {}".format(
                        datetime.timedelta(seconds=time.time() - start_de))

                with open(s_file.format(4), 'rb') as reader:
                    start_de = time.time()
                    count_line = 0
                    for line in reader:
                        count_line += 1
                        start_de_2 = time.time()
                        de_serialised['reconciled'].update(ast.literal_eval(line))
                        print "> LINE {} DE-SERIALISED IN {}".format(
                            count_line, datetime.timedelta(seconds=time.time() - start_de_2))
                    print "\tDONE DE-SERIALISING ['reconciled'] in {}".format(
                        datetime.timedelta(seconds=time.time() - start_de))

                diff = datetime.timedelta(seconds=time.time() - start)

                print "DE-SERIALISED IN  {}".format(diff)
                print "\nJOB DONE!!!\nDATA RETURNED TO THE CLIENT SIDE TO BE PROCESSED FOR DISPLAY\n"
                return de_serialised

            except (IOError, ValueError) as err:
                print err.message
                print "\nRE-RUNNING IT ALL BECAUSE THE SERIALISED FILE [{}].txt COULD NOT BE FOUND.".format(
                    serialised_hash)
                # traceback.print_exc()
                print "DELETING THE EXTENDED SERIALISED SERIALISED DATA FROM: {}".format(graph)
                delete_serialised_extended_clusters(graph)

    # **************************************************************************************************
    # 2. ALIGNMENT HAS NOT YET BEEN EXTENDED AND SERIALISED
    # **************************************************************************************************

    if True:
        cycle_paths = {}
        print "\tFETCHING THE RELATED ALIGNMENT TRIPLES"
        fetch_q = """
        select distinct ?sub ?obj
        {{
             GRAPH <{}>
            {{
               {{ ?sub ?pred ?obj . }}
                union
               {{ ?obj ?pred ?sub . }}
               filter (str(?sub) < str(?obj))
            }}
        }}""".format(related_linkset)
        fetched_res = Qry.sparql_xml_to_matrix(fetch_q)
        related = fetched_res[St.result]
        size = len(related)
        print "\t\tRELATED LINKSET SIZE: {}\n\tCOMPUTING THE EXTENSIONS\n".format(size - 1)

        # 2.1 ITERATE THROUGH THE PAIRED FOR EXTENSIONS
        #     ITERATING THROUGH THE RELATED LIST OF NODES
        # *******************************************
        for i in range(1, size):

            print '\r', "{} / {}".format(i, size),

            # RELATED NODES
            sub = "<{}>".format(related[i][0])
            obj = "<{}>".format(related[i][1])

            # CHECK WHETHER EACH SIDE BELONG TO A CLUSTER
            if sub in node2cluster and obj in node2cluster:

                # FETCH THE CLUSTER ID OF THE NODES IN THE ASSOCIATION
                src_cluster_id = node2cluster[sub]
                trg_cluster_id = node2cluster[obj]

                # ****************************************************************
                # TO SAVE TIME, WE DO NOT EVALUATE CLUSTERS OF SIZE BIGGER THAN 30
                # ****************************************************************
                condition = \
                    len(clusters[src_cluster_id]['nodes']) <= 30 and len(clusters[trg_cluster_id]['nodes']) <= 30

                if condition is False:
                    continue

                # condition = src_cluster == 'N6849355419779822524' or trg_cluster == 'N6849355419779822524'
                # if condition is False:
                #     continue

                # list_extended_clusters_cycle IS THE LIST OF ALL CLUSTERS THAT EXTEND AND HAVE A CYCLE
                if src_cluster_id != trg_cluster_id:

                    # **********************************************************************************
                    # 1. CHECKING FOR EXTENSION
                    # IF THE CLUSTER TO WHICH THE NODES BELONG ARE NOT THE SAME THEN THE CLUSTERS EXTEND
                    # **********************************************************************************
                    # extended_clusters IS THE LIST OF ALL CLUSTERS THAT EXTEND
                    extended_clusters.add(src_cluster_id)
                    extended_clusters.add(trg_cluster_id)

                    # **********************************************************************************
                    # CHECKING AND DOCUNENTING CYCLES IN A SPECIFIC ORDER TO MAKE SURE OF A UNIQUE LIST
                    # **********************************************************************************
                    # print '\r', "\tLINE: {}".format(i),
                    if src_cluster_id < trg_cluster_id:

                        if (src_cluster_id, trg_cluster_id) in dict_clusters_pairs.keys():

                            # IT HAS A CYCLE
                            list_extended_clusters_cycle.add(src_cluster_id)
                            list_extended_clusters_cycle.add(trg_cluster_id)

                            # DOCUMENTING THE CYCLE START AND END FOR THIS SPECIFIC ORDER
                            cycle_helper(
                                src_node=sub, trg_node=obj,
                                source_cluster=src_cluster_id, target_cluster=trg_cluster_id)

                            # DOCUMENTING THE EXTENDED CLUSTERS AND RELATED NODES THAT EXTEND THE CLUSTERS
                            dict_clusters_pairs[(src_cluster_id, trg_cluster_id)] += [(sub, obj)]

                            # for related_nodes in dict_clusters_pairs[(src_cluster, trg_cluster)]:
                            #
                            #     # COMPUTE THE SHORTEST PATH SIZE (DIAMETER) FOR THESE START AND END NODES (SUBJECT)
                            #     sub_link_network = clusters[src_cluster]['links']
                            #     sub_diameter = shortest_paths_lite(
                            #         sub_link_network, start_node=related_nodes[0], end_node=sub)
                            #
                            #     # COMPUTE THE SHORTEST PATH SIZE FOR T(DIAMETER) THESE START AND END NODES (TARGET)
                            #     obj_link_network = clusters[trg_cluster]['links']
                            #     obj_diameter = shortest_paths_lite(
                            #         obj_link_network, start_node=related_nodes[1], end_node=obj)
                            #
                            #     # COMPUTE THE EVIDENCE'S STRENGTH OF THE SUBJECT
                            #     subj_strength = evidence_penalty(
                            #         investigated_diameter=sub_diameter, evidence_diameter=obj_diameter)
                            #
                            #     # COMPUTE THE EVIDENCE'S STRENGTH OF THE OBJECT
                            #     obj_strength = evidence_penalty(
                            #         investigated_diameter=obj_diameter, evidence_diameter=sub_diameter)
                            #
                            #     # MAKING SURE WE HAVE THE HIGHEST WEIGHT FOR THE LINKS IN THE SHORTEST PATH
                            #     if len(cycle_paths[src_cluster]) == 0:
                            #         cycle_paths[src_cluster] += [(related_nodes[0], sub, subj_strength)]
                            #
                            #     else:
                            #         for start_n, end_n, strength in cycle_paths[src_cluster]:
                            #             if (start_n, end_n) == (related_nodes[0], sub) and strength < subj_strength:
                            #                 list(cycle_paths[src_cluster]).remove((start_n, end_n, strength))
                            #                 cycle_paths[src_cluster] += [(related_nodes[0], sub, subj_strength)]
                            #
                            #
                            #     if len(cycle_paths[trg_cluster]) == 0:
                            #         cycle_paths[trg_cluster] += [(related_nodes[1], obj, obj_strength)]
                            #
                            #     else:
                            #         for start_n, end_n, strength in cycle_paths[trg_cluster]:
                            #             if (start_n, end_n) == (related_nodes[1], obj) and strength < obj_strength:
                            #                 list(cycle_paths[trg_cluster]).remove((start_n, end_n, strength))
                            #                 cycle_paths[trg_cluster] += [(related_nodes[1], obj, obj_strength)]

                            #     cycle_paths[curr_sub_cluster] += [(related_nodes[0], sub)]
                            #     cycle_paths[curr_obj_cluster] += [(related_nodes[1], obj)]

                        else:
                            # WE DO NOT USE THE VALUE OF THE DICTIONARY SO ITS EMPTY
                            # DOCUMENTING FIRST OCCURRENCE
                            dict_clusters_pairs[(src_cluster_id, trg_cluster_id)] = [(sub, obj)]

                    else:

                        if (trg_cluster_id, src_cluster_id) in dict_clusters_pairs.keys():

                            # IT HAS A CYCLE
                            list_extended_clusters_cycle.add(src_cluster_id)
                            list_extended_clusters_cycle.add(trg_cluster_id)

                            # DOCUMENTING THE CYCLE START AND END FOR THIS SPECIFIC ORDER
                            cycle_helper(
                                src_node=obj, trg_node=sub,
                                source_cluster=trg_cluster_id, target_cluster=src_cluster_id)

                            # DOCUMENTING THE EXTENDED CLUSTERS AND RELATED NODES THAT EXTEND THE CLUSTERS
                            dict_clusters_pairs[(trg_cluster_id, src_cluster_id)] += [(obj, sub)]

                        else:
                            # WE DO NOT USE THE VALUE OF THE DICTIONARY SO ITS EMPTY
                            # DOCUMENTING FIRST OCCURRENCE
                            dict_clusters_pairs[(trg_cluster_id, src_cluster_id)] = [(obj, sub)]

        # 2.2 EXTRACT ALL RECONCILED NODES PER EXTENDED CLUSTER
        #     INSTANTIATING reconciled_nodes WITH THE NODES
        # **************************************************

        for key, value in reconciled_nodes.items():
            links = value['links']
            nodes = list(set([data[0] for data in links] + [data[1] for data in links]))
            reconciled_nodes[key]['nodes'] = nodes

        # for key, value in dict_clusters_pairs.items():
        #
        #     if key[0] not in reconciled_nodes:
        #         reconciled_nodes[key[0]] = {"nodes": set()}
        #         for item in value:
        #             reconciled_nodes[key[0]]["nodes"].add(item[0])
        #     else:
        #         if "nodes" not in reconciled_nodes[key[0]]:
        #             reconciled_nodes[key[0]]["nodes"] = set()
        #             for item in value:
        #                 reconciled_nodes[key[0]]["nodes"].add(item[0])
        #         else:
        #             for item in value:
        #                 reconciled_nodes[key[0]]["nodes"].add(item[0])
        #
        #     if key[1] not in reconciled_nodes:
        #         reconciled_nodes[key[1]] = {"nodes": set()}
        #         for item in value:
        #             reconciled_nodes[key[1]]["nodes"].add(item[1])
        #     else:
        #         if "nodes" not in reconciled_nodes[key[1]]:
        #             reconciled_nodes[key[1]]["nodes"] = set()
        #             for item in value:
        #                 reconciled_nodes[key[1]]["nodes"].add(item[1])
        #         else:
        #             for item in value:
        #                 reconciled_nodes[key[1]]["nodes"].add(item[1])

        # ***********************************************************
        # 2.3 COMPUTING THE DERIVED RECONCILIATION STRENGTHS
        # ***********************************************************
        print "*** COMPUTING THE DERIVED STRENGTHS ***"
        for key in reconciled_nodes.keys():
            # reconciled_nodes[key]['nodes'] = list(reconciled_nodes[key]['nodes'])
            derive_reconciliation(key, detail=False)
            # print key
        # derive_reconciliation('P1935396683', detail=True)
        # derive_reconciliation('N1096153044', detail=True)
        # Ut.print_dict(reconciled_nodes)

        # BUILDING UP CLUSTER DATA
        related_graph_mane = Ut.get_uri_local_name_plus(related_linkset)
        c_data = []
        for key, reconciled in reconciled_nodes.items():
            strengths = reconciled['strengths']
            for link in reconciled['links']:
                c_data += [(link[0], link[1], strengths[Ut.get_key(link[0], link[1])])]

        # Ut.print_list(c_data)

        links_list_clustering(c_data, serialisation_dir, reconciled_name=reconciled_name, stop_at=None)

        diff = datetime.timedelta(seconds=time.time() - start)
        print "\n\t\tFOUND: {} IN {}".format(len(extended_clusters), diff)
        print "\t\tFOUND: {} CYCLES".format(len(list_extended_clusters_cycle))

        if len(extended_clusters) != 0 and len(list_extended_clusters_cycle) != 0:

            # SERIALISATION
            data = {'extended_clusters': list(extended_clusters),
                    'list_extended_clusters_cycle': list(list_extended_clusters_cycle),
                    'cycle_paths': cycle_paths}
            file_name = "ExtendedBy_{}".format(related_graph_mane)
            # file_name = file_name.replace("-", "Cluster_N") \
            #     if file_name.startswith("-") else "Cluster_P{}".format(file_name)

            # ***************************************************************************************************
            print "\n5. SERIALISING THE EXTENDED CLUSTERS DICTIONARIES AND THE LIST OF CLUSTERS IN A CYCLE..."
            # ***************************************************************************************************
            s_file_1 = os.path.join(serialisation_dir, "{}-1.txt".format(file_name))
            s_file_2 = os.path.join(serialisation_dir, "{}-2.txt".format(file_name))
            s_file_3 = os.path.join(serialisation_dir, "{}-3.txt".format(file_name))
            s_file_4 = os.path.join(serialisation_dir, "{}-4.txt".format(file_name))

            with open(s_file_1, 'wb') as writer:
                writer.write(data['extended_clusters'].__str__())

            with open(s_file_2, 'wb') as writer:
                writer.write(data['list_extended_clusters_cycle'].__str__())

            with open(s_file_3, 'wb') as writer:

                cluster_limit = 1000
                counting = 0
                sub_cluster = {}

                for key, value in cycle_paths.items():
                    counting += 1
                    sub_cluster[key] = value

                    if counting == cluster_limit:
                        writer.write(sub_cluster.__str__() + "\n")
                        sub_cluster = {}
                        counting = 0

                if counting != 0:
                    writer.write(sub_cluster.__str__() + "\n")

            with open(s_file_4, 'wb') as writer:

                cluster_limit = 1000
                counting = 0
                sub_cluster = {}

                for key, value in reconciled_nodes.items():
                    counting += 1
                    sub_cluster[key] = value

                    if counting == cluster_limit:
                        writer.write(sub_cluster.__str__() + "\n")
                        sub_cluster = {}
                        counting = 0

                if counting != 0:
                    writer.write(sub_cluster.__str__() + "\n")

            print "\n6. SAVING THE HASH OF EXTENDED CLUSTERS TO THE TRIPLE STORE AS: {}".format(file_name)
            Qry.endpoint("""INSERT DATA {{
            <{0}> <{1}extendedClusters> '''{2}''' .
            }}""".format(graph, Ns.alivocab, file_name))

            print "\n7. SERIALISATION IS COMPLETED..."
            diff = datetime.timedelta(seconds=time.time() - start)
            print "\t{} triples serialised in {}".format(size, diff)

            print "\nJOB DONE!!!\nDATA RETURNED TO THE CLIENT SIDE TO BE PROCESSED FOR DISPLAY\n"

        else:
            print "\tTHE RETURNED DICTIONARY IS EMPTY."

    return data


def fetch_paired(nodes_list, linkset):
    picked_nodes_csv = "\n\t\t\t".join(str(s) for s in nodes_list)
    query = """
        SELECT ?node ?pred ?paired
        {{
            VALUES ?node {{
                {0} }}

            # NODE PAIRED TO THE LINKSET FROM OBJECT
            {{
                GRAPH <{1}>
                {{
                    ?paired ?pred ?node .
                }}
            }}UNION

            # NODE PAIRED TO THE LINKSET FROM SUBJECT
            {{
                GRAPH <{1}>
                {{
                    ?node ?pred ?paired .
                }}
            }}
        }}
                """.format(picked_nodes_csv, linkset)
    # print query
    query_response = Qry.sparql_xml_to_matrix(query=query)
    # Qry.display_result(query, is_activated=True)
    return query_response[St.result]


# RETURNS ALL POSSIBLE SHORTEST PATHS
def shortest_paths_lite(link_network, start_node, end_node, strengths=None):

    # print "\nCOMPUTING PATH USING [shortest_paths_lite]..."

    diameter = 0

    # EXTRACT THE NODES FROM THE NETWORK OF LINKS
    nodes = set([data[0] for data in link_network] + [data[1] for data in link_network])

    # INSTANTIATE THE GRAPH
    g = nx.Graph()

    # add nodes
    for node in nodes:
        g.add_node(node)

    # add edges
    for edge in link_network:
        g.add_edge(edge[0], edge[1])

    # GET THE SHORTEST PATH (THE FUNCTION RETURNS ONLY ONE PATH)
    # print "GRAPH-1:", g.__str__()
    # print "\t\t\v ", start_node, "AND", end_node
    result = nx.shortest_path(g, source=start_node, target=end_node)
    diameter = len(result) - 1
    # print "RESULT-1:", result
    results = []

    # FIND OTHER PATHS OF THE SAME SIZE
    if result is not None:

        results = [result]
        size = len(result)
        diameter = size - 1

        # for each of the results of same size found, remove edges to try and find other paths
        for result in results:
            # print result
            partials = []

            # for each pair in the path, remove the link and check the shortest path and add it again
            for i in range(len(result)-1):
                # print "removing ", result[i], ', ', result[i+1]
                # print "GRAPH-2:", g.__str__()
                # print start_node, "AND" , end_node
                g.remove_edge(result[i], result[i+1])
                # print "REMOVED:", result[i], result[i+1]
                try:
                    partial = nx.shortest_path(g, source=start_node, target=end_node)

                except IOError:
                    partial = []

                except nx.NetworkXNoPath:
                    partial = []

                # if there is a path of same size, keep it in a set (there can be repetition)
                if len(partial) == size:
                    if partial not in partials:
                        partials += [partial]

                g.add_edge(result[i], result[i+1])

            # add whatever paht found if so
            for p in partials:
                if p not in results:
                    results += [p]
            # print 'new paths: ', partials

    # NOW WE HAVE ALL POSSIBLE SHORTEST PATHS
    weighted_paths = []
    for path in results:
        weight = 0
        for i in range(0, diameter):
            link = (path[i], path[i + 1]) if path[i] < path[i + 1] else (path[i + 1], path[i])
            key = "key_{}".format(str(hash(link)).replace("-", "N"))
            # print "strengths:", strengths[key]
            weight += max(map(float, strengths[key]))
        weighted_paths += [weight]

    weighted_diameter = max(weighted_paths) if len(weighted_paths) > 0 else 0

    return diameter, weighted_diameter


def shortest_paths_lite_size(link_network, start_node, end_node):

    print "COMPUTING SHORTEST PATH USING [shortest_paths_lite]..."

    # EXTRACT THE NODES FROM THE NETWORK OF LINKS
    nodes = set([data[0] for data in link_network] + [data[1] for data in link_network])

    # INSTANTIATE THE GRAPH
    g = nx.Graph()

    # add nodes
    for node in nodes:
        g.add_node(node)

    # add edges
    for edge in link_network:
        g.add_edge(edge[0], edge[1])

    # GET THE SHORTEST PATH (THE FUNCTION RETURNS ONLY ONE PATH)
    # THE PATH IS A SET OF NODES IN SEQUENCE
    result = nx.shortest_path(g, source=start_node, target=end_node)

    if result is not None:
        return len(result) - 1
    else:
        return 0


def cluster_extension(nodes, node2cluster, linkset):

    """
    :param nodes:           THE SET OF NODES RELATED BY A SAME AS LINK.
    :param node2cluster:    A DICTIONARY {NODE: CLUSTER-ID} MAPPING A CLUSTER IDEA TO TO ALL NODES IN THE MATHER CLUSTER
    :param linkset:         THE LINKSET USED FOR EXTENDING A CLUSTER STEMMED FROM THE MOTHER CLUSTER
    :return:                A DICTIONARY {'links': links, 'extensions': list(set(extension))}
    """
    # ***********************************************************************************
    # CLUSTER EXTENSION
    # THIS FUNCTION TRIES TO BRIDGE AN EXISTING CLUSTER WITH OTHER CLUSTERS BASED ON
    # A GIVEN SET OF CONNECTING LINKS. THE LINKS ARE SUPPOSED TO CONNECT NODES OF THE
    # EXISTING CLUSTER WITH NODE ON THE OTHER SIDE OF THE LINK HOPPING THAT THE OTHER
    # SIDE IS A CLUSTER.
    # ***********************************************************************************

    print "\t> CHECKING FOR EXTENSION"

    # 1. PICK A CLUSTER
    # picked_cluster = clusters[clusters.keys()[0]]
    # picked_nodes_csv = picked_cluster['nodes']
    picked_nodes_csv = "\n\t\t\t".join(str(s) for s in nodes)

    # 2. FETCH THE PAIRED NODE FOR EACH NODE IN THE CLUSTER
    query = """
    SELECT ?node ?pred ?paired
    {{
        VALUES ?node {{
            {0} }}

        # NODE PAIRED TO THE LINKSET FROM OBJECT
        {{
            GRAPH <{1}>
            {{
                ?paired ?pred ?node .
            }}
        }}UNION

        # NODE PAIRED TO THE LINKSET FROM SUBJECT
        {{
            GRAPH <{1}>
            {{
                ?node ?pred ?paired .
            }}
        }}
    }}
            """.format(picked_nodes_csv, linkset)
    # print query
    query_response = Qry.sparql_xml_to_matrix(query=query)
    query_result = query_response[St.result]
    # Qry.display_result(query, is_activated=True)

    # 3. FOR EACH PARED NOD, EXTRACT THE CLUSTER ID THE NODE BELONGS TO
    extension = []
    links = []
    if query_result is not None:
        for i in range(1, len(query_result)):
            node = "<{}>".format(query_result[i][0])
            paired = "<{}>".format(query_result[i][2])
            links += [(node, paired)]
            if paired in node2cluster:
                extension += [node2cluster[paired]]

    # EXTENSION IS THE LIST OF CLUSTER ID THAT EXTEND THE GIVEN CLUSTER
    to_return = {'links': links, 'extensions': list(set(extension))}
    print "\tNUMBER OF LINKS FOUND:", len(links)
    print "\tNUMBER OF EXTENSION IDS FOUND", len(to_return['extensions'])
    for ex_id in to_return['extensions']:
        print "\t\t", ex_id
    print "\tTHE EXTENSION:", to_return

    return to_return


def cluster_links_between_extension(nodes, linkset):

    """
    :param nodes:           THE SET OF NODES RELATED BY A SAME AS LINK.
    :param linkset:         THE LINKSET USED FOR EXTENDING A CLUSTER STEMMED FROM THE MOTHER CLUSTER
    :return:                A DICTIONARY {'links': links, 'extensions': list(set(extension))}
    """
    # ***********************************************************************************
    # THIS FUNCTION CHECKS FOR LINKS BETWEEN A GIVEN ET OF NODES
    # THE GOAL IS TO VERIFY IF THE EXTESIONS OF A CLUSTER ARE LINKED AMONG THEM
    # ***********************************************************************************

    print "\n\t> CHECKING FOR LINKS BETWEEN THE NODES OF THE EXTESIONS"

    picked_nodes_csv = "\n\t\t\t".join(str(s) for s in nodes)

    # EXTRACT LINKS BETWEEN THE GIVEN NODES
    query = """
    SELECT ?node1 ?pred ?node2
    {{
        VALUES ?node1 {{
            {0} }}

        VALUES ?node2 {{
            {0} }}

        # LINKS BETWEEN THE GIVEN NODES
        {{
            GRAPH <{1}>
            {{
                ?node1 ?pred ?node2 .
            }}
        }}
    }}
            """.format(picked_nodes_csv, linkset)
    # print query
    query_response = Qry.sparql_xml_to_matrix(query=query)
    query_result = query_response[St.result]
    # Qry.display_result(query, is_activated=True)

    links = []
    if query_result is not None:
        for i in range(1, len(query_result)):
            node1 = "<{}>".format(query_result[i][0])
            node2 = "<{}>".format(query_result[i][2])
            links += [(node1, node2)]

    print "\tNUMBER OF LINKS FOUND:", len(links)

    return links


def delete_serialised_clusters(graph):
    query = """
    delete
    {{
        <{0}> <{1}serialisedClusters> ?serialised .
        <{0}> <{1}numberOfClusters> ?numberOfClusters .
    }}

    where
    {{
        <{0}> <{1}serialisedClusters> ?serialised .
        <{0}> <{1}numberOfClusters> ?numberOfClusters .
    }}
    """.format(graph, Ns.alivocab)
    Qry.endpoint(query=query)
    print "DONE1!!"


def delete_serialised_extended_clusters(graph):
    query = """
    delete
    {{
        <{0}> <{1}extendedClusters> ?serialised .
    }}

    where
    {{
        <{0}> <{1}extendedClusters> ?serialised .
    }}
    """.format(graph, Ns.alivocab)
    Qry.endpoint(query=query)
    print "DONE1!!"


def evidence_penalty(investigated_diameter, evidence_diameter, penalty_percentage=10):

    penalty = (100 - penalty_percentage * (evidence_diameter - 1)) / float(100)
    return 0 if penalty < 0 else (1 / float(investigated_diameter)) * penalty


def reconciliation_strength(sim, ev_diameter, ev_w_diameter, c_penalty=10):

    # print "\t\t>>> SIM DATA:", "sim = ", "ev_diameter = ", ev_diameter, "ev_W_diameter = ", ev_w_diameter
    validation_strength = (100 - c_penalty * (2 * ev_diameter - ev_w_diameter - 1)) / float(100)
    strength = min(sim, validation_strength) if sim > 0 else validation_strength
    # print "\t\t>>> RECONCILED:", 0 if strength < 0 else strength
    return 0 if strength < 0 else strength


def list_extended_clusters_short_problem(node2cluster, related_linkset):
    print ">>> RUNNING THE FUNCTION [list_extended_clusters_short_problem]"
    # 1. FETCH THE PAIRED NODES
    extended_clusters = set()
    list_extended_clusters_cycle = set()
    dict_clusters_pairs = {}
    start = time.time()
    fetch_q = """
    select distinct ?sub ?obj
    {{
         GRAPH <{}>
        {{
           {{ ?sub ?pred ?obj . }}
            union
           {{ ?obj ?pred ?sub . }}
           filter (str(?sub) < str(?obj))
        }}

    }}""".format(related_linkset)
    print "FETCHING THE RELATED ALIGNMENT TRIPLES"
    fetched_res = Qry.sparql_xml_to_matrix(fetch_q)
    fetched = fetched_res[St.result]

    # ITERATE THROUGH THE PAIRED FOR ExTENSIONS
    print "\tRELATED LINKSET SIZE: {}\nCOMPUTING THE EXTENSIONS.\nTHIS MAY TAKE A WHILE...".format(len(fetched) - 1)
    for i in range(1, len(fetched)):
        sub = "<{}>".format(fetched[i][0])
        obj = "<{}>".format(fetched[i][1])

        # CHECK WHETHER EACH SIDE BELONG TO A CLUSTER
        if sub in node2cluster and obj in node2cluster:

            curr_sub_cluster = node2cluster[sub]
            curr_obj_cluster = node2cluster[obj]

            # extended_clusters IS THE LIST OF ALL CLUSTERS THAT EXTEND
            # list_extended_clusters_cycle IS THE LIST OF ALL CLUSTERS THAT EXTEND AND HAVE A CYCLE
            if curr_sub_cluster != curr_obj_cluster:
                extended_clusters.add(curr_sub_cluster)
                extended_clusters.add(curr_obj_cluster)

                if (curr_sub_cluster, curr_obj_cluster) in dict_clusters_pairs.keys():
                    # IT HAS A CYCLE
                    list_extended_clusters_cycle.add(curr_sub_cluster)
                    list_extended_clusters_cycle.add(curr_obj_cluster)

                else:
                    # WE DO NOT USE THE VALUE OF THE DICTIONARY SO ITS EMPTY
                    # DOCUMENTING FIRST OCCURRENCE
                    dict_clusters_pairs[(curr_sub_cluster, curr_obj_cluster)] = ""
                    dict_clusters_pairs[(curr_obj_cluster, curr_sub_cluster)] = ""

    diff = datetime.timedelta(seconds=time.time() - start)
    print "\tFOUND: {} IN {}".format(len(extended_clusters), diff)
    print "\tFOUND: {} CYCLES".format(len(list_extended_clusters_cycle))

    return extended_clusters, list_extended_clusters_cycle


def list_extended_clusters_long(serialised_path, related_linkset):

    print ">>> RUNNING THE FUNCTION [list_extended_clusters_long]"
    # s_file = open(os.path.join(serialisation_dir, "{}.txt".format(serialised_path)), 'rb')
    s_file = open(serialised_path, 'rb')

    # 1. READ FROM FILE
    try:
        print '\nREADING FROM: {}'.format(serialised_path)
        serialised = s_file.read()

    except (IOError, ValueError):
        print "\nCAN NOT GO ANY FURTHER AS THE SERIALISED FILE [{}].txt COULD NOT BE FOUND.".format(s_file)

    else:
        # 2. DE-SERIALISE THE SERIALISED CLUSTERS DICTIONARY
        start = time.time()
        de_serialised = ast.literal_eval(serialised)
        diff = datetime.timedelta(seconds=time.time() - start)

        clusters = de_serialised['clusters']
        node2cluster = de_serialised['node2cluster_id']
        print "\tLOADED in {}, THE FILE CONTAINS {}.".format(diff, len(clusters))

        # 3. FETCH THE PAIRED NODES
        extended_clusters = set()
        # pre_extended_pair_clusters = set()
        list_extended_clusters_cycle = set()
        dict_clusters_pairs = {}
        start = time.time()
        fetch_q = """
        select distinct ?sub ?obj
        {{
             GRAPH <{}>
            {{
               {{ ?sub ?pred ?obj . }}
                union
               {{ ?obj ?pred ?sub . }}
               filter (str(?sub) < str(?obj))
            }}

        }}""".format(related_linkset)
        fetched_res = Qry.sparql_xml_to_matrix(fetch_q)
        fetched = fetched_res[St.result]

        # ITERATE THROUGH THE PAIRED FOR EXTENSIONS
        print "\tRELATED LINKSET SIZE: {}".format(len(fetched) - 1)
        for i in range(1, len(fetched)):
            sub = "<{}>".format(fetched[i][0])
            obj = "<{}>".format(fetched[i][1])

            # CHECK WHETHER EACH SIDE BELONG TO A CLUSTER
            if sub in node2cluster and obj in node2cluster:
                if node2cluster[sub] != node2cluster[obj]:
                    extended_clusters.add(node2cluster[sub])
                    extended_clusters.add(node2cluster[obj])

                    if node2cluster[sub] < node2cluster[obj]:
                        if (node2cluster[sub], node2cluster[obj]) in dict_clusters_pairs.keys():
                            dict_clusters_pairs[(node2cluster[sub], node2cluster[obj])].add((sub, obj))
                            # s
                        else:
                            dict_clusters_pairs[(node2cluster[sub],node2cluster[obj])] = set([(sub, obj)])
                    else:
                        if (node2cluster[obj],node2cluster[sub]) in dict_clusters_pairs.keys():
                            dict_clusters_pairs[(node2cluster[obj], node2cluster[sub])].add((sub, obj))
                            # s.add((sub,obj))
                        else:
                            dict_clusters_pairs[(node2cluster[obj], node2cluster[sub])] = set([(sub, obj)])

                    # if node2cluster[sub] < node2cluster[obj]:
                    #     if (node2cluster[sub],node2cluster[obj]) in pre_extended_pair_clusters:
                    #         list_extended_clusters_cycle.add(node2cluster[sub])
                    #         list_extended_clusters_cycle.add(node2cluster[obj])
                    #     else:
                    #         pre_extended_pair_clusters.add((node2cluster[sub],node2cluster[obj]))
                    # else:
                    #     if (node2cluster[obj],node2cluster[sub]) in pre_extended_pair_clusters:
                    #         list_extended_clusters_cycle.add(node2cluster[sub])
                    #         list_extended_clusters_cycle.add(node2cluster[obj])
                    #     else:
                    #         pre_extended_pair_clusters.add((node2cluster[obj],node2cluster[sub]))

        for cluster_pair, node_pairs in dict_clusters_pairs.items():
            if len(node_pairs) > 1:
                list_extended_clusters_cycle.add(cluster_pair[0])
                list_extended_clusters_cycle.add(cluster_pair[1])

        diff = datetime.timedelta(seconds=time.time() - start)
        print "\tFOUND: {} IN {}".format(len(extended_clusters), diff)
        print "\tFOUND: {} CYCLES".format(len(list_extended_clusters_cycle))

        return extended_clusters, list_extended_clusters_cycle


def list_extended_clusters0(serialised_path, related_linkset):

    # s_file = open(os.path.join(serialisation_dir, "{}.txt".format(serialised_path)), 'rb')
    s_file = open(serialised_path, 'rb')

    # 1. READ FROM FILE
    try:
        print '\nREADING FROM: {}'.format(serialised_path)
        serialised = s_file.read()

    except (IOError, ValueError):
        print "\nCAN NOT GO ANY FURTHER AS THE SERIALISED FILE [{}].txt COULD NOT BE FOUND.".format(s_file)

    else:
        # 2. DE-SERIALISE THE SERIALISED CLUSTERS DICTIONARY
        start = time.time()
        de_serialised = ast.literal_eval(serialised)
        diff = datetime.timedelta(seconds=time.time() - start)

        clusters = de_serialised['clusters']
        node2cluster = de_serialised['node2cluster_id']
        print "\tLOADED in {}, THE FILE CONTAINS {}.".format(diff, len(clusters))

        # 3. FETCH THE PAIRED NODES
        extended_clusters = []
        found = 0
        start = time.time()
        for cluster_id in clusters:
            nodes = clusters[cluster_id]['nodes']
            query_result = fetch_paired(nodes, linkset=related_linkset)

            if query_result is not None:
                # print "CLUSTER IS NOT NONE"
                for i in range(1, len(query_result)):
                    # node = "<{}>".format(query_result[i][0])
                    # paired = "<{}>".format(query_result[i][2])

                    if "<{}>".format(query_result[i][2]) in node2cluster:
                        extended_clusters += [cluster_id]
                        found += 1
                        break
        diff = datetime.timedelta(seconds=time.time() - start)
        print "\tFOUND: {} IN {}".format(found, diff)

        return extended_clusters
    # ITERATE THROUGH THE CLUSTERS AND EXTRACT THOSE WITH EXTENSION

"""""""""
# TESTING THE CLUSTER ANALYSIS
"""""""""
# def cluster_test(linkset, network_size=3, greater_equal=True, limit=5000):
#
#     count_1 = 0
#     count_2 = 0
#
#     print ""
#
#     linkset = linkset.strip()
#
#     # RUN THE CLUSTER
#     clusters_0 = cluster_links(linkset, limit)
#
#     for i_cluster in clusters_0.items():
#
#         network = []
#         count_1 += 1
#         children = i_cluster[1][St.children]
#         # if "<http://www.grid.ac/institutes/grid.10493.3f>" not in children:
#         #     continue
#
#         check = len(children) >= network_size if greater_equal else len(children) == network_size
#
#         if check:
#             count_2 += 1
#
#             print "\nCLUSTER {:>3}: {}: with size: {}".format(count_1, i_cluster[0], len(children))
#             for child in children:
#                 print "\t{}".format(child)
#
#             print "\nDISAMBIGUATION HELPER"
#             disambiguate_network(linkset, children)
#
#             position = i_cluster[1][St.row]
#             print "\nANNOTATED CLUSTER PROCESS"
#             print i_cluster[1][St.annotate]
#
#             # THE CLUSTER
#             # print "POSITION: {}".format(position)
#             print "\nMATRIX DISPLAY\n"
#             for i in range(0, position):
#                 resource = (i_cluster[1][St.matrix])[i]
#                 print "\t{}".format(resource[:position])
#                 # print "\t{}".format(resource)
#
#             # THE MATRIX
#             for i in range(1, position):
#                 for j in range(1, position):
#                     if (i_cluster[1][St.matrix])[i][j] != 0:
#                         r = (i_cluster[1][St.matrix])[i][0]
#                         c = (i_cluster[1][St.matrix])[0][j]
#                         # r_name = r[-25:]
#                         # c_name = c[-25:]
#                         r_name = "{}:{}".format(i, Ut.get_uri_local_name(r))
#                         c_name = "{}:{}".format(j, Ut.get_uri_local_name(c))
#                         # r_smart = {"key": i, "name": r_name}
#                         # c_smart = {"key": j, "name": c_name}
#                         network += [(r_name, c_name)]
#                         # network += [(r_smart, c_smart)]
#
#             print ""
#             # print "\tNETWORK", network
#             Plt.draw_graph(network)
#
#     print "FOUND: {}".format(count_2)


# WORKING ONE

"""""""""
TO DELETE FROM THE FILE
"""""""""
# # LINKSET CLUSTERING
# def cluster_links(graph):
#
#     count = 0
#     clusters = dict()
#     root = dict()
#
#     # DOWNLOAD THE GRAPH
#     print "\n0. DOWNLOADING THE GRAPH"
#     response = Exp.export_alignment(graph)
#     links = response['result']
#     # print links
#
#     # LOAD THE GRAPH
#     print "1. LOADING THE GRAPH"
#     g = rdflib.Graph()
#     g.parse(data=links, format="turtle")
#     # g = [
#     #     ("<http://grid.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgref.2>"),
#     #     ("<http://leiden.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://grid.2>"),
#     #     ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgreg.2>"),
#     #     ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://h2020.2> "),
#     #     ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://eter.2>"),
#     #     ("<http://eter.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://leiden.2>"),
#     # ]
#
#     g = [
#         ("<http://grid.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgref.2>"),
#         ("<http://eter.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://leiden.2>"),
#         ("<http://orgreg.2> ", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://h2020.2> "),
#         ("<http://leiden.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://grid.2>"),
#         ("<http://orgref.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://orgreg.2>"),
#         ("<http://h2020.2>", "<http://risis.eu/alignment/predicate/SAMEAS>", "<http://eter.2>"),
#     ]
#
#     print "2. ITERATING THROUGH THE GRAPH OF SIZE {}".format(len(g))
#     for subject, predicate, obj in g:
#
#         count += 1
#         # child_1 = subject.n3().strip()
#         # child_2 = obj.n3().strip()
#
#         child_1 = subject.strip()
#         child_2 = obj.strip()
#         # parent = ""
#
#         # DATE CREATION
#         date = "{}".format(datetime.datetime.today().strftime(_format))
#
#         # CHECK WHETHER A CHILD HAS A PARENT
#         has_parent_1 = True if child_1 in root else False
#         has_parent_2 = True if child_2 in root else False
#         # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)
#
#         # BOTH CHILD ARE ORPHANS
#         if has_parent_1 is False and has_parent_2 is False:
#
#             print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
#
#             # GENERATE THE PARENT
#             hash_value = hash(date + str(count) + graph)
#             parent = "{}".format(str(hash_value).replace("-", "N")) if str(hash_value).startswith("-") \
#                 else "P{}".format(hash_value)
#
#             # ASSIGN A PARENT TO BOTH CHILD
#             root[child_1] = parent
#             root[child_2] = parent
#
#             # CREATE A CLUSTER
#             if parent not in clusters:
#
#                 # MATRIX
#                 mx = matrix(150, 150)
#                 # ROW
#                 mx[0][1] = child_1
#                 mx[0][2] = child_2
#                 # COLUMNS
#                 mx[1][0] = child_1
#                 mx[2][0] = child_2
#                 # RELATION
#                 # mx[1][2] = 1
#                 mx[2][1] = 1
#
#                 clusters[parent] = {St.children: [child_1, child_2], St.matrix: mx, St.row: 3}
#
#             print "\tPOSITION: {}".format(3)
#             print "\tIT WILL BE PRINTED AT: ({}, {})".format(2, 1)
#
#         # BOTH CHILD HAVE A PARENT OF THEIR OWN
#         elif has_parent_1 is True and has_parent_2 is True:
#
#             # IF BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
#             if root[child_1] == root[child_2]:
#                 # print "CLUSTER SIZE IS {} BUT THERE IS NOTHING TO DO\n".format(len(clusters))
#                 print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
#
#                 print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
#                 cur_mx = clusters[root[child_1]][St.matrix]
#
#                 row_1 = 0
#                 row_2 = 0
#
#                 # FIND ROW
#                 # row_1 = clusters[root[child_1]][St.row]
#                 for row in range(1, clusters[root[child_1]][St.row]):
#                     if cur_mx[row][0] == child_1:
#                         row_1 = row
#
#                 for col in range(1, clusters[root[child_1]][St.row]):
#                     if cur_mx[0][col] == child_2:
#                         row_2 = col
#
#                 # row_2 = clusters[root[child_2]][St.row]
#
#                 print "\tPOSITIONS: {} | {}".format(row_2, row_1)
#                 cur_mx[row_2][row_1] = 1
#
#
#                 # row_1 = clusters[root[child_1]][St.row]
#                 # row_2 = clusters[root[child_2]][St.row]
#                 #
#                 # print "\tPOSITION: {}".format(row_1)
#                 # print "\tPOSITION: {}".format(row_2)
#                 #
#                 # # COPY THE SUB-MATRIX
#                 # cur_mx = clusters[root[child_1]][St.matrix]
#                 # for col in range(1, row_1):
#                 #     if cur_mx[0][col] == child_2:
#                 #         print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
#                 #         print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
#                 #         cur_mx[row_1 - 1][col] = 1
#
#                 continue
#
#             # THE PARENT WITH THE MOST CHILD GET THE CHILD OF THE OTHER PARENT
#             # fFETCHING THE RESOURCES IN THE CLUSTER (CHILDREN)
#             print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
#
#             children_1 = (clusters[root[child_1]])[St.children]
#             children_2 = (clusters[root[child_2]])[St.children]
#
#             # CHOOSE A PARENT
#             if len(children_1) >= len(children_2):
#                 print "\tPARENT 1"
#                 parent = root[child_1]
#                 pop_parent = root[child_2]
#                 # root[child_2] = parent
#
#             else:
#                 print "\tPARENT 2"
#                 parent = root[child_2]
#                 pop_parent = root[child_1]
#                 # root[child_1] = parent
#
#             # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
#             for offspring in clusters[pop_parent][St.children]:
#                 root[offspring] = parent
#                 clusters[parent][St.children] += [offspring]
#
#             merge_matrices(clusters, parent, pop_parent)
#
#             # COPYING LESSER MATRIX TO BIGGER MATRIX
#             # index = clusters[parent][St.row]
#             # pop_row = clusters[pop_parent][St.row]
#             # cur_mx = clusters[parent][St.matrix]
#             # pop_mx = clusters[pop_parent][St.matrix]
#             # # position_add = clusters[parent][St.row] - 1
#             #
#             # print "\tPOSITION: {} | POSITION POP: {}".format(index, pop_row)
#             # # print "\tADD VALUE: {}".format(position_add)
#             #
#             # # # ADD HEADER
#             # # for x in range(1, pop_index):
#             # #     cur_mx[0][index - 1 + x] = pop_mx[0][x]
#             # #     cur_mx[index - 1 + x][0] = pop_mx[0][x]
#             # #     clusters[parent][St.row] += 1
#             #
#             # # COPY MATRIX
#             # print "\tPOP HEADER: {}".format(pop_mx[0][:])
#             # for row in range(1, pop_row):
#             #
#             #     # ADD HEADER IF NOT ALREADY IN
#             #     # print "\tCURREENT HEADER ADDED: {}".format(cur_mx[0:])
#             #     if pop_mx[row][0] not in cur_mx[0:]:
#             #         pop_item_row = pop_mx[row][0]
#             #         cur_mx[index][0] = pop_item_row
#             #         cur_mx[0][index] = pop_item_row
#             #         index += 1
#             #         clusters[parent][St.row] = index
#             #         print "\tHEADER ADDED: {}".format(pop_item_row)
#             #
#             #
#             #         # FOR THAT HEADER, COPY THE SUB-MATRIX
#             #         for col in range(1, pop_row):
#             #
#             #             # THE HEADER IS NOT IN
#             #             if pop_mx[row][col] != 0 and pop_mx[row][0] not in cur_mx[1:-1]:
#             #                 print "\tIN ({}, {})".format(index-1, col )
#             #                 # index += 1
#             #                 # clusters[parent][St.row] = index
#             #
#             #             # THE HEADER ARE ALREADY IN THERE
#             #             if pop_mx[row][col] != 0:
#             #                 # find header in current matrix
#             #                 for col_item in range(1, len(cur_mx[1:-1])):
#             #                     if cur_mx[0][col_item] == pop_mx[0][col]:
#             #                         print "\tIN2 ({}, {})".format(index-1, col_item)
#                             # cur_mx[row + position_add][col + position_add] = pop_mx[row][col]
#
#
#                             # cur_mx[0][position_add+ row] = pop_mx[row][0]
#
#                             # cur_mx[y + position_add][x + position_add] = pop_mx[y][x]
#
#             # POP THE PARENT WITH THE LESSER CHILD
#             clusters.pop(pop_parent)
#
#         elif has_parent_1 is True:
#
#             # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
#             print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
#
#             parent = root[child_1]
#             root[child_2] = parent
#             clusters[parent][St.children] += [child_2]
#             print "\t>>> {} is in root {}".format(child_2, child_2 in root)
#
#             cur_mx = clusters[parent][St.matrix]
#             row_1 = clusters[parent][St.row]
#
#             # ADD HEADER
#             cur_mx[row_1][0] = child_2
#             cur_mx[0][row_1] = child_2
#
#             # INCREMENT POSITION
#             row_1 += 1
#             print "\tPOSITION: {}".format(row_1)
#             clusters[parent][St.row] = row_1
#
#             # COPY MATRIX
#             for col in range(1, row_1):
#                 # print cur_mx[0][x], child_1
#                 if cur_mx[0][col] == child_1:
#                     print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
#                     print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_1 - 1, col)
#                     # cur_mx[position_1 - 1][x] = 1
#                     cur_mx[row_1 - 1][col] = 1
#
#         elif has_parent_2 is True:
#
#             # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
#             print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)
#
#             parent = root[child_2]
#             root[child_1] = parent
#             clusters[parent][St.children] += [child_1]
#             print "\t>>> {} is in root {}".format(child_1, child_1 in root)
#
#             cur_mx = clusters[parent][St.matrix]
#             row_2 = clusters[parent][St.row]
#
#             # ADD HEADER
#             cur_mx[row_2][0] = child_1
#             cur_mx[0][row_2] = child_1
#
#
#             # INCREMENT POSITION
#             row_2 += 1
#             print "\tPOSITION: {}".format(row_2)
#             clusters[parent][St.row] = row_2
#
#             # COPY MATRIX
#             for col in range(1, row_2):
#                 # print cur_mx[0][x], child_1
#                 if cur_mx[0][col] == child_2:
#                     print "\tFOUND: {} AT POSITION: {}".format(cur_mx[0][col], col)
#                     print "\tIT WILL BE PRINTED AT: ({}, {})".format(row_2 - 1, col)
#                     # cur_mx[position_2 - 1][x] = 1
#                     cur_mx[row_2 - 1][col] = 1
#
#         # print "{} Clusters but the current is: {}\n".format(len(clusters), clusters[parent])
#     print "\n3. NUMBER OF CLUSTER FOND: {}".format(len(clusters))
#     return clusters


# linkset_1 = "http://risis.eu/linkset/clustered_exactStrSim_N167245093"
# linkset_2 = "http://risis.eu/linkset/clustered_exactStrSim_N1245679810818748702"
# linkset_3 = "http://risis.eu/linkset/clustered_test"
#
# rsrd_list = ["<http://risis.eu/orgref_20170703/resource/1389122>",
#              "<http://risis.eu/cordisH2020/resource/participant_993809912>",
#              "<http://www.grid.ac/institutes/grid.1034.6>"]
#
# # print disambiguate_network(linkset_1, rsrd_list)
# cluster_test(linkset_2, network_size=4, limit=1000)

" >>> CLUSTERING RESOURCES BASED ON COUNTRY CODE"
# groups0 = cluster_triples("http://risis.eu/dataset/grid_country")
# count = 0
# print ""
# for cluster1 in groups0.items():
#
#     count += 1
#     country = None
#     for instance in cluster1[1]:
#         if str(instance).__contains__("http://") is False:
#             country = instance
#     if country is not None:
#         print "{} in {} {}".format(cluster1[0], country, len(cluster1[1]))
# exit(0)

" >>> COMPARE LINKSET FOR MERGED CLUSTERS"
# groups1 = cluster_triples(
#     "http://risis.eu/linkset/orgref_20170703_grid_20170712_approxStrSim_Organisation_Name_N221339442")
# groups2 = cluster_triples(
#     "http://risis.eu/linkset/orgref_20170703_grid_20170712_approxStrSim_Organisation_Name_N212339613")
# counter = 0
# print ""
# for cluster1 in groups1.items():
#     counter += 1
#     stop = False
#     outer = "CLUSTER {} of size {}".format(cluster1[0], len(cluster1[1]))
#
#     # for instance in cluster1[1]:
#     #     print "\t{}".format(instance)
#
#     for instance in cluster1[1]:
#         for other_cluster in groups2.items():
#             if instance in other_cluster[1]:
#                 stop = True
#                 inner = "LINKED TO CLUSTER {} OF SIZE {}".format(other_cluster[0], len(other_cluster[1]))
#                 if len(cluster1[1]) != len(other_cluster[1]):
#                     print "{} {}".format(outer, inner)
#                 # for o_cluster in other_cluster[1]:
#                 #     print "\t\t\t{}".format(o_cluster)
#             if stop:
#                 break
#     if counter == 5000:
#         break

#     if len(item['cluster']) > 1:
#         print "\n{:10}\t{:3}\t{}".format(item['parent'], len(item['cluster']), item['sample'])

# test = [('x','y'), ('x','B'), ('w','B'), ('x','w'), ('e','d'), ('e','y'),
# ('s', 'w'),('a','b'),('h','j'),('k','h'),('k','s'),('s','a')]
# clus= cluster(test)
# for key, value in clus.items():
#     print "{} {}".format(key, value)

# test = cluster_triples("http://risis.eu/linkset/subset_openAire_20170816_openAire_20170816_"
#                        "embededAlignment_Organization_sameAs_P541043043")

# groups = cluster_dataset("http://risis.eu/dataset/grid_20170712", "http://xmlns.com/foaf/0.1/Organization")
# properties = ["http://www.w3.org/2004/02/skos/core#prefLabel", "{}label".format(Ns.rdfs)]
# for key, value in groups.items():
#     if len(value) > 15:
#         print "\n{:10}\t{:3}".format(key, len(value))
#         response = cluster_values(value, properties)
#         exit(0)

# groups = cluster_dataset("http://goldenagents.org/datasets/Ecartico", "http://ecartico.org/ontology/Person")
# # print groups
# properties = ["http://ecartico.org/ontology/full_name", "http://goldenagents.org/uva/SAA/ontology/full_name"]
# counter = 0
# for key, value in groups.items():
#     if len(value) > 15:
#         print "\n{:10}\t{:3}".format(key, len(value))
#         response = cluster_values(value, properties, display=True)
#         if counter > 5:
#             exit(0)
#         counter +=1

# groups = cluster_triples2("http://risis.eu/linkset/refined_003MarriageRegistries_Ecartico_exactStrSim_Person_full_"
#                           "name_N3531703432838097870_approxNbrSim_isInRecord_registration_date_P0")
# counter = 0
# for item in groups:
#     if len(item['cluster']) > 1:
#         print "\n{:10}\t{:3}\t{}".format(item['parent'], len(item['cluster']), item['sample'])


# links_clustering("", limit=1000)
