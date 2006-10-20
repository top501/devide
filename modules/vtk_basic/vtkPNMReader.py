# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkPNMReader(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkPNMReader(), 'Reading vtkPNM.',
            (), ('vtkPNM',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
