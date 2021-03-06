# surfaceToDistanceField copyright (c) 2004 by Charl P. Botha cpbotha.net
# $Id$

import gen_utils
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class surfaceToDistanceField(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._implicitModeller = vtk.vtkImplicitModeller()

        module_utils.setup_vtk_object_progress(
            self, self._implicitModeller,
            'Converting surface to distance field')
                                           
        self._config.bounds = (-1, 1, -1, 1, -1, 1)
        self._config.dimensions = (64, 64, 64)
        self._config.maxDistance = 0.1
        
        configList = [
            ('Bounds:', 'bounds', 'tuple:float,6', 'text',
             'The physical location of the sampled volume in space '
             '(x0, x1, y0, y1, z0, z1)'),
            ('Dimensions:', 'dimensions', 'tuple:int,3', 'text',
             'The number of points that should be sampled in each dimension.'),
            ('Maximum distance:', 'maxDistance', 'base:float', 'text',
             'The distance will only be calculated up to this maximum.')]

        ScriptedConfigModuleMixin.__init__(
            self, configList,
            {'Module (self)' : self,
             'vtkImplicitModeller' : self._implicitModeller})

        self.sync_module_logic_with_config()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._implicitModeller

    def get_input_descriptions(self):
        return ('Surface (vtkPolyData)',)

    def set_input(self, idx, inputStream):
        self._implicitModeller.SetInput(inputStream)
        
    def get_output_descriptions(self):
        return ('Distance field (VTK Image Data)',)

    def get_output(self, idx):
        return self._implicitModeller.GetOutput()

    def logic_to_config(self):
        self._config.bounds = self._implicitModeller.GetModelBounds()
        self._config.dimensions = self._implicitModeller.GetSampleDimensions()
        self._config.maxDistance = self._implicitModeller.GetMaximumDistance()
        
    def config_to_logic(self):
        self._implicitModeller.SetModelBounds(self._config.bounds)
        self._implicitModeller.SetSampleDimensions(self._config.dimensions)
        self._implicitModeller.SetMaximumDistance(self._config.maxDistance)
    
    def execute_module(self):
        self._implicitModeller.Update()


