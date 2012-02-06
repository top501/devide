# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkMergeTables(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkMergeTables(), 'Processing.',
            ('vtkTable', 'vtkTable'), ('vtkTable',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
