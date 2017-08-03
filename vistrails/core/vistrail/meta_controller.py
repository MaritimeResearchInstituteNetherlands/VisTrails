import vistrails.core.db.io
from vistrails.core.vistrail.vistrail import MetaVistrail
from vistrails.core.vistrail.controller import VistrailController

class MetaVistrailController(VistrailController):
    def __init__(self, *args, **kwargs):
        VistrailController.__init__(self, *args, **kwargs)
        self.vt_controller = None

    def change_selected_version(self, new_version, report_all_errors=True,
                                do_validate=True, from_root=False):
        self.do_version_switch(new_version, report_all_errors,
                               do_validate, from_root)

    def do_version_switch(self, new_version, report_all_errors=False,
                          do_validate=True, from_root=False):
        """ do_version_switch(new_version: int,
                              resolve_all_errors: boolean) -> None
        Change the current vistrail version into new_version, reporting
        either the first error or all errors.

        """
        new_error = None
        self.current_vistrail = self.get_vistrail(new_version,
                                          # do_validate=do_validate,
                                          # from_root=from_root,
                                          # use_current=True
                                        )
        self.current_version = new_version
        self.vt_controller.update_vistrail(self.current_vistrail)

    def get_vistrail(self, version):
        return self.vistrail.getVistrail(version)

    def add_new_action(self, action, description=None, session=None):
        # create meta action that includes action using current meta version
        # as previd
        # need to create add op that has action embedded
        # action needs to reference current vistrail's prev id

        # keep the original vistrail intact in sub controller

        if action is not None:
            if self.current_version == -1:
                self.change_selected_version(MetaVistrail.ROOT_VERSION)

            meta_action = \
                vistrails.core.db.io.create_action([('add', action)], False)
            self.vistrail.add_action(meta_action, self.current_version,
                                     session)
            if description is not None:
                self.vistrail.change_description(description, meta_action.id)
            self.current_version = meta_action.db_id
            self.set_changed(True)
            self.recompute_terse_graph()
            return meta_action