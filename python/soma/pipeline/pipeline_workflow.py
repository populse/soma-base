#!/usr/bin/env python


'''Capsul Pipeline conversion into soma-workflow workflow.

A single available function:
workflow = workflow_from_pipeline(pipeline)
'''

import soma_workflow.client as swclient
from soma.pipeline import Pipeline
from soma.process import Process
from soma.pipeline.topological_sort import Graph


def workflow_from_pipeline(pipeline):
    '''Create a soma-workflow workflow from a Capsul Pipeline
    '''

    def build_job(name, process):
        command = ['sleep', '1']
        job = swclient.Job(name=name, command=command)
        return job

    def build_group(name, jobs):
        group = swclient.Group(jobs, name=name)
        return group

    def get_jobs(group, groups):
        gqueue = list(group.elements)
        jobs = []
        while gqueue:
            group_or_job = gqueue.pop(0)
            if group_or_job in groups:
                gqueue += group_or_job.elements
            else:
                jobs.append(group_or_job)
        return jobs

    def workflow_from_graph(graph):
        jobs = {}
        groups = {}
        root_jobs = {}
        root_groups = {}
        dependencies = set()
        group_nodes = {}

        for node_name, node in graph._nodes.iteritems():
            sub_jobs = {}
            if isinstance(node.meta, Graph):
                group_nodes[node_name] = node
            else:
                for process in node.meta:
                    if not isinstance(process, Pipeline) \
                            and isinstance(process, Process):
                        job = build_job(process.name, process)
                        sub_jobs[process] = job
                        root_jobs[process] = job
                        node.job = job
                jobs.update(sub_jobs)

        for node_name, node in group_nodes.iteritems():
            wf_graph = node.meta
            sub_jobs, sub_deps, sub_groups, sub_root_groups, sub_root_jobs \
                = workflow_from_graph(wf_graph)
            group = build_group(node_name,
                sub_root_groups.values() + sub_root_jobs.values())
            groups[node.meta] = group
            root_groups[node.meta] = group
            jobs.update(sub_jobs)
            groups.update(sub_groups)
            dependencies.update(sub_deps)

        groups_val = groups.values()
        for node_name, node in graph._nodes.iteritems():
            if isinstance(node.meta, list) and node.meta[0] in jobs:
                sjobs = [jobs[node.meta[0]]]
            else:
                sjobs = get_jobs(groups[node.meta], groups_val)
            djobs = []
            for dnode in node.links_to:
                if isinstance(dnode.meta, list) and dnode.meta[0] in jobs:
                    djobs.append(jobs[dnode.meta[0]])
                else:
                    djobs = get_jobs(groups[dnode.meta], groups_val)
            for sjob in sjobs:
                for djob in djobs:
                    dependencies.add((sjob, djob))

        return jobs, dependencies, groups, root_groups, root_jobs

    # get a graph
    graph = pipeline.workflow_graph()
    jobs, dependencies, groups, root_groups, root_jobs \
        = workflow_from_graph(graph)
    # TODO: root_group would need reordering according to dependencies
    # (maybe using topological_sort)
    workflow = swclient.Workflow(jobs=jobs.values(),
        dependencies=dependencies,
        root_group=root_groups.values() + root_jobs.values(),
        name=pipeline.name)

    return workflow
