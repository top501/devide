from external import wxPyPlot
import gen_utils
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils

try:
    import Numeric
except:
    import numarray as Numeric
    
import vtk
import wx

class histogram1D(IntrospectModuleMixin, ModuleBase):

    """Calculates and shows 1D histogram (occurrences over value) of its
    input data.

    $Revision: 1.3 $
    """

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._imageAccumulate = vtk.vtkImageAccumulate()
        module_utils.setup_vtk_object_progress(self, self._imageAccumulate,
                                           'Calculating histogram')

        self._viewFrame = None
        self._createViewFrame()
        self._bindEvents()

        self._config.numberOfBins = 256
        self._config.minValue = 0.0
        self._config.maxValue = 256.0
        
        self.config_to_logic()
        self.logic_to_config()
        self.config_to_view()

        self.view()

    def close(self):
        for i in range(len(self.get_input_descriptions())):
            self.set_input(i, None)

        self._viewFrame.Destroy()
        del self._viewFrame

        del self._imageAccumulate

        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ('VTK Image Data',)

    def set_input(self, idx, inputStream):

        self._imageAccumulate.SetInput(inputStream)

    def get_output_descriptions(self):
        return ()

    def logic_to_config(self):
        # for now, we work on the first component (of a maximum of three)
        # we could make this configurable
        
        minValue = self._imageAccumulate.GetComponentOrigin()[0]
        
        cs = self._imageAccumulate.GetComponentSpacing()
        ce = self._imageAccumulate.GetComponentExtent()
        
        numberOfBins = ce[1] - ce[0] + 1
        # again we use nob - 1 so that maxValue is also part of a bin
        maxValue = minValue + (numberOfBins-1) * cs[0]

        self._config.numberOfBins = numberOfBins
        self._config.minValue = minValue
        self._config.maxValue = maxValue

    def config_to_logic(self):
        co = list(self._imageAccumulate.GetComponentOrigin())
        co[0] = self._config.minValue
        self._imageAccumulate.SetComponentOrigin(co)

        ce = list(self._imageAccumulate.GetComponentExtent())

        ce[0] = 0
        ce[1] = self._config.numberOfBins - 1
        self._imageAccumulate.SetComponentExtent(ce)

        cs = list(self._imageAccumulate.GetComponentSpacing())
        # we divide by nob - 1 because we want maxValue to fall in the
        # last bin...
        cs[0] = (self._config.maxValue - self._config.minValue) / \
                (self._config.numberOfBins - 1)
        
        self._imageAccumulate.SetComponentSpacing(cs)
        
    def view_to_config(self):
        self._config.numberOfBins = gen_utils.textToInt(
            self._viewFrame.numBinsSpinCtrl.GetValue(),
            self._config.numberOfBins)

        self._config.minValue = gen_utils.textToFloat(
            self._viewFrame.minValueText.GetValue(),
            self._config.minValue)

        self._config.maxValue = gen_utils.textToFloat(
            self._viewFrame.maxValueText.GetValue(),
            self._config.maxValue)

        if self._config.minValue > self._config.maxValue:
            self._config.maxValue = self._config.minValue

    def config_to_view(self):
        self._viewFrame.numBinsSpinCtrl.SetValue(
            self._config.numberOfBins)

        self._viewFrame.minValueText.SetValue(
            str(self._config.minValue))

        self._viewFrame.maxValueText.SetValue(
            str(self._config.maxValue))

    def execute_module(self):
        if self._imageAccumulate.GetInput() == None:
            return
        
        self._imageAccumulate.Update()

        # get histogram params directly from logic
        minValue = self._imageAccumulate.GetComponentOrigin()[0]
        
        cs = self._imageAccumulate.GetComponentSpacing()
        ce = self._imageAccumulate.GetComponentExtent()
        
        numberOfBins = ce[1] - ce[0] + 1
        maxValue = minValue + numberOfBins * cs[0]
        # end of param extraction

        histArray = Numeric.arange(numberOfBins * 2)
        histArray.shape = (numberOfBins, 2)
        
        od = self._imageAccumulate.GetOutput()
        for i in range(numberOfBins):
            histArray[i,0] = minValue + i * cs[0]
            histArray[i,1] = od.GetScalarComponentAsDouble(i,0,0,0)

        lines = wxPyPlot.PolyLine(histArray, colour='blue')

        self._viewFrame.plotCanvas.Draw(
            wxPyPlot.PlotGraphics([lines], "Histogram", "Value", "Occurrences")
            )

    def view(self):
        self._viewFrame.Show()
        self._viewFrame.Raise()

    # ---------------------------------------------------------------
    # END of API methods
    # ---------------------------------------------------------------

    def _createViewFrame(self):
        # create the viewerFrame
        import modules.viewers.resources.python.histogram1DFrames
        reload(modules.viewers.resources.python.histogram1DFrames)

        self._viewFrame = module_utils.instantiate_module_view_frame(
            self, self._module_manager,
            modules.viewers.resources.python.histogram1DFrames.\
            histogram1DFrame)

        self._viewFrame.plotCanvas.SetEnableZoom(True)
        self._viewFrame.plotCanvas.SetEnableGrid(True)

        objectDict = {'Module (self)' : self,
                      'vtkImageAccumulate' : self._imageAccumulate}

        module_utils.create_standard_object_introspection(
            self, self._viewFrame, self._viewFrame.viewFramePanel,
            objectDict, None)

        module_utils.create_eoca_buttons(self, self._viewFrame,
                                      self._viewFrame.viewFramePanel)
        
        
                      
    def _bindEvents(self):
        wx.EVT_BUTTON(self._viewFrame,
                      self._viewFrame.autoRangeButton.GetId(),
                      self._handlerAutoRangeButton)

    def _handlerAutoRangeButton(self, event):
        if self._imageAccumulate.GetInput() == None:
            return

        self._imageAccumulate.GetInput().Update()
        sr = self._imageAccumulate.GetInput().GetScalarRange()
        self._viewFrame.minValueText.SetValue(str(sr[0]))
        self._viewFrame.maxValueText.SetValue(str(sr[1]))
