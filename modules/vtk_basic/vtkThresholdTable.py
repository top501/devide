# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkThresholdTable(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkThresholdTable(), 'Processing.',
            ('vtkTable',), ('vtkTable',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
