# $Id: gradientAnisotropicDiffusion.py,v 1.1 2004/03/03 12:20:16 cpbotha Exp $

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

class gradientAnisotropicDiffusion(scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        self._config.numberOfIterations = 5
        self._config.conductanceParameter = 3.0

        configList = [
            ('Number of iterations:', 'numberOfIterations', 'base:int', 'text',
             'Number of time-step updates (iterations) the solver will '
             'perform.'),
            ('Conductance parameter:', 'conductanceParameter', 'base:float',
             'text', 'Sensitivity of the  conductance term.  Lower == more '
             'preservation of image features.')]

        
        scriptedConfigModuleMixin.__init__(self, configList)


        # setup the pipeline
        d = itk.itkGradientAnisotropicDiffusionImageFilterF3F3_New()
        d.SetTimeStep(0.0625) # standard for 3D
        
        moduleUtilsITK.setupITKObjectProgress(
            self, d, 'itkGradientAnisotropicDiffusionImageFilter',
            'Smoothing data')
        self._diffuse = d

        self._createWindow(
            {'Module (self)' : self,
             'itkGradientAnisotropicDiffusion' : self._diffuse})

        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._diffuse

    def executeModule(self):
        self._diffuse.Update()

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def setInput(self, idx, inputStream):
        self._diffuse.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def getOutput(self, idx):
        return self._diffuse.GetOutput()

    def configToLogic(self):
        self._diffuse.SetNumberOfIterations(self._config.numberOfIterations)
        self._diffuse.SetConductanceParameter(
            self._config.conductanceParameter)

    def logicToConfig(self):
        self._config.numberOfIterations = self._diffuse.GetNumberOfIterations()
        self._config.conductanceParameter = self._diffuse.\
                                            GetConductanceParameter()