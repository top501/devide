from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
from wxPython.wx import *
import vtk

class testModule3(moduleBase, noConfigModuleMixin):

    """Module to prototype modification of homotopy and subsequent
    watershedding of curvature-on-surface image.
    """

    def __init__(self, moduleManager):
        # initialise our base class
        moduleBase.__init__(self, moduleManager)
        # initialise any mixins we might have
        noConfigModuleMixin.__init__(self)

        mm = self._moduleManager        

        self._wspdf = vtk.vtkWindowedSincPolyDataFilter()
        self._wspdf.SetProgressText('smoothing')
        self._wspdf.SetProgressMethod(lambda s=self, mm=mm:
                                      mm.vtk_progress_cb(s._wspdf))

        self._stripper = vtk.vtkStripper()

        self._tf = vtk.vtkTriangleFilter()
        self._tf.SetInput(self._stripper.GetOutput())
        self._curvatures = vtk.vtkCurvatures()
        self._curvatures.SetCurvatureTypeToMean()        
        self._curvatures.SetInput(self._tf.GetOutput())


        self._tf.SetProgressText('triangulating')
        self._tf.SetProgressMethod(lambda s=self, mm=mm:
                                   mm.vtk_progress_cb(s._tf))

        self._curvatures.SetProgressText('calculating curvatures')
        self._curvatures.SetProgressMethod(lambda s=self, mm=mm:
                                           mm.vtk_progress_cb(s._curvatures))

        self._inputPoints = None
        self._inputPointsOID = None
        self._outputPolyDataARB = vtk.vtkPolyData()
        self._outputPolyDataHM = vtk.vtkPolyData()

        self._createViewFrame('Test Module View',
                              {'vtkTriangleFilter' : self._tf,
                               'vtkCurvatures' : self._curvatures})

        self._viewFrame.Show(True)

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)
        # don't forget to call the close() method of the vtkPipeline mixin
        noConfigModuleMixin.close(self)
        # get rid of our reference
        del self._wspdf
        del self._curvatures
        del self._tf

    def getInputDescriptions(self):
	return ('vtkPolyData', 'Watershed minima')

    def setInput(self, idx, inputStream):
        if idx == 0:
            self._stripper.SetInput(inputStream)
        else:
            if inputStream is not self._inputPoints:
                if self._inputPoints:
                    self._inputPoints.removeObserver(self._inputPointsOID)

                if inputStream:
                    self._inputPointsOID = inputStream.addObserver(
                        self._inputPointsObserver)

                self._inputPoints = inputStream

                # initial update
                self._inputPointsObserver(None)

    def getOutputDescriptions(self):
        return ('ARB PolyData output', 'Homotopically modified polydata')

    def getOutput(self, idx):
        if idx == 0:
            return self._outputPolyDataARB
        else:
            return self._outputPolyDataHM

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    

    def executeModule(self):
        if self._stripper.GetInput() and \
               self._outsidePoint and self._giaGlenoid:
            
            self._curvatures.Update()
            # vtkCurvatures has added a mean curvature array to the
            # pointData of the output polydata

            pd = self._curvatures.GetOutput()

            # make a deep copy of the data that we can work with
            tempPd1 = vtk.vtkPolyData()
            tempPd1.DeepCopy(self._curvatures.GetOutput())

            # and now we have to unsign it!
            tempPd1Scalars = tempPd1.GetPointData().GetScalars()
            for i in xrange(tempPd1Scalars.GetNumberOfTuples()):
                a = tempPd1Scalars.GetTuple1(i)
                tempPd1Scalars.SetTuple1(i, float(abs(a)))

            self._outputPolyDataARB.DeepCopy(tempPd1)

            # BUILDING NEIGHBOUR MAP ####################################
            
            # iterate through all points
            numPoints = tempPd1.GetNumberOfPoints()
            neighbourMap = [[] for i in range(numPoints)]
            cellIdList = vtk.vtkIdList()
            pointIdList = vtk.vtkIdList()

            for ptId in xrange(numPoints):
                # this has to be first
                neighbourMap[ptId].append(ptId)
                tempPd1.GetPointCells(ptId, cellIdList)
                # we now have all edges meeting at point i
                for cellIdListIdx in range(cellIdList.GetNumberOfIds()):
                    edgeId = cellIdList.GetId(cellIdListIdx)
                    tempPd1.GetCellPoints(edgeId, pointIdList)
                    # there have to be two points per edge,
                    # one if which is the centre-point itself
                    for pointIdListIdx in range(pointIdList.GetNumberOfIds()):
                        tempPtId = pointIdList.GetId(pointIdListIdx)
                        if tempPtId not in neighbourMap[ptId]:
                            neighbourMap[ptId].append(tempPtId)

                #print neighbourMap[ptId]

                if ptId % (numPoints / 20) == 0:
                    self._moduleManager.setProgress(100.0 * ptId / numPoints,
                                                    "Building neighbour map")

            self._moduleManager.setProgress(100.0,
                                            "Done building neighbour map")

            # DONE BUILDING NEIGBOUR MAP ################################

            # BUILDING SEED IMAGE #######################################

            # now let's build the seed image
            # wherever we want to enforce minima, the seed image
            # should be equal to the lowest value of the mask image
            # everywhere else it should be the maximum value of the mask
            # image
            cMin, cMax = tempPd1.GetScalarRange()
            print "range: %d - %d" % (cMin, cMax)
            seedPd = vtk.vtkPolyData()
            # first make a copy of the complete PolyData
            seedPd.DeepCopy(tempPd1)
            # now change EVERYTHING to the maximum value
            print seedPd.GetPointData().GetScalars().GetName()
            # we know that the active scalars thingy has only one component,
            # namely Mean_Curvature - set it all to MAX
            seedPd.GetPointData().GetScalars().FillComponent(0, cMax)

            # now find the minima and set them too
            gPtId = seedPd.FindPoint(self._giaGlenoid)
            oPtId = seedPd.FindPoint(self._outsidePoint)

            # the pointdata is of course dependent on the points - we know
            # that Mean_Curvature is a 1-tuple
            seedPd.GetPointData().GetScalars().SetTuple1(gPtId, cMin)
            seedPd.GetPointData().GetScalars().SetTuple1(oPtId, cMin)
            # remember vtkDataArray: array of tuples, each tuple made up
            # of n components

            # DONE BUILDING SEED IMAGE ###################################

            # MODIFY MASK IMAGE ##########################################

            # make sure that the minima as indicated by the user are cMin
            # in the mask image!

            gPtId = tempPd1.FindPoint(self._giaGlenoid)
            tempPd1.GetPointData().GetScalars().SetTuple1(gPtId, cMin)
            oPtId = tempPd1.FindPoint(self._outsidePoint)
            tempPd1.GetPointData().GetScalars().SetTuple1(oPtId, cMin)
            
            # DONE MODIFYING MASK IMAGE ##################################


            # BEGIN erosion + supremum (modification of image homotopy)
            newSeedPd = vtk.vtkPolyData()

            newSeedPd.DeepCopy(seedPd)

            # get out some temporary variables
            tempPd1Scalars = tempPd1.GetPointData().GetScalars()
            seedPdScalars = seedPd.GetPointData().GetScalars()
            newSeedPdScalars = newSeedPd.GetPointData().GetScalars()
            
            stable = False
            iteration = 0
            while not stable:
                for nbh in neighbourMap:
                    # by definition, EACH position in neighbourmap must have
                    # at least ONE (1) ptId

                    # create list with corresponding curvatures
                    nbhC = [seedPdScalars.GetTuple1(ptId) for ptId in nbh]
                    # sort it
                    nbhC.sort()
                    # replace the centre point in newSeedPd with the lowest val
                    newSeedPdScalars.SetTuple1(nbh[0], nbhC[0])

                # now put result of supremum of newSeed and tempPd1 (the mask)
                # directly into seedPd - the loop can then continue

                # in theory, these two polydatas have identical pointdata
                # go through them, constructing newSeedPdScalars
                # while we're iterating through this loop, also check if
                # newSeedPdScalars is identical to seedPdScalars
                stable = True
                
                for i in xrange(newSeedPdScalars.GetNumberOfTuples()):
                    a = newSeedPdScalars.GetTuple1(i)
                    b = tempPd1Scalars.GetTuple1(i)
                    c = [b, a][bool(a > b)]

                    if stable and c != seedPdScalars.GetTuple1(i):
                        # we only check if stable == True
                        # if a single scalar is different, stable becomes
                        # false and we'll never have to check again
                        stable = False
                        print "unstable on point %d" % (i)
                    
                    # stuff the result directly into seedPdScalars, ready
                    # for the next iteration
                    seedPdScalars.SetTuple1(i, c)

                print "iteration %d done" % (iteration)
                iteration += 1

                self._outputPolyDataHM.DeepCopy(seedPd)
                    

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()
    
    def _inputPointsObserver(self, obj):
        # extract a list from the input points
        if self._inputPoints:
            # extract the two points with labels 'GIA Glenoid'
            # and 'GIA Humerus'
            
            giaGlenoid = [i['world'] for i in self._inputPoints
                          if i['name'] == 'GIA Glenoid']

            outside = [i['world'] for i in self._inputPoints
                       if i['name'] == 'Outside']


            if giaGlenoid and outside:
                
                # we only apply these points to our internal parameters
                # if they're valid and if they're new
                self._giaGlenoid = giaGlenoid[0]
                self._outsidePoint = outside[0]
    
        
        
        
