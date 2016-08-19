###############################################################################
##
## Copyright (C) 2011-2013, NYU-Poly.
## Copyright (C) 2006-2011, University of Utah. 
## All rights reserved.
## Contact: contact@vistrails.org
##
## This file is part of VisTrails.
##
## "Redistribution and use in source and binary forms, with or without 
## modification, are permitted provided that the following conditions are met:
##
##  - Redistributions of source code must retain the above copyright notice, 
##    this list of conditions and the following disclaimer.
##  - Redistributions in binary form must reproduce the above copyright 
##    notice, this list of conditions and the following disclaimer in the 
##    documentation and/or other materials provided with the distribution.
##  - Neither the name of the University of Utah nor the names of its 
##    contributors may be used to endorse or promote products derived from 
##    this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
###############################################################################
from vistrails.db.versions.v1_0_4.domain import DBVistrail, \
    DBWorkflow, DBLog, DBRegistry, DBAdd, DBChange, DBDelete, DBAbstraction, \
    DBGroup, DBModule, DBActionAnnotation, DBAnnotation, DBLoopExec, \
    DBModuleExec, DBGroupExec, DBAction, IdScope, SaveBundle

import copy
import unittest

def check_id_types(vistrail):
    def getOldObjId(operation):
        if operation.vtType == 'change':
            return operation.db_oldObjId
        return operation.db_objectId

    def getNewObjId(operation):
        if operation.vtType == 'change':
            return operation.db_newObjId
        return operation.db_objectId

    for action in vistrail.db_actions:
        if not isinstance(action.db_id, ( int, long )):
            print "ACTION:", action.db_id
        if not isinstance(action.db_session, (int, long)):
            print "SESSION", action.db_session
        for operation in action.db_operations:
            if not isinstance(operation.db_id, (int, long)):
                print "OPERATION", operation.vtType, operation.db_id
            if operation.vtType == 'add' or operation.vtType == 'change':
                # update ids of data
                if not isinstance(getNewObjId(operation), (int, long)):
                    print "OPDATA", operation.db_what, getNewObjId(operation)
        for annotation in action.db_annotations:
            if not isinstance(annotation.db_id, (int, long)):
                print "ANNOTATION", annotation.db_id

    for annotation in vistrail.db_annotations:
        if not isinstance(annotation.db_id, (int, long)):
            print "ANNOTATION", annotation.db_id
    for annotation in vistrail.db_actionAnnotations:
        if not isinstance(annotation.db_id, (int, long)):
            print "ANNOTATION", annotation.db_id
    for paramexp in vistrail.db_parameter_explorations:
        if not isinstance(paramexp.db_id, (int, long)):
            print "ANNOTATION", paramexp.db_id

def translateVistrail(_vistrail, external_data=None):
    if external_data is not None and "id_remap" in external_data:
        id_remap = external_data["id_remap"]
    else:
        id_remap = {}
    if external_data is not None and "group_remaps" in external_data:
        group_remaps = external_data["group_remaps"]
    else:
        group_remaps = {}
    if external_data is not None and "translate_dict" in external_data:
        translate_dict = copy.copy(external_data["translate_dict"])
    else:
        translate_dict = {}

    def update_workflow(old_obj, trans_dict):
        if old_obj.db_id in group_remaps:
            group_remap = group_remaps[old_obj.db_id]
        else:
            group_remap = {}

        group_data = {"translate_dict": trans_dict,
                      "id_remap": group_remap}
        workflow = translateWorkflow(old_obj.db_workflow, group_data)
        group_remaps[old_obj.db_id] = group_data["id_remap"]
        return workflow

    if 'DBGroup' not in translate_dict:
        translate_dict['DBGroup'] = {'workflow': update_workflow}

    root_action_t = (DBAction.vtType, "00000000-0000-0000-0000-000000000000")
    if root_action_t not in id_remap:
        id_remap[root_action_t] = 0

    vistrail = DBVistrail()
    id_scope = vistrail.idScope
    vistrail = DBVistrail.update_version(_vistrail, translate_dict, vistrail, False)
    # FIXME have to eventually expand the inner workflows and update their ids
    vistrail = vistrail.do_copy(True, id_scope, id_remap)

    # remap upgrade annotations
    for ann in vistrail.db_actionAnnotations[:]:
        if ann.db_key == "__upgrade__": # vistrails.core.vistrail.vistrail.Vistrail.UPDATE_ANNOTATION
            vistrail.db_delete_actionAnnotation(ann)
            ann.db_value = "%d" % id_remap[(DBAction.vtType, ann.db_value)]
            vistrail.db_add_actionAnnotation(ann)

    vistrail.db_version = '1.0.4'
    return vistrail

def translateWorkflow(_workflow, external_data=None):
    if external_data is not None and "id_remap" in external_data:
        id_remap = external_data["id_remap"]
    else:
        id_remap = {}
    if external_data is not None and "group_remaps" in external_data:
        group_remaps = external_data["group_remaps"]
    else:
        group_remaps = {}
    if external_data is not None and "translate_dict" in external_data:
        translate_dict = external_data["translate_dict"]
    else:
        translate_dict = {}

    def update_workflow(old_obj, trans_dict):
        if old_obj.db_id in group_remaps:
            group_remap = group_remaps[old_obj.db_id]
        else:
            group_remap = {}

        group_data = {"translate_dict": trans_dict,
                      "id_remap": group_remap}
        workflow = translateWorkflow(old_obj.db_workflow, group_data)
        group_remaps[old_obj.db_id] = group_data["id_remap"]
        return workflow

    if 'DBGroup' not in translate_dict:
        translate_dict['DBGroup'] = {'workflow': update_workflow}

    workflow = DBWorkflow()
    id_scope = IdScope(remap={DBAbstraction.vtType: DBModule.vtType, DBGroup.vtType: DBModule.vtType})
    workflow = DBWorkflow.update_version(_workflow, translate_dict, workflow)
    workflow = workflow.do_copy(True, id_scope, id_remap)
    workflow.db_version = '1.0.4'
    return workflow

def translateLog(_log, external_data=None):
    if external_data is not None and "id_remap" in external_data:
        id_remap = external_data["id_remap"]
    else:
        id_remap = {}
    if external_data is not None and "translate_dict" in external_data:
        translate_dict = external_data["translate_dict"]
    else:
        translate_dict = {}

    log = DBLog()
    id_scope = log.id_scope
    log = DBLog.update_version(_log, translate_dict, log)
    log = log.do_copy(True, id_scope, id_remap)
    log.db_version = '1.0.4'
    return log

def translateRegistry(_registry, external_data=None):
    if external_data is not None and "id_remap" in external_data:
        id_remap = external_data["id_remap"]
    else:
        id_remap = {}
    if external_data is not None and "translate_dict" in external_data:
        translate_dict = external_data["translate_dict"]
    else:
        translate_dict = {}

    registry = DBRegistry()
    id_scope = registry.idScope
    registry = DBRegistry.update_version(_registry, translate_dict, registry, False)
    registry = registry.do_copy(True, id_scope, id_remap)
    registry.db_version = '1.0.4'
    return registry

def translateBundle(_bundle, external_data=None):
    if external_data is not None and "translate_dict" in external_data:
        translate_dict = external_data["translate_dict"]
    else:
        translate_dict = {}

    def remove_non_unique(extdata, non_unique):
        new_remap = {}
        for ((t, k1), k2) in extdata["id_remap"].iteritems():
            if t not in non_unique:
                # check for idscope remap here...
                new_remap[(t, k1)] = k2
        extdata["id_remap"] = new_remap

    def copy_extdata(extdata):
        return {k: copy.copy(v) for k,v in extdata.iteritems()}

    def update_extdata(extdata, updates):
        for k,v in updates.iteritems():
            if k in extdata:
                extdata[k].update(v)
            else:
                extdata[k] = v

    bundle_contents = {}

    if external_data is not None and "vistrail_extdata" in external_data:
        vistrail_extdata = external_data["vistrail_extdata"]
    else:
        vistrail_extdata = None
    if external_data is not None and "workflow_extdata" in external_data:
        workflow_extdata = external_data["workflow_extdata"]
    else:
        workflow_extdata = None
    if external_data is not None and "log_extdata" in external_data:
        log_extdata = external_data["log_extdata"]
    else:
        log_extdata = None
    if _bundle.vistrail is not None:
        if vistrail_extdata is None:
            vistrail_extdata = {"id_remap": {}, "group_remaps": {}}
        _vistrail = _bundle.vistrail
        vistrail = translateVistrail(_vistrail, vistrail_extdata)
        bundle_contents['vistrail'] = vistrail

    if _bundle.workflow is not None:
        if workflow_extdata is None:
            workflow_extdata = {"id_remap": {}, "group_remaps": {}}
        if vistrail_extdata is not None:
            vt_extdata = copy_extdata(vistrail_extdata)
            remove_non_unique(vt_extdata, set()) # nothing for wf
            #FIXME allow vistrail to clobber workflow ids?
            # if materialization is direct, this should be better
            update_extdata(workflow_extdata, vt_extdata)

        _workflow = _bundle.workflow
        workflow = translateWorkflow(_workflow, workflow_extdata)
        bundle_contents['workflow'] = workflow

    abstractions = []
    for _abstraction in _bundle.abstractions:
        # convert abstractions
        # should just be able to run vistrail translation...
        pass

    for mashup in _bundle.mashups:
        # convert mashups
        pass

    # FIXME abstractions and mashups may affect log
    if _bundle.log is not None:
        if log_extdata is None:
            log_extdata = {"id_remap": {}, "group_remaps": {}}
        if vistrail_extdata is not None:
            vt_extdata = copy_extdata(vistrail_extdata)
            remove_non_unique(vt_extdata, set([DBAnnotation.vtType]))
            update_extdata(log_extdata, vt_extdata)
        elif workflow_extdata is not None:
            wf_extdata = copy_extdata(workflow_extdata)
            remove_non_unique(wf_extdata, set())
            update_extdata(log_extdata, wf_extdata)

        _log = _bundle.log
        log = translateLog(_log, log_extdata)
        bundle_contents['log'] = log

    if _bundle.registry is not None:
        if external_data is not None and "registry_extdata" in external_data:
            registry_extdata = external_data["registry_extdata"]
        else:
            registry_extdata = {"id_remap": {}}
        _registry = _bundle.registry
        registry = translateRegistry(_registry, registry_extdata)
        bundle_contents['registry'] = registry


    # FIXME set version in bundle
    return SaveBundle(_bundle.bundle_type,
                      **bundle_contents)