# $Id$

from module_base import ModuleBase
from module_mixins import FilenameViewModuleMixin
import module_utils
import vtk


class plyRDR(FilenameViewModuleMixin, ModuleBase):

    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)

        self._reader = vtk.vtkPLYReader()

        # ctor for this specific mixin
        FilenameViewModuleMixin.__init__(
            self,
            'Select a filename',
            '(Stanford) Polygon File Format (*.ply)|*.ply|All files (*)|*',
            {'vtkPLYReader': self._reader,
             'Module (self)' : self})

        module_utils.setup_vtk_object_progress(
            self, self._reader,
            'Reading PLY PolyData')

        # set up some defaults
        self._config.filename = ''

        # there is no view yet...
        self._module_manager.sync_module_logic_with_config(self)
        
    def close(self):
        del self._reader
        FilenameViewModuleMixin.close(self)

    def get_input_descriptions(self):
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('vtkPolyData',)
    
    def get_output(self, idx):
        return self._reader.GetOutput()

    def logic_to_config(self):
        filename = self._reader.GetFileName()
        if filename == None:
            filename = ''

        self._config.filename = filename

    def config_to_logic(self):
        self._reader.SetFileName(self._config.filename)

    def view_to_config(self):
        self._config.filename = self._getViewFrameFilename()

    def config_to_view(self):
        self._setViewFrameFilename(self._config.filename)
    
    def execute_module(self):
        # get the vtkPLYReader to try and execute
        if len(self._reader.GetFileName()):
            self._reader.Update()