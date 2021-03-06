# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkImageChangeInformation(SimpleVTKClassModuleBase):
    def __init__(self, module_manager):
        SimpleVTKClassModuleBase.__init__(
            self, module_manager,
            vtk.vtkImageChangeInformation(), 'Processing.',
            ('vtkImageData', 'vtkImageData'), ('vtkImageData',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
