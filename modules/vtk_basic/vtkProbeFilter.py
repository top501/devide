# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkProbeFilter(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkProbeFilter(), 'Processing.',
            ('vtkDataSet', 'vtkDataSet'), ('vtkDataSet',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
