# slice3d_vwr.py copyright (c) 2002 Charl P. Botha <cpbotha@ieee.org>
# $Id: slice3dVWR.py,v 1.44 2005/10/15 00:25:03 cpbotha Exp $
# next-generation of the slicing and dicing devide module

import cPickle
from external.SwitchColourDialog import ColourDialog
import genUtils

from moduleBase import moduleBase
from moduleMixins import introspectModuleMixin, colourDialogMixin
import moduleUtils

# the following four lines are only needed during prototyping of the modules
# that they import
import modules.Viewers.slice3dVWRmodules.sliceDirections
reload(modules.Viewers.slice3dVWRmodules.sliceDirections)
import modules.Viewers.slice3dVWRmodules.selectedPoints
reload(modules.Viewers.slice3dVWRmodules.selectedPoints)
import modules.Viewers.slice3dVWRmodules.tdObjects
reload(modules.Viewers.slice3dVWRmodules.tdObjects)
import modules.Viewers.slice3dVWRmodules.implicits
reload(modules.Viewers.slice3dVWRmodules.implicits)


from modules.Viewers.slice3dVWRmodules.sliceDirections import sliceDirections
from modules.Viewers.slice3dVWRmodules.selectedPoints import selectedPoints
from modules.Viewers.slice3dVWRmodules.tdObjects import tdObjects
from modules.Viewers.slice3dVWRmodules.implicits import implicits

import os
import time
import vtk
import vtkdevide

import wx

from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import operator


# -------------------------------------------------------------------------

class slice3dVWR(introspectModuleMixin, colourDialogMixin, moduleBase):
    
    """Slicing, dicing slice viewing class.

    Please see the main DeVIDE help/user manual by pressing F1.  This module,
    being so absolutely great, has its own section.

    $Revision: 1.44 $
    """

    IS_VIEW = 1

    gridSelectionBackground = (11, 137, 239)

    def __init__(self, moduleManager):
        # call base constructor
        moduleBase.__init__(self, moduleManager)
        colourDialogMixin.__init__(
            self, moduleManager.get_module_view_parent_window())
        self._numDataInputs = 7
        # use list comprehension to create list keeping track of inputs
        self._inputs = [{'Connected' : None, 'inputData' : None,
                         'vtkActor' : None, 'ipw' : None}
                       for i in range(self._numDataInputs)]
        # then the window containing the renderwindows
        self.threedFrame = None

        # the renderers corresponding to the render windows
        self._threedRenderer = None
        self._dummyRenderer = None
        self._executionEnabled = True
        self._cachedInputs = [-1] * len(self._inputs)

        self._outline_source = vtk.vtkOutlineSource()
        om = vtk.vtkPolyDataMapper()
        om.SetInput(self._outline_source.GetOutput())
        self._outline_actor = vtk.vtkActor()
        self._outline_actor.SetMapper(om)
        self._cube_axes_actor2d = vtk.vtkCubeAxesActor2D()
        self._cube_axes_actor2d.SetFlyModeToOuterEdges()
        #self._cube_axes_actor2d.SetFlyModeToClosestTriad()


        # use box widget for VOI selection
        self._voi_widget = vtk.vtkBoxWidget()
        # we want to keep it aligned with the cubic volume, thanks
        self._voi_widget.SetRotationEnabled(0)
        self._voi_widget.AddObserver('InteractionEvent',
                                     self.voiWidgetInteractionCallback)
        self._voi_widget.AddObserver('EndInteractionEvent',
                                     self.voiWidgetEndInteractionCallback)
        self._voi_widget.NeedsPlacement = True

        # also create the VTK construct for actually extracting VOI from data
        #self._extractVOI = vtk.vtkExtractVOI()
        self._currentVOI = 6 * [0]

        # set the whole UI up!
        self._create_window()

        # our interactor styles (we could add joystick or something too)
        self._cInteractorStyle = vtk.vtkInteractorStyleTrackballCamera()


        # set the default
        self.threedFrame.threedRWI.SetInteractorStyle(self._cInteractorStyle)

        # initialise our sliceDirections, this will also setup the grid and
        # bind all slice UI events
        self.sliceDirections = sliceDirections(
            self, self.controlFrame.sliceGrid)

        self.selectedPoints = selectedPoints(
            self, self.controlFrame.pointsGrid)

        # we now have a wx.ListCtrl, let's abuse it
        self._tdObjects = tdObjects(self,
                                    self.controlFrame.objectsListGrid)

        self._implicits = implicits(self,
                                    self.controlFrame.implicitsGrid)


        # setup orientation widget stuff
        self._orientationWidget = vtk.vtkOrientationMarkerWidget()
        self._annotatedCubeActor = vtk.vtkAxesActor() #vtk.vtkAnnotatedCubeActor()

        self._orientationWidget.SetInteractor(
            self.threedFrame.threedRWI)
        self._orientationWidget.SetOrientationMarker(
            self._annotatedCubeActor)
        self._orientationWidget.On()
        

    #################################################################
    # module API methods
    #################################################################

    def close(self):
        # shut down the orientationWidget/Actor stuff
        self._orientationWidget.Off()
        self._orientationWidget.SetInteractor(None)
        self._orientationWidget.SetOrientationMarker(None)
        del self._orientationWidget
        del self._annotatedCubeActor
        
        # take care of scalarbar
        self._showScalarBarForProp(None)
        
        # this is standard behaviour in the close method:
        # call set_input(idx, None) for all inputs
        for idx in range(self._numDataInputs):
            self.setInput(idx, None)

        # also make sure the cached inputs are not bound
        for idx in range(len(self._cachedInputs)):
            self._cachedInputs[idx] = -1

        # take care of the sliceDirections
        self.sliceDirections.close()
        del self.sliceDirections

        # the points
        self.selectedPoints.close()
        del self.selectedPoints

        # take care of the threeD objects
        self._tdObjects.close()
        del self._tdObjects

        # the implicits
        self._implicits.close()
        del self._implicits

        # don't forget to call the mixin close() methods
        introspectModuleMixin.close(self)
        colourDialogMixin.close(self)
        
        # unbind everything that we bound in our __init__
        del self._outline_source
        del self._outline_actor
        del self._cube_axes_actor2d


        del self._voi_widget
        #del self._extractVOI

        del self._cInteractorStyle

        # make SURE there are no props in the Renderer
        self._threedRenderer.RemoveAllProps()
        # take care of all our bindings to renderers
        del self._threedRenderer
        del self._dummyRenderer

        # the remaining bit of logic is quite crucial:
        # we can't explicitly Destroy() the frame, as the RWI that it contains
        # will only disappear when it's reference count reaches 0, and we
        # can't really force that to happen either.  If you DO Destroy() the
        # frame before the RW destructs, it will cause the application to
        # crash because the RW assumes a valid WindowId in its dtor
        #
        # we have two solutions:
        # 1. call a WindowRemap on the RenderWindows so that they reparent
        #    themselves to newly created windowids
        # 2. attach event handlers to the RenderWindow DeleteEvent and
        #    destroy the containing frame from there
        #
        # method 2 doesn't alway work, so we use WindowRemap

        # hide it so long
        #self.threedFrame.Show(0)

        #self.threedFrame.threedRWI.GetRenderWindow().SetSize(10,10)
        self.threedFrame.threedRWI.GetRenderWindow().WindowRemap()
        
        # all the RenderWindow()s are now reparented, so we can destroy
        # the containing frame
        self.threedFrame.Destroy()
        # unbind the _view_frame binding
        del self.threedFrame

        # take care of the objectAnimationFrame
        self.objectAnimationFrame.Destroy()
        del self.objectAnimationFrame

        # take care of the controlFrame too
        self.controlFrame.Destroy()
        del self.controlFrame

    def disableExecution(self):
        self._executionEnabled = False
        
        rw = self.threedFrame.threedRWI.GetRenderWindow()

        # disable interaction
        rw.GetInteractor().Disable()

        # disable all sliceDirections
        self.sliceDirections.disableEnabledSliceDirections()
        
        # remove current renderer from renderwindow
        rw.RemoveRenderer(self._threedRenderer)

        # create and install dummy renderer
        self._dummyRenderer = vtk.vtkRenderer()
        self._dummyRenderer.SetBackground(0.4, 0.4, 0.4)
        rw.AddRenderer(self._dummyRenderer)

        # add text to show that we've been disabled
        ta = vtk.vtkTextActor()
        ta.SetInput("Execution disabled.  Enable in main window.")
        x,y = rw.GetSize()
        ta.SetPosition(10, y / 2 )
        self._dummyRenderer.AddActor(ta)

        # set cachedInputs to -1, indicating that they have not been touched
        for idx in range(len(self._cachedInputs)):
            self._cachedInputs[idx] = -1

        #
        self.render3D()

    def enableExecution(self):
        self._executionEnabled = True
        if self._dummyRenderer:
            
            # put old renderer back and destroy dummyRenderer
            rw = self.threedFrame.threedRWI.GetRenderWindow()
            rw.RemoveRenderer(self._dummyRenderer)
            rw.AddRenderer(self._threedRenderer)
            self._dummyRenderer.RemoveAllProps()
            self._dummyRenderer = None

            # enable interaction
            rw.GetInteractor().Enable()

            # enable all sliceDirections
            self.sliceDirections.enableEnabledSliceDirections()

            # reset the thing
            self._resetAll()

            # now do all the cached inputs, checking for exceptions!
            for idx in range(len(self._cachedInputs)):

                # we only have to something if an input is != -1

                if self._cachedInputs[idx] == None:
                    # we're going to try to disconnect
                    try:
                        self.setInput(idx, None)
                        
                    except Exception, e:
                        genUtils.logError(
                            'Error disconnecting input %d of slice3dVWR ' \
                            '%s:%s. ' % \
                            (idx, self._moduleManager.getInstanceName(self),
                             str(e)))

                elif self._cachedInputs[idx] != -1:
                    # this means it's NOT None and NOT -1
                    # so first disconnect
                    try:
                        self.setInput(idx, None)

                    except Exception, e:
                        genUtils.logError(
                            'Error disconnecting input %d of slice3dVWR ' \
                            '%s before reconnect:%s. Going to attempt ' \
                            'reconnection anyway.' % \
                            (idx, self._moduleManager.getInstanceName(self),
                             str(e)))

                    try:
                        self.setInput(idx, self._cachedInputs[idx])
                        
                    except Exception, e:
                        # when this happens, the moduleManager (and
                        # graphEditor) still think this input port is
                        # connected, but this module obviously doesn't
                        genUtils.logError(
                            'Error adding input %d of slice3dVWR %s: %s. ' \
                            'Consider disconnecting it.' % \
                            (idx, self._moduleManager.getInstanceName(self),
                             str(e)))
                        
                # clear the cached input
                self._cachedInputs[idx] = -1

    def executeModule(self):
        # in terms of the view module, executeModule() should update the
        # view.
        self.render3D()
            
    def getConfig(self):
        # implant some stuff into the _config object and return it
        self._config.savedPoints = self.selectedPoints.getSavePoints()

        # also save the visible bounds (this will be used during unpickling
        # to calculate pointwidget and text sizes and the like)
        self._config.boundsForPoints = self._threedRenderer.\
                                       ComputeVisiblePropBounds()

        self._config.implicitsState = self._implicits.getImplicitsState()
        
        return self._config

    def setConfig(self, aConfig):
        self._config = aConfig

        savedPoints = self._config.savedPoints

        self.selectedPoints.setSavePoints(
            savedPoints, self._config.boundsForPoints)

        # we remain downwards compatible
        if hasattr(self._config, 'implicitsState'):
            self._implicits.setImplicitsState(self._config.implicitsState)
        
    def getInputDescriptions(self):
        # concatenate it num_inputs times (but these are shallow copies!)
        return self._numDataInputs * \
               ('vtkStructuredPoints|vtkImageData|vtkPolyData',)

    def setInput(self, idx, inputStream):

        # if execution is disabled, cache all attempts (and store bindings
        # to the inputStreams) - when execution is re-enabled, we will
        # playback the cache, destroying connections if necessary; to the
        # user, it looks like all connections/disconnections are successful
        if not self._executionEnabled:
            # store the input
            self._cachedInputs[idx] = inputStream
            # and return
            return
            
        
        if inputStream == None:
            if self._inputs[idx]['Connected'] == 'tdObject':
                self._tdObjects.removeObject(self._inputs[idx]['tdObject'])
                self._inputs[idx]['Connected'] = None
                self._inputs[idx]['tdObject'] = None

            elif self._inputs[idx]['Connected'] == 'vtkImageDataPrimary' or \
                 self._inputs[idx]['Connected'] == 'vtkImageDataOverlay':
                # remove data from the sliceDirections
                self.sliceDirections.removeData(self._inputs[idx]['inputData'])

                if self._inputs[idx]['Connected'] == 'vtkImageDataPrimary':
                    self._threedRenderer.RemoveActor(self._outline_actor)
                    self._threedRenderer.RemoveActor(self._cube_axes_actor2d)


                    # deactivate VOI widget as far as possible
                    self._voi_widget.SetInput(None)
                    self._voi_widget.Off()
                    self._voi_widget.SetInteractor(None)

                self._inputs[idx]['Connected'] = None
                self._inputs[idx]['inputData'] = None

            elif self._inputs[idx]['Connected'] == 'namedWorldPoints':
                pass

        # END of if inputStream is None clause -----------------------------

        # check for VTK types
        elif hasattr(inputStream, 'GetClassName') and \
             callable(inputStream.GetClassName):

            if inputStream.GetClassName() == 'vtkVolume' or \
               inputStream.GetClassName() == 'vtkPolyData':
                # our _tdObjects instance likes to do this
                self._tdObjects.addObject(inputStream)
                # if this worked, we have to make a note that it was
                # connected as such
                self._inputs[idx]['Connected'] = 'tdObject'
                self._inputs[idx]['tdObject'] = inputStream
                
            elif inputStream.IsA('vtkImageData'):
                connecteds = [i['Connected'] for i in self._inputs]
                if 'vtkImageDataOverlay' in connecteds and \
                   'vtkImageDataPrimary' not in connecteds:
                    # this means the user has disconnected his primary and
                    # is trying to reconnect something in its place.  We
                    # don't like that...
                    raise Exception, \
                          "Please remove all overlays first " \
                          "before attempting to add primary data."

                # if we already have a primary, make sure the new inputStream
                # is added at a higher port number than all existing
                # primaries and overlays
                if 'vtkImageDataPrimary' in connecteds:
                    highestPortIndex = connecteds.index('vtkImageDataPrimary')
                    for i in range(highestPortIndex, len(connecteds)):
                        if connecteds[i] == 'vtkImageDataOverlay':
                            highestPortIndex = i

                    if idx <= highestPortIndex:
                        raise Exception, \
                              "Please add overlay data at higher input " \
                              "port numbers " \
                              "than existing primary data and overlays."

                
                
                # tell all our sliceDirections about the new data
                self.sliceDirections.addData(inputStream)
                
                # find out whether this is  primary or an overlay, record it
                if 'vtkImageDataPrimary' in connecteds:
                    # there's no way there can be only overlays in the list,
                    # the check above makes sure of that
                    self._inputs[idx]['Connected'] = 'vtkImageDataOverlay'
                else:
                    # there are no primaries or overlays, this must be
                    # a primary then
                    self._inputs[idx]['Connected'] = 'vtkImageDataPrimary'

                # also store binding to the data itself
                self._inputs[idx]['inputData'] = inputStream

                if self._inputs[idx]['Connected'] == 'vtkImageDataPrimary':
                    # things to setup when primary data is added
                    #self._extractVOI.SetInput(inputStream)

                    # add outline actor and cube axes actor to renderer
                    self._threedRenderer.AddActor(self._outline_actor)
                    self._outline_actor.PickableOff()
                    self._threedRenderer.AddActor(self._cube_axes_actor2d)
                    self._cube_axes_actor2d.PickableOff()
                    # FIXME: make this toggle-able
                    self._cube_axes_actor2d.VisibilityOn()

                    # reset everything, including ortho camera
                    self._resetAll()

                # update our 3d renderer
                self.threedFrame.threedRWI.Render()

            else:
                raise TypeError, "Wrong input type!"

        # ends: elif hasattr GetClassName
        elif hasattr(inputStream, 'devideType'):
            print "has d3type"
            if inputStream.devideType == 'namedPoints':
                print "d3type correct"
                # add these to our selected points!
                self._inputs[idx]['Connected'] = 'namedWorldPoints'
                for point in inputStream:
                    self.selectedPoints._storePoint(
                        (0,0,0), point['world'], 0.0,
                        point['name'])

        else:
            raise TypeError, "Input type not recognised!"

    def getOutputDescriptions(self):
        return ('Selected points',
                'Implicit Function',
                'Slices polydata',
                'Slices unstructured grid')
        

    def getOutput(self, idx):
        if idx == 0:
            return self.selectedPoints.outputSelectedPoints
        elif idx == 1:
            return self._implicits.outputImplicitFunction
        elif idx == 2:
            return self.sliceDirections.ipwAppendPolyData.GetOutput()
        else:
            return self.sliceDirections.ipwAppendFilter.GetOutput()

    def view(self):
        self.controlFrame.Show(True)
        self.controlFrame.Raise()

        self.threedFrame.Show(True)
        self.threedFrame.Raise()

    #################################################################
    # miscellaneous public methods
    #################################################################

    def getIPWPicker(self):
        return self._ipwPicker

    def getViewFrame(self):
        return self.threedFrame

    def render3D(self):
        """This will cause a render to be called on the encapsulated 3d
        RWI.
        """
        self.threedFrame.threedRWI.Render()

        

    #################################################################
    # internal utility methods
    #################################################################


    def _create_window(self):
        import modules.Viewers.resources.python.slice3dVWRFrames
        reload(modules.Viewers.resources.python.slice3dVWRFrames)

        stereo = self._moduleManager.getAppMainConfig().stereo
        print stereo
        modules.Viewers.resources.python.slice3dVWRFrames.S3DV_STEREO = stereo

        # threedFrame creation and basic setup -------------------
        threedFrame = modules.Viewers.resources.python.slice3dVWRFrames.\
                      threedFrame
        self.threedFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, threedFrame)
            
        # see about stereo
        #self.threedFrame.threedRWI.GetRenderWindow().SetStereoCapableWindow(1)

        # add the renderer
        self._threedRenderer = vtk.vtkRenderer()
        self._threedRenderer.SetBackground(0.5, 0.5, 0.5)
        self.threedFrame.threedRWI.GetRenderWindow().AddRenderer(self.
                                                               _threedRenderer)
        
        # controlFrame creation and basic setup -------------------
        controlFrame = modules.Viewers.resources.python.slice3dVWRFrames.\
                       controlFrame
        self.controlFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, controlFrame)

        # fix for the grid
        #self.controlFrame.spointsGrid.SetSelectionMode(wx.Grid.wxGridSelectRows)
        #self.controlFrame.spointsGrid.DeleteRows(
        #   0, self.controlFrame.spointsGrid.GetNumberRows())


        # add possible point names
        self.controlFrame.sliceCursorNameCombo.Clear()
        self.controlFrame.sliceCursorNameCombo.Append('Point 1')
        self.controlFrame.sliceCursorNameCombo.Append('GIA Glenoid')
        self.controlFrame.sliceCursorNameCombo.Append('GIA Humerus')
        self.controlFrame.sliceCursorNameCombo.Append('FBZ Superior')
        self.controlFrame.sliceCursorNameCombo.Append('FBZ Inferior')
        
        # event handlers for the global control buttons
        wx.EVT_BUTTON(self.threedFrame, self.threedFrame.showControlsButtonId,
                   self._handlerShowControls)
        
        wx.EVT_BUTTON(self.threedFrame, self.threedFrame.resetCameraButtonId,
                   self._handlerResetCamera)

        wx.EVT_BUTTON(self.threedFrame, self.threedFrame.resetAllButtonId,
                   lambda e: (self._resetAll(), self._resetAll()))

        wx.EVT_BUTTON(self.threedFrame, self.threedFrame.saveImageButton.GetId(),
                   self._handlerSaveImageButton)
        
        wx.EVT_CHOICE(self.threedFrame,
                   self.threedFrame.projectionChoiceId,
                   self._handlerProjectionChoice)

        wx.EVT_BUTTON(self.threedFrame,
                   self.threedFrame.introspectButton.GetId(),
                   self._handlerIntrospectButton)

        wx.EVT_BUTTON(self.threedFrame,
                   self.threedFrame.introspectPipelineButtonId,
                   lambda e, pw=self.threedFrame, s=self,
                   rw=self.threedFrame.threedRWI.GetRenderWindow():
                   s.vtkPipelineConfigure(pw, rw))

#         wx.EVT_BUTTON(self.threedFrame, self.threedFrame.resetButtonId,
#                    lambda e, s=self: s._resetAll())


        # event logic for the voi panel

        wx.EVT_CHECKBOX(self.controlFrame,
                     self.controlFrame.voiEnabledCheckBoxId,
                     self._handlerWidgetEnabledCheckBox)

        wx.EVT_CHOICE(self.controlFrame,
                   self.controlFrame.voiAutoSizeChoice.GetId(),
                   self._handlerVoiAutoSizeChoice)

        wx.EVT_BUTTON(self.controlFrame,
                   self.controlFrame.voiFilenameBrowseButton.GetId(),
                   self._handlerVoiFilenameBrowseButton)

        wx.EVT_BUTTON(self.controlFrame,
                   self.controlFrame.voiSaveButton.GetId(),
                   self._handlerVoiSaveButton)

        def _ps_cb():
            # FIXME: update to new factoring
            sliceDirection  = self.getCurrentSliceDirection()
            if sliceDirection:
                val = self.threedFrame.pushSliceSpinCtrl.GetValue()
                if val:
                    sliceDirection.pushSlice(val)
                    self.threedFrame.pushSliceSpinCtrl.SetValue(0)
                    self.threedFrame.threedRWI.Render()

        # clicks directly in the window for picking
        self.threedFrame.threedRWI.AddObserver('LeftButtonPressEvent',
                                               self._rwiLeftButtonCallback)


        # objectAnimationFrame creation and basic setup -------------------
        oaf = modules.Viewers.resources.python.slice3dVWRFrames.\
              objectAnimationFrame
        self.objectAnimationFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager, oaf)

        # display the windows (but we don't show the oaf yet)
        self.view()
        
        if os.name == 'posix':
            # yet another workaround for GTK1.2 on Linux (Debian 3.0)
            # if we don't do this, the renderer is far smaller than its
            # containing window and only corrects once the window is resized

            # also, this shouldn't really fix it, but it does:
            # then size that we set, is the "small" incorrect size
            # but somehow tickling GTK in this way makes everything better
            self.threedFrame.threedRWI.GetRenderWindow().SetSize(
                self.threedFrame.threedRWI.GetSize())
            self.threedFrame.threedRWI._Iren.ConfigureEvent()
            wx.SafeYield()

    def getPrimaryInput(self):
        """Get primary input data, i.e. bottom layer.

        If there is no primary input data, this will return None.
        """
        
        inputs = [i for i in self._inputs if i['Connected'] ==
                  'vtkImageDataPrimary']

        if inputs:
            inputData = inputs[0]['inputData']
        else:
            inputData = None

        return inputData

    def getWorldPositionInInputData(self, discretePos):
        if len(discretePos) < 3:
            return None
        
        inputData = self.getPrimaryInput()

        if inputData:
            ispacing = inputData.GetSpacing()
            iorigin = inputData.GetOrigin()
            # calculate real coords
            world = map(operator.add, iorigin,
                        map(operator.mul, ispacing, discretePos[0:3]))
            return world

        else:
            return None

    def getValuesAtDiscretePositionInInputData(self, discretePos):
        inputData = self.getPrimaryInput()

        if inputData == None:
            return

        # check that discretePos is in the input volume
        validPos = True
        extent = inputData.GetExtent()
        for d in range(3):
            if discretePos[d]< extent[d*2] or discretePos[d] > extent[d*2+1]:
                validPos = False
                break

        if validPos:
            nc = inputData.GetNumberOfScalarComponents()
            values = []
            for c in range(nc):
                values.append(inputData.GetScalarComponentAsDouble(
                    discretePos[0], discretePos[1], discretePos[2], c))
                
        else:
            values = None

        return values
            

    def getValueAtPositionInInputData(self, worldPosition):
        """Try and find out what the primary image data input value is at
        worldPosition.

        If there is no inputData, or the worldPosition is outside of the
        inputData, None is returned.
        """
        
        inputData = self.getPrimaryInput()

        if inputData:
            # then we have to update our internal record of this point
            ispacing = inputData.GetSpacing()
            iorigin = inputData.GetOrigin()
            discrete = map(
                round, map(
                operator.div,
                map(operator.sub, worldPosition, iorigin), ispacing))
                
            validPos = True
            extent = inputData.GetExtent()
            for d in range(3):
                if discrete[d]< extent[d*2] or discrete[d] > extent[d*2+1]:
                    validPos = False
                    break

            if validPos:
                # we rearch this else if the for loop completed normally
                val = inputData.GetScalarComponentAsDouble(discrete[0],
                                                           discrete[1],
                                                           discrete[2], 0)
            else:
                val = None

        else:
            discrete = (0,0,0)
            val = None

        return (val, discrete)
        

    def _resetAll(self):
        """Arrange everything for a single overlay in a single ortho view.

        This method is to be called AFTER the pertinent VTK pipeline has been
        setup.  This is here, because one often connects modules together
        before source modules have been configured, i.e. the success of this
        method is dependent on whether the source modules have been configged.
        HOWEVER: it won't die if it hasn't, just complain.

        It will configure all 3d widgets and textures and thingies, but it
        won't CREATE anything.
        """

        # we can't do any of this if execution has not been enabled
        if not self._executionEnabled:
            return

        # we only do something here if we have data
        inputDataL = [i['inputData'] for i in self._inputs
                      if i['Connected'] == 'vtkImageDataPrimary']
        if inputDataL:
            inputData = inputDataL[0]
        else:
            return

        # we might have ipws, but no inputData, in which we can't do anything
        # either, so we bail
        if inputData is None:
            return

        # make sure this is all nicely up to date
        inputData.Update()

        # set up helper actors
        self._outline_source.SetBounds(inputData.GetBounds())
        self._cube_axes_actor2d.SetBounds(inputData.GetBounds())
        self._cube_axes_actor2d.SetCamera(
            self._threedRenderer.GetActiveCamera())

        # reset the VOI widget
        self._voi_widget.SetInteractor(self.threedFrame.threedRWI)
        self._voi_widget.SetInput(inputData)

        # we only want to placewidget if this is the first time
        if self._voi_widget.NeedsPlacement:
            self._voi_widget.PlaceWidget()
            self._voi_widget.NeedsPlacement = False

        self._voi_widget.SetPriority(0.6)
        self._handlerWidgetEnabledCheckBox()

        self._threedRenderer.ResetCamera()

        # make sure the overlays follow  suit
        self.sliceDirections.resetAll()
        
        # whee, thaaaar she goes.
        self.render3D()

    def _save3DToImage(self, filename):
        self._moduleManager.setProgress(0, "Writing PNG image...")
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(self.threedFrame.threedRWI.GetRenderWindow())

        writer = vtk.vtkPNGWriter()
        writer.SetInput(w2i.GetOutput())
        writer.SetFileName(filename)
        writer.Write()
        self._moduleManager.setProgress(100, "Writing PNG image... [DONE]")

    def _showScalarBarForProp(self, prop):
        """Show scalar bar for the data represented by the passed prop.
        If prop is None, the scalar bar will be removed and destroyed if
        present.
        """

        destroyScalarBar = False

        if prop:
            # activate the scalarbar, connect to mapper of prop
            if prop.GetMapper() and prop.GetMapper().GetLookupTable():
                if not hasattr(self, '_pdScalarBarActor'):
                    self._pdScalarBarActor = vtk.vtkScalarBarActor()
                    self._threedRenderer.AddProp(self._pdScalarBarActor)

                sname = "Unknown"
                s = prop.GetMapper().GetInput().GetPointData().GetScalars()
                if s and s.GetName():
                    sname = s.GetName()

                self._pdScalarBarActor.SetTitle(sname)
                    
                self._pdScalarBarActor.SetLookupTable(
                    prop.GetMapper().GetLookupTable())

                self.threedFrame.threedRWI.Render()
                    
            else:
                # the prop doesn't have a mapper or the mapper doesn't
                # have a LUT, either way, we switch off the thingy...
                destroyScalarBar = True

        else:
            # the user has clicked "somewhere else", so remove!
            destroyScalarBar = True
                

        if destroyScalarBar and hasattr(self, '_pdScalarBarActor'):
            self._threedRenderer.RemoveProp(self._pdScalarBarActor)
            del self._pdScalarBarActor
        

    def _storeSurfacePoint(self, actor, pickPosition):
        polyData = actor.GetMapper().GetInput()
        if polyData:
            xyz = pickPosition
        else:
            # something really weird went wrong
            return

        if self.selectedPoints.hasWorldPoint(xyz):
            return

        val, discrete = self.getValueAtPositionInInputData(xyz)
        if val == None:
            discrete = (0,0,0)
            val = 0

        pointName = self.controlFrame.sliceCursorNameCombo.GetValue()
        self.selectedPoints._storePoint(
            discrete, xyz, val, pointName, True) # lock to surface

        
    #################################################################
    # callbacks
    #################################################################

    def _handlerVoiAutoSizeChoice(self, event):
        if self._voi_widget.GetEnabled():
            asc = self.controlFrame.voiAutoSizeChoice.GetSelection()

            if asc == 0: # bounding box of selected points
                swp = self.selectedPoints.getSelectedWorldPoints()

                if len(swp) > 0:
                    minxyz = list(swp[0])
                    maxxyz = list(swp[0])

                    # find max bounds of the selected points
                    for p in swp:
                        for i in range(3):
                            if p[i] < minxyz[i]:
                                minxyz[i] = p[i]

                            if p[i] > maxxyz[i]:
                                maxxyz[i] = p[i]

                    # now set bounds on VOI thingy
                    # first we zip up minxyz maxxyz to get minx, maxx, miny
                    # etc., then we use * to break this open into 6 args
                    self._voi_widget.SetPlaceFactor(1.0)
                    self._voi_widget.PlaceWidget(minxyz[0], maxxyz[0],
                                                 minxyz[1], maxxyz[1],
                                                 minxyz[2], maxxyz[2])

                    # make sure these changes are reflected in the VOI output
                    self.voiWidgetInteractionCallback(self._voi_widget, None)
                    self.voiWidgetEndInteractionCallback(self._voi_widget,
                                                         None)
                    
                    self.render3D()

                        
    def _handlerWidgetEnabledCheckBox(self, event=None):
        # event can be None
        if self._voi_widget.GetInput():
            if self.controlFrame.voiEnabledCheckBox.GetValue():
                self._voi_widget.On()
                self.voiWidgetInteractionCallback(self._voi_widget, None)
                self.voiWidgetEndInteractionCallback(self._voi_widget,
                                                         None)
                
            else:
                self._voi_widget.Off()

    def _handlerVoiFilenameBrowseButton(self, event):
        dlg = wx.FileDialog(self.controlFrame,
                           "Select VTI filename to write VOI to",
                           "", "", "*.vti", wx.OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.controlFrame.voiFilenameText.SetValue(dlg.GetPath())
                     

    def _handlerVoiSaveButton(self, event):
        input_data = self.getPrimaryInput()
        filename = self.controlFrame.voiFilenameText.GetValue()
        if input_data and self._voi_widget.GetEnabled() and filename:
            # see if we need to reset to zero origin
            zor = self.controlFrame.voiResetToOriginCheck.GetValue()

            extractVOI = vtk.vtkExtractVOI()
            extractVOI.SetInput(input_data)
            extractVOI.SetVOI(self._currentVOI)

            writer = vtk.vtkXMLImageDataWriter()
            writer.SetDataModeToBinary()
            writer.SetFileName(filename)
            
            if zor:
                ici = vtk.vtkImageChangeInformation()
                ici.SetOutputExtentStart(0,0,0)
                ici.SetInput(extractVOI.GetOutput())
                writer.SetInput(ici.GetOutput())

            else:
                writer.SetInput(extractVOI.GetOutput())

            writer.Write()

    def _handlerIntrospectButton(self, event):
        """Open Python introspection window with this module as main object.
        """

        self.miscObjectConfigure(self.threedFrame, self,
                                 'slice3dVWR %s' % \
                                 (self._moduleManager.getInstanceName(self),))
        

    def _handlerProjectionChoice(self, event):
        """Handler for global projection type change.
        """
        
        cam = self._threedRenderer.GetActiveCamera()
        if not cam:
            return
        
        pcs = self.threedFrame.projectionChoice.GetSelection()
        if pcs == 0:
            # perspective
            cam.ParallelProjectionOff()
        else:
            cam.ParallelProjectionOn()

        self.render3D()

    def _handlerResetCamera(self, event):
        self._threedRenderer.ResetCamera()
        self.render3D()

    def _handlerSaveImageButton(self, event):
        # first get the filename
        filename = wx.FileSelector(
            "Choose filename for PNG image",
            "", "", "png",
            "PNG files (*.png)|*.png|All files (*.*)|*.*",
            wx.SAVE)
                    
        if filename:
            self._save3DToImage(filename)

    def _handlerShowControls(self, event):
        if not self.controlFrame.Show(True):
            self.controlFrame.Raise()


    def voiWidgetInteractionCallback(self, o, e):
        planes = vtk.vtkPlanes()
        o.GetPlanes(planes)
        bounds =  planes.GetPoints().GetBounds()

        # first set bounds
        self.controlFrame.voiBoundsText.SetValue(
            "(%.2f %.2f %.2f %.2f %.2f %.2f) mm" %
            bounds)

        input_data = self.getPrimaryInput()
        if input_data:
            ispacing = input_data.GetSpacing()
            iorigin = input_data.GetOrigin()
            # calculate discrete coords
            bounds = planes.GetPoints().GetBounds()
            voi = 6 * [0]
            # excuse the for loop :)
            for i in range(6):
                voi[i] = round((bounds[i] - iorigin[i / 2]) / ispacing[i / 2])

            # store the VOI (this is a shallow copy)
            self._currentVOI = voi
            # display the discrete extent
            self.controlFrame.voiExtentText.SetValue(
                "(%d %d %d %d %d %d)" % tuple(voi))

    def voiWidgetEndInteractionCallback(self, o, e):
        # adjust the vtkExtractVOI with the latest coords
        #self._extractVOI.SetVOI(self._currentVOI)
        pass

    def _rwiLeftButtonCallback(self, obj, event):

        def findPickedProp(obj, onlyTdObjects=False):
            # we use a cell picker, because we don't want the point
            # to fall through the polygons, if you know what I mean
            picker = vtk.vtkCellPicker()
            # very important to set this, else we pick the weirdest things
            picker.SetTolerance(0.005)

            if onlyTdObjects:
                pp = self._tdObjects.getPickableProps()
                if not pp:
                    return (None, (0,0,0))
                
                else:
                    # tell the picker which props it's allowed to pick from
                    for p in pp:
                        picker.AddPickList(p)

                    picker.PickFromListOn()
                    
                
            (x,y) = obj.GetEventPosition()
            picker.Pick(x,y,0.0,self._threedRenderer)
            return (picker.GetActor(), picker.GetPickPosition())
            
        pickAction = self.controlFrame.surfacePickActionChoice.GetSelection()
        if pickAction == 1:
            # Place point on surface
            actor, pickPosition = findPickedProp(obj, True)
            if actor:
                self._storeSurfacePoint(actor, pickPosition)
                
        elif pickAction == 2:
            # configure picked object
            prop, unusedPickPosition = findPickedProp(obj)
            if prop:
                self.vtkPipelineConfigure(self.threedFrame,
                                          self.threedFrame.threedRWI, (prop,))

        elif pickAction == 3:
            # show scalarbar for picked object
            prop, unusedPickPosition = findPickedProp(obj)
            self._showScalarBarForProp(prop)

        elif pickAction == 4:
            # move the object -- for this we're going to use a special
            # vtkBoxWidget
            pass
                    
                    

