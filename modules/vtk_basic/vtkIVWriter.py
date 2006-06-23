# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkIVWriter(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkIVWriter(), 'Writing vtkIV.',
            ('vtkIV',), (),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
