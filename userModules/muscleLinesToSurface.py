# muscleLinesToSurface copyright (c) 2003 Charl P. Botha http://cpbotha.net/
# $Id: muscleLinesToSurface.py,v 1.2 2004/01/27 15:12:37 cpbotha Exp $

from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
from wxPython.wx import *
import vtk

class muscleLinesToSurface(moduleBase, noConfigModuleMixin):
    """Given muscle centre lines marked with 0-valued voxels, calculate a
    continuous surface through these marked lines.

    Make sure that ONLY the desired voxels have 0 value.  You can do this
    with for instance the doubleThreshold DeVIDE module.  This module
    calculates a 3D distance field, processes this field to yield a signed
    distance field, extracts an isosurface and then clips off extraneous
    surfaces.
    """
    

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)


        self._distance = vtk.vtkImageEuclideanDistance()
        # this seems to yield more accurate results in this case
        # it would probably be better to calculate only 2d distance fields
        self._distance.ConsiderAnisotropyOff()

        self._xEndPoints = []
        self._pf1 = vtk.vtkProgrammableFilter() # yeah
        self._pf1.SetInput(self._distance.GetOutput())
        self._pf1.SetExecuteMethod(self.pf1Execute)

        self._pf2 = vtk.vtkProgrammableFilter()
        self._pf2.SetInput(self._pf1.GetOutput())
        self._pf2.SetExecuteMethod(self.pf2Execute)

        self._mc = vtk.vtkMarchingCubes()
        self._mc.SetInput(self._pf1.GetOutput())
        self._mc.SetValue(0,0.1)

        self._iv = vtk.vtkImplicitVolume()
        self._iv.SetVolume(self._pf2.GetOutput())

        self._cpd = vtk.vtkClipPolyData()
        self._cpd.SetClipFunction(self._iv)
        self._cpd.SetInput(self._mc.GetOutput())
        #self._cpd.InsideOutOn()

        moduleUtils.setupVTKObjectProgress(self, self._distance,
                                           'Calculating distance field...')
        moduleUtils.setupVTKObjectProgress(self, self._pf1,
                                           'Signing distance field...')
        moduleUtils.setupVTKObjectProgress(self, self._pf2,
                                           'Creating implicit volume...')
        moduleUtils.setupVTKObjectProgress(self, self._mc,
                                           'Extracting isosurface...')
        moduleUtils.setupVTKObjectProgress(self, self._cpd,
                                           'Clipping isosurface...')
        
        
        
        

        self._iObj = self._distance
        self._oObj = self._cpd
        
        self._viewFrame = self._createViewFrame({'distance' :
                                                 self._distance,
                                                 'pf1' :
                                                 self._pf1,
                                                 'pf2' :
                                                 self._pf2,
                                                 'mc' :
                                                 self._mc,
                                                 'cpd' :
                                                 self._cpd})

    def pf1Execute(self):
        inputData = self._pf1.GetStructuredPointsInput()
        outputData = self._pf1.GetOutput()
        outputData.DeepCopy(inputData)

        xdim = inputData.GetWholeExtent()[1]
        ydim = inputData.GetWholeExtent()[3]
        zdim = inputData.GetWholeExtent()[5]
        
        self._xEndPoints = [[] for dummy in range(zdim + 1)]
            
        for z in xrange(zdim + 1):

            x = 0
            startPointFound = False

            while not startPointFound and x != xdim + 1:
                for y in xrange(ydim + 1):
                    val = inputData.GetScalarComponentAsDouble(x,y,z,0)
                    if val == 0:
                        startPointFound = True
                        self._xEndPoints[z].append((x,y))
                        # this will break out of the for loop (no else clause
                        # will be executed)
                        break

                x += 1

            if not startPointFound:
                print "ERROR: startPoint not found on slice %d." % (z,)
                return

            x = xdim
            endPointFound = False

            while not endPointFound and x != -1:
                for y in xrange(ydim + 1):
                    val = inputData.GetScalarComponentAsDouble(x,y,z,0)
                    if val == 0:
                        endPointFound = True
                        self._xEndPoints[z].append((x,y))
                        break

                x -= 1

            if not endPointFound:
                print "ERROR: endPoint not found on slice %d." % (z,)
                return

            prevFlipY = -1
            for x in xrange(self._xEndPoints[z][0][0],
                            self._xEndPoints[z][1][0] + 1):
                
                signFlip = False
                signFlipped = False
                prevVal = -1
                for y in xrange(ydim + 1):
                    val = inputData.GetScalarComponentAsDouble(x,y,z,0)
                    
                    if val == 0 and prevVal != 0:
                        signFlip = not signFlip
                        signFlipped = True
                        prevFlipY = y
                        
                    if signFlip:
                        outputData.SetScalarComponentFromDouble(x,y,z,0,-val)
                    else:
                        # this is necessary (CopyStructure doesn't do it)
                        outputData.SetScalarComponentFromDouble(x,y,z,0,val)

                    prevVal = val

                if not signFlipped:
                    # this shouldn't happen, because we're by definition
                    # between endpoints - we're going to use prevFlipY
                    print "Fixing noFlip"                    
                    if prevFlipY >= 0:

                        for y in xrange(prevFlipY, ydim + 1):
                            val = inputData.GetScalarComponentAsDouble(x,y,z,0)
                            outputData.SetScalarComponentFromDouble(
                                x,y,z,0,-val)

            # now check the bottom row of the distance field!
            for x in xrange(self._xEndPoints[z][0][0],
                            self._xEndPoints[z][1][0] + 1):
                val = outputData.GetScalarComponentAsDouble(x,ydim,z,0)
                if val > 0:
                    # this means it's screwed, we have to redo from bottom up
                    # first make all positive until we reach 0 again
                    y = ydim
                    while val != 0 and y != -1:
                        val = outputData.GetScalarComponentAsDouble(x,y,z,0)
                        if val > 0:
                            outputData.SetScalarComponentFromDouble(
                                x,y,z,0,-val)
                        y -= 1

                    # FIXME: continue here... past the first 0, we have to
                    # check for each voxel whether it's inside or outside
                        
                    

            self._pf1.UpdateProgress(z / float(zdim))
            
        # end for z
                        
    def pf2Execute(self):
        """Mask unwanted surface out with negative numbers.  I'm evil.
        """
        
        inputData = self._pf2.GetStructuredPointsInput()
        outputData = self._pf2.GetOutput()
        outputData.DeepCopy(inputData)

        xdim = inputData.GetWholeExtent()[1]        
        ydim = inputData.GetWholeExtent()[3]        
        zdim = inputData.GetWholeExtent()[5]

        for z in xrange(zdim + 1):
            x0 = self._xEndPoints[z][0][0]
            y0 = self._xEndPoints[z][0][1]
            for y in xrange(y0, ydim + 1):            
                for x in xrange(0, x0):
                    val = inputData.GetScalarComponentAsDouble(x,y,z,0)
                    # make this negative as well, so that the surface will
                    # get nuked by this implicitvolume
                    outputData.SetScalarComponentFromDouble(x,y,z,0,-val)

            x1 = self._xEndPoints[z][1][0]
            y1 = self._xEndPoints[z][1][1]
            for y in xrange(y1, ydim + 1):
                for x in xrange(x1 + 1, xdim + 1):
                    val = inputData.GetScalarComponentAsDouble(x,y,z,0)
                    # make this negative as well, so that the surface will
                    # get nuked by this implicitvolume
                    outputData.SetScalarComponentFromDouble(x,y,z,0,-val)

            self._pf2.UpdateProgress(z / float(zdim))

        # outputData.GetPointData().GetScalars() still valid here

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._distance
        del self._mc
        del self._iv
        del self._cpd
        del self._pf1
        del self._pf2
        del self._iObj
        del self._oObj

    def getInputDescriptions(self):
	return ('vtkImageData',)

    def setInput(self, idx, inputStream):
        self._iObj.SetInput(inputStream)

    def getOutputDescriptions(self):
        return (self._oObj.GetOutput().GetClassName(),)

    def getOutput(self, idx):
        return self._oObj.GetOutput()

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass

    def executeModule(self):
        self._oObj.Update()
        #print str(self._pf2.GetOutput().GetPointData().GetScalars())

    def view(self, parent_window=None):
        self._viewFrame.Show(True)
        self._viewFrame.Raise()