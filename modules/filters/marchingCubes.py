from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk


class marchingCubes(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):

        # call parent constructor
        ModuleBase.__init__(self, module_manager)

        self._contourFilter = vtk.vtkMarchingCubes()

        module_utils.setup_vtk_object_progress(self, self._contourFilter,
                                           'Extracting iso-surface')
        

        # now setup some defaults before our sync
        self._config.iso_value = 128

        config_list = [
            ('ISO value:', 'iso_value', 'base:float', 'text',
             'Surface will pass through points with this value.')]
        ScriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self,
             'vtkMarchingCubes' : self._contourFilter})

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        self.set_input(0, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._contourFilter

    def get_input_descriptions(self):
	return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._contourFilter.SetInput(inputStream)

    def get_output_descriptions(self):
	return (self._contourFilter.GetOutput().GetClassName(),)
    

    def get_output(self, idx):
        return self._contourFilter.GetOutput()

    def logic_to_config(self):
        self._config.iso_value = self._contourFilter.GetValue(0)

    def config_to_logic(self):
        self._contourFilter.SetValue(0, self._config.iso_value)

    def execute_module(self):
        self._contourFilter.Update()
        

