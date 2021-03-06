import gen_utils
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class DilateExample(ScriptedConfigModuleMixin, ModuleBase):

    """Performs a greyscale 3D dilation on the input.
    
    $Revision: 1.2 $
    """
    
    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)


        self._imageDilate = vtk.vtkImageContinuousDilate3D()
        
        module_utils.setup_vtk_object_progress(self, self._imageDilate,
                                           'Performing greyscale 3D dilation')
        
                                           
        self._config.kernelSize = (3, 3, 3)


        configList = [
            ('Kernel size:', 'kernelSize', 'tuple:int,3', 'text',
             'Size of the kernel in x,y,z dimensions.')]
        ScriptedConfigModuleMixin.__init__(self, configList)        
        

        self._viewFrame = self._createWindow(
            {'Module (self)' : self,
             'vtkImageContinuousDilate3D' : self._imageDilate})

        # pass the data down to the underlying logic
        self.config_to_logic()
        # and all the way up from logic -> config -> view to make sure
        self.logic_to_config()
        self.config_to_view()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of all display thingies
        ScriptedConfigModuleMixin.close(self)

        ModuleBase.close(self)
        
        # get rid of our reference
        del self._imageDilate

    def get_input_descriptions(self):
        return ('vtkImageData',)

    def set_input(self, idx, inputStream):
        self._imageDilate.SetInput(inputStream)

    def get_output_descriptions(self):
        return (self._imageDilate.GetOutput().GetClassName(), )

    def get_output(self, idx):
        return self._imageDilate.GetOutput()

    def logic_to_config(self):
        self._config.kernelSize = self._imageDilate.GetKernelSize()
    
    def config_to_logic(self):
        ks = self._config.kernelSize
        self._imageDilate.SetKernelSize(ks[0], ks[1], ks[2])
    
    def execute_module(self):
        self._imageDilate.Update()
        

    #def view(self, parent_window=None):
    #    # if the window was visible already. just raise it
    #    self._viewFrame.Show(True)
    #    self._viewFrame.Raise()


