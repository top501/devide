# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkDiscreteMarchingCubes(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkDiscreteMarchingCubes(), 'Processing.',
            ('vtkImageData',), ('vtkPolyData',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
