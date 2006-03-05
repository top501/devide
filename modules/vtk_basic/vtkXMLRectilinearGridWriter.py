# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkXMLRectilinearGridWriter(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkXMLRectilinearGridWriter(), 'Writing vtkXMLRectilinearGrid.',
            ('vtkXMLRectilinearGrid',), (),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)