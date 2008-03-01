# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkOpenFOAMReader(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkOpenFOAMReader(), 'Reading vtkOpenFOAM.',
            (), ('vtkOpenFOAM',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
