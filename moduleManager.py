import sys, os, fnmatch
import copy
import genUtils
import modules
import mutex
from random import choice
from moduleBase import defaultConfigClass

class metaModule:
    """Class used to store module-related information.
    """
    
    def __init__(self, instance, instanceName):
        """Instance is the actual class instance and instanceName is a unique
        name that has been chosen by the user or automatically.
        """
        self.instance = instance        
        self.instanceName = instanceName
        self.resetInputsOutputs()

    def close(self):
        del self.instance
        del self.inputs
        del self.outputs

    def resetInputsOutputs(self):
        numIns = len(self.instance.getInputDescriptions())
        numOuts = len(self.instance.getOutputDescriptions())
        # numIns list of tuples of (supplierModule, supplierOutputIdx)
        self.inputs = [None] * numIns
        # numOuts list of lists of tuples of (consumerModule, consumerInputIdx)
        # be careful with list concatenation, it makes copies, which are mostly
        # shallow!!!
        self.outputs = [[] for _ in range(numOuts)]

class pickledModuleState:
    def __init__(self):
        self.moduleConfig = None
        # e.g. modules.Viewers.histogramSegment
        self.moduleName = None
        # this is the unique name of the module, e.g. dvm15
        self.instanceName = None

class pickledConnection:
    def __init__(self, sourceInstanceName=None, outputIdx=None,
                 targetInstanceName=None, inputIdx=None, connectionType=None):
        
        self.sourceInstanceName = sourceInstanceName
        self.outputIdx = outputIdx
        self.targetInstanceName = targetInstanceName
        self.inputIdx = inputIdx
        self.connectionType = connectionType

class moduleManager:
    """This class in responsible for picking up new modules in the modules 
    directory and making them available to the rest of the program."""
    
    def __init__(self, devide_app):
	"""Initialise module manager by fishing .py devide modules from
	all pertinent directories."""
	
        self._devide_app = devide_app
        # module dictionary, keyed on instance... cool.
        # values are metaModules
	self._moduleDict = {}

        # we use this to store temporary bindings to modules so that
        # they can be scripted with
        self._markedModules = {}

        appdir = self._devide_app.get_appdir()
        self._modules_dir = os.path.join(appdir, 'modules')
        self._userModules_dir = os.path.join(appdir, 'userModules')
        
	# make first scan of available modules
	self.scanModules()

        # this is a list of modules that have the ability to start a network
        # executing all by themselves and usually do... when we break down
        # a network, we should take these out first.  when we build a network
        # we should put them down last

        # slice3dVWRs must be connected LAST, histogramSegment second to last
        # and all the rest before them
        self.consumerTypeTable = {'slice3dVWR' : 5,
                                'histogramSegment' : 4}

        # we'll use this to perform mutex-based locking on the progress
        # callback... (there SHOULD only be ONE moduleManager instance)
        self._inProgressCallback = mutex.mutex()

        self._executionDisabled = True

    def close(self):
        """Iterates through each module and closes it.

        This is only called during devide application shutdown.
        """

        # this is fine because .items() makes a copy of the dict
        for mModule in self._moduleDict.items():
            try:
                self.deleteModule(mModule.instance)
            except:
                # we can't allow a module to stop us
                pass

    def scanModules(self):
	"""(Re)Check the modules directory for *.py files and put them in
	the list self.module_files."""
        self._availableModuleList = {}

        def recursiveDirectoryD3MNSearch(adir, curModulePath, mnList):
            """Iterate recursively starting at adir and make a list of
            all available modules and networks.  We do not traverse into dirs
            that are named 'resources' or that end with 'modules'.
            """

            if curModulePath:
                wildCard = "*.py"
            else:
                wildCard = "*.dvn"
                
            fileNames = os.listdir(adir)
            for fileName in fileNames:
                completeName = os.path.join(adir, fileName)
                if os.path.isdir(completeName) and \
                       fileName.strip('/') != 'resources' and \
                       not fileName.strip('/').lower().endswith('modules'):
                    # fileName is just a directory name then
                    # make sure it has no /'s at the end and append
                    # it to the curModulePath when recursing
                    newCurModulePath = None
                    if curModulePath:
                        newCurModulePath = curModulePath + '.' + \
                                           fileName.strip('/')

                    recursiveDirectoryD3MNSearch(
                        completeName,
                        newCurModulePath,
                        mnList)

                elif os.path.isfile(completeName) and \
                         fnmatch.fnmatch(fileName, wildCard) and \
                         not fnmatch.fnmatch(fileName, "_*"):
                    if curModulePath:
                        mnList.append(
                            "%s.%s" % (curModulePath,
                                       os.path.splitext(fileName)[0]))
                    else:
                        mnList.append(completeName)

        appDir = self._devide_app.get_appdir()
        userModuleList = []
        recursiveDirectoryD3MNSearch(os.path.join(appDir,
                                                    'userModules'),
                                       'userModules', userModuleList)

        # make sure we pick it up if someone has edited the moduleList
        reload(modules)
        # first add the core modules to our central list
        for mn in modules.moduleList:
            if self._devide_app.mainConfig.useInsight or \
               not mn.startswith('Insight'):
                self._availableModuleList['modules.%s' % (mn,)] = \
                                                       modules.moduleList[mn]

        # now do the modulePacks
        # first get a list of directories in modulePacks
        modulePacksDir = os.path.join(appDir, 'modulePacks')        
        try:
            mpdcands = os.listdir(modulePacksDir)
        except Exception, e:
            print "Could not list modulePacks: %s." % (str(e),)
        else:
            try:
                import modulePacks
            except ImportError, e:
                print "Could not import modulePacks: %s." % (str(e),)
            else:
                mpdirs = [mpdir for mpdir in mpdcands
                          if os.path.isdir(
                    os.path.join(modulePacksDir, mpdir))]

                for mpdir in mpdirs:
                    # this should remove trailing dirseps
                    mpdir = os.path.normpath(mpdir)
                    try:
                        # import the modulePack
                        __import__('modulePacks.%s' % (mpdir,),
                                   globals(), locals())
                        # reload it
                        reload(getattr(modulePacks, mpdir))
                    except ImportError:
                        # skip to next mpdir
                        continue

                    mpdirModuleList = getattr(modulePacks, mpdir).moduleList
                    for mn,cats in mpdirModuleList.items():
                        self._availableModuleList['modulePacks.%s.%s' %
                                                  (mpdir, mn)] = cats
                                                  

            

        # then all the user modules
        for umn in userModuleList:
            self._availableModuleList['%s' % (umn,)] = \
                                           ('userModules',)

        # we should move this functionality to the graphEditor.  "segments"
        # are _probably_ only valid there... alternatively, we should move
        # the concept here
        segmentList = []
        recursiveDirectoryD3MNSearch(os.path.join(appDir, 'segments'),
                                     None, segmentList)
        self.availableSegmentsList = segmentList

    def disableExecution(self):
        """This will call the disableExecution on all modules that have
        this method.  In addition, this call will be attempted on all new
        modules that are created.
        """

        for moduleInstance in self._moduleDict:
            if hasattr(moduleInstance, 'disableExecution'):
                moduleInstance.disableExecution()

        self._executionDisabled = True
            

    def enableExecution(self):
        """This will call enableExecution on all modules that have this
        method.  In addition, disableExecution will not be called on newly
        created modules.
        """

        for moduleInstance in self._moduleDict:
            if hasattr(moduleInstance, 'enableExecution'):
                moduleInstance.enableExecution()

        self._executionDisabled = False
              


    def interruptExecution(self):
        """Stop as much of the demand driven execution as possible.
        """

        # here we call disableExecution, else the interruption can never
        # work... resumeExecution does NOT automatically call enableExecution()
        self.disableExecution()

        for moduleInstance, metaModule in self._moduleDict.items():
            className = moduleInstance.__class__.__name__

            # now go through all the module's attributes calling
            # SetAbortExecute() and SetAbortGenerateData() everywhere
            for attrName in dir(moduleInstance):
                obj = getattr(moduleInstance, attrName)
                try:
                    obj.SetAbortExecute(1)
                except Exception:
                    pass
                else:
                    print "Successfully called SetAbortExecute(1) on %s.%s" \
                          % (moduleInstance, obj.GetClassName())

                try:
                    obj.SetAbortGenerateData(1)
                except Exception:
                    pass
                else:
                    print "Successfully called SetAbortGenerateData(1) on " \
                          "%s.%s" \
                          % (moduleInstance, obj.__class__)

    def resumeExecution(self):
        """Restart all execution after an interruptExecution
        """

        # FIXME: we ONLY want to do this if we're not inProgress
        for moduleInstance, metaModule in self._moduleDict.items():
            className = moduleInstance.__class__.__name__

            # now go through all the module's attributes calling
            # SetAbortExecute() and SetAbortGenerateData() everywhere
            for attrName in dir(moduleInstance):
                obj = getattr(moduleInstance, attrName)
                try:
                    obj.SetAbortExecute(0)
                except Exception:
                    pass
                else:
                    print "Successfully called SetAbortExecute(0) on %s.%s" \
                          % (moduleInstance, obj.GetClassName())

                try:
                    obj.SetAbortGenerateData(0)
                except Exception:
                    pass
                else:
                    print "Successfully called SetAbortGenerateData(0) on " \
                          "%s.%s" \
                          % (moduleInstance, obj.__class__)

    def get_app_dir(self):
        return self.getAppDir()

    def getAppDir(self):
        return self._devide_app.getAppDir()
	
    def getAvailableModuleList(self):
	return self._availableModuleList

    def getInstance(self, instanceName):
        """Given the unique instance name, return the instance itself.
        If the module doesn't exist, return None.
        """

        found = False
        for instance, mModule in self._moduleDict.items():
            if mModule.instanceName == instanceName:
                found = True
                break

        if found:
            return mModule.instance

        else:
            return None

    def getInstanceName(self, instance):
        """Given the actual instance, return its unique instance.  If the
        instance doesn't exist in self._moduleDict, return the currently
        halfborn instance.
        """

        try:
            return self._moduleDict[instance].instanceName
        except Exception:
            return self._halfBornInstanceName

    def get_modules_dir(self):
	return self._modules_dir

    def get_module_view_parent_window(self):
        # this could change
        return self.getModuleViewParentWindow()

    def getModuleViewParentWindow(self):
        return self._devide_app.get_main_window()
    
    def createModule(self, fullName, instanceName=None):
        """Try and create module fullName.  fullName is the complete module
        spec below application directory, e.g. modules.Readers.hdfRDR.
        """
        
	try:
            # think up name for this module (we have to think this up now
            # as the module might want to know about it whilst it's being
            # constructed
            instanceName = self._makeUniqueInstanceName(instanceName)
            self._halfBornInstanceName = instanceName
            
            # perform the conditional import/reload
            self.importReload(fullName)
            # importReload requires this afterwards for safety reasons
            exec('import %s' % fullName)
            # in THIS case, there is a McMillan hook which'll tell the
            # installer about all the devide modules. :)
            print "imported: " + str(id(sys.modules[fullName]))

	    # then instantiate the requested class
            moduleInstance = None
            exec('moduleInstance = %s.%s(self)' % (fullName,
                                                   fullName.split('.')[-1]))

            # and store it in our internal structures
            self._moduleDict[moduleInstance] = metaModule(moduleInstance,
                                                          instanceName)

            # it's now fully born ;)
            self._halfBornInstanceName = None


	except ImportError:
	    genUtils.logError("Unable to import module %s!" % fullName)
	    return None
	except Exception, e:
	    genUtils.logError("Unable to instantiate module %s: %s" \
                                % (fullName, str(e)))
	    return None

        # first apply the executionDisabled setting
        if self._executionDisabled:
            if hasattr(moduleInstance, 'disableExecution'):
                moduleInstance.disableExecution()
                                    
	# return the instance
	return moduleInstance

    def importReload(self, fullName):
        """This will import and reload a module if necessary.  Use this only
        for things in modules or userModules.

        If we're NOT running installed, this will run import on the module.
        If it's not the first time this module is imported, a reload will
        be run straight after.

        If we're running installed, reloading only makes sense for things in
        userModules, so it's only done for these modules.  At the moment,
        the stock Installer reload() is broken.  Even with my fixes, it doesn't
        recover memory used by old modules, see:
        http://trixie.triqs.com/pipermail/installer/2003-May/000303.html
        This is one of the reasons we try to avoid unnecessary reloads.

        You should use this as follows:
        moduleManager.importReloadModule('full.path.to.my.module')
        import full.path.to.my.module
        so that the module is actually brought into the calling namespace.

        importReload used to return the modulePrefix object, but this has
        been changed to force module writers to use a conventional import
        afterwards so that the McMillan installer will know about dependencies.
        """

        # this should yield modules or userModules
        modulePrefix = fullName.split('.')[0]

        # determine whether this is a new import
        if not sys.modules.has_key(fullName):
            newModule = True
        else:
            newModule = False
                
        # import the correct module - we have to do this in anycase to
        # get the thing into our local namespace
        exec('import ' + fullName)
            
        # there can only be a reload if this is not a newModule
        if not newModule:
            #if not self.isInstalled() or \
            #       modulePrefix == 'userModules':

            # we've changed the logic of this.  bugs in Installer have been
            # fixed, this shouldn't break things too badly.

            # we only reload if we're not running from an Installer
            # package (the __importsub__ check) OR if we are running
            # from Installer, but it's a userModule; there's no sense
            # in reloading a module from an Installer package as these
            # can never change in anycase
            exec('reload(' + fullName + ')')

        # we need to inject the import into the calling dictionary...
        # importing my.module results in "my" in the dictionary, so we
        # split at '.' and return the object bound to that name
        # return locals()[modulePrefix]
        # we DON'T do this anymore, so that module writers are forced to
        # use an import statement straight after calling importReload (or
        # somewhere else in the module)

    def isInstalled(self):
        """Returns True if devide is running from an Installed state.
        Installed of course refers to being installed with Gordon McMillan's
        Installer.  This can be used by devide modules to determine whether
        they should use reload or not.
        """
        return hasattr(modules, '__importsub__')

    def executeModule(self, instance):
        try:
            instance.executeModule()
        except Exception, e:
            mModule = self._moduleDict[instance]
            instanceName = mModule.instanceName
            moduleName = instance.__class__.__name__
            
            genUtils.logError('Unable to execute module %s (%s): %s' \
                              % (instanceName, moduleName, str(e)))
			      
    def viewModule(self, instance):
        instance.view()
    
    def deleteModule(self, instance):
        # first disconnect all outgoing connections
        inputs = self._moduleDict[instance].inputs
        outputs = self._moduleDict[instance].outputs

        # outputs is a list of lists of tuples, each tuple containing
        # moduleInstance and inputIdx of the consumer module
        for output in outputs:
            if output:
                # we just want to walk through the dictionary tuples
                for consumer in output:
                    # disconnect all consumers
                    consumer[0].setInput(consumer[1], None)
                    # the setInput could fail, which would throw an exception,
                    # but that's really just too deep: just in case
                    # we set it to None
                    consumer[0] = None
                    consumer[1] = -1

        # inputs is a list of tuples, each tuple containing moduleInstance
        # and outputIdx of the producer/supplier module
        for inputIdx in range(len(inputs)):
            instance.setInput(inputIdx, None)
            # set supplier to None - so we know it's nuked
            inputs[inputIdx] = None

        # we've disconnected completely - let's reset all lists
        self._moduleDict[instance].resetInputsOutputs()

        # remove the instance from the markedModules (if it's present)
        # 1. first find all keys that point to it
        mmKeys = [mmItem[0] for mmItem in self._markedModules.items()
                  if mmItem[1] == instance]
        # 2. remove all of em
        for mmKey in mmKeys:
            del self._markedModules[mmKey]
        
        # now we can finally call close on the instance
	instance.close()
        # if that worked (i.e. no exception) let's remove it from the dict
        del self._moduleDict[instance]


#         print "Deleted %s, %.2fM freed." % \
#               (instance.__class__.__name__,
#                (endFreeMemory - beginFreeMemory) / 1024.0 / 1024.0)
                                          
    def connectModules(self, output_module, output_idx,
                        input_module, input_idx):
        """Connect output_idx'th output of provider output_module to
        input_idx'th input of consumer input_module.
        """

	input_module.setInput(input_idx, output_module.getOutput(output_idx))
        
        # update the inputs thingy on the input_module
        self._moduleDict[input_module].inputs[input_idx] = (output_module,
                                                            output_idx)

        #
        self._moduleDict[output_module].outputs[output_idx].append(
            (input_module, input_idx))
	
    def disconnectModules(self, input_module, input_idx):
        """Disconnect a consumer module from its provider.

        This method will disconnect input_module from its provider by
        disconnecting the link between the provider and input_module at
        the input_idx'th input port of input_module.
        """

	input_module.setInput(input_idx, None)

        # trace it back to our supplier, and tell it that it has one
        # less consumer (if we even HAVE a supplier on this port)
        s = self._moduleDict[input_module].inputs[input_idx]
        if s:
            supp = s[0]
            suppOutIdx = s[1]
        
            oList = self._moduleDict[supp].outputs[suppOutIdx]
            del oList[oList.index((input_module, input_idx))]

        # indicate to the meta data that this module doesn't have an input
        # anymore
        self._moduleDict[input_module].inputs[input_idx] = None

    def deserialiseModuleInstances(self, pmsDict, connectionList):
        """Given a pickled stream, this method will recreate all modules,
        configure them and connect them up.  It returns a list of
        successfully instantiated modules.
        """
        
        # let's attempt to instantiate all the modules

        # newModulesDict will act as translator between pickled instanceName
        # and new instance!
        newModulesDict = {}
        for pmsTuple in pmsDict.items():
            # each pmsTuple == (instanceName, pms)
            newModule = self.createModule(pmsTuple[1].moduleName)
            if newModule:
                # set its config!
                try:
                    # we need to DEEP COPY the config, else it could easily
                    # happen that objects have bindings to the same configs!
                    # to see this go wrong, switch off the deepcopy, create
                    # a network by copying/pasting a vtkPolyData, load
                    # two datasets into a slice viewer... now save the whole
                    # thing and load it: note that the two readers are now
                    # reading the same file!
                    configCopy = copy.deepcopy(pmsTuple[1].moduleConfig)
                    newModule.setConfig(configCopy)
                except Exception, e:
                    # it could be a module with no defined config logic
                    genUtils.logWarning(
                        'Could not restore state/config to module %s: %s' %
                        (newModule.__class__.__name__, e))
                
                # and record that it's been recreated (once again keyed
                # on the OLD unique instance name)
                newModulesDict[pmsTuple[1].instanceName] = newModule

        # now we're going to connect all of the successfully created
        # modules together; we iterate DOWNWARDS through the different
        # consumerTypes
        
        newConnections = []
        for connectionType in range(max(self.consumerTypeTable.values()) + 1):
            typeConnections = [connection for connection in connectionList
                               if connection.connectionType == connectionType]
            
            for connection in typeConnections:
                if newModulesDict.has_key(connection.sourceInstanceName) and \
                   newModulesDict.has_key(connection.targetInstanceName):
                    sourceM = newModulesDict[connection.sourceInstanceName]
                    targetM = newModulesDict[connection.targetInstanceName]
                    # attempt connecting them
                    print "connecting %s:%d to %s:%d..." % \
                          (sourceM.__class__.__name__, connection.outputIdx,
                           targetM.__class__.__name__, connection.inputIdx)

                    try:
                        self.connectModules(sourceM, connection.outputIdx,
                                            targetM, connection.inputIdx)
                    except:
                        pass
                    else:
                        newConnections.append(connection)

        # now do the POST connection module config!
        for oldInstanceName,newModuleInstance in newModulesDict.items():
            # retrieve the pickled module state
            pms = pmsDict[oldInstanceName]
            # take care to deep copy the config
            configCopy = copy.deepcopy(pms.moduleConfig)

            # now try to call setConfigPostConnect
            try:
                newModuleInstance.setConfigPostConnect(configCopy)
            except AttributeError:
                pass
            except Exception, e:
                # it could be a module with no defined config logic
                genUtils.logWarning(
                    'Could not restore post connect state/config to module '
                    '%s: %s' % (newModuleInstance.__class__.__name__, e))
                


        # we return a dictionary, keyed on OLD pickled name with value
        # the newly created module-instance and a list with the connections
        return (newModulesDict, newConnections)

    def serialiseModuleInstances(self, moduleInstances):
        """Given 
        """

        # dictionary of pickled module instances keyed on unique module
        # instance name
        pmsDict = {}
        # we'll use this list internally to check later (during connection
        # pickling) which modules are being written away
        pickledModuleInstances = []
        
        for moduleInstance in moduleInstances:
            if self._moduleDict.has_key(moduleInstance):

                # first get the metaModule
                mModule = self._moduleDict[moduleInstance]
                
                # create a picklable thingy
                pms = pickledModuleState()
                
                try:
                    print "SERIALISE: %s - %s" % \
                          (str(moduleInstance),
                           str(moduleInstance.getConfig()))
                    pms.moduleConfig = moduleInstance.getConfig()
                except AttributeError, e:
                    genUtils.logWarning(
                        'Could not extract state (config) from module %s: %s' \
                        % (moduleInstance.__class__.__name__, str(e)))

                    # if we can't get a config, we pickle a default
                    pms.moduleConfig = defaultConfigClass()
                    
                #pms.moduleName = moduleInstance.__class__.__name__
                # we need to store the complete module name
                pms.moduleName = moduleInstance.__class__.__module__

                # this will only be used for uniqueness purposes
                pms.instanceName = mModule.instanceName

                pmsDict[pms.instanceName] = pms
                pickledModuleInstances.append(moduleInstance)

        # now iterate through all the actually pickled module instances
        # and store all connections in a connections list
        # three different types of connections:
        # 0. connections with source modules with no inputs
        # 1. normal connections
        # 2. connections with targets that are exceptions, e.g. sliceViewer
        connectionList = []
        for moduleInstance in pickledModuleInstances:
            mModule = self._moduleDict[moduleInstance]
            # we only have to iterate through all outputs
            for outputIdx in range(len(mModule.outputs)):
                outputConnections = mModule.outputs[outputIdx]
                # each output can of course have multiple outputConnections
                # each outputConnection is a tuple:
                # (consumerModule, consumerInputIdx)
                for outputConnection in outputConnections:
                    if outputConnection[0] in pickledModuleInstances:
                        # this means the consumerModule is also one of the
                        # modules to be pickled and so this connection
                        # should be stored

                        # find the type of connection (1, 2, 3), work from
                        # the back...
                        moduleClassName = \
                                        outputConnection[0].__class__.__name__
                        
                        if moduleClassName in self.consumerTypeTable:
                            connectionType = self.consumerTypeTable[
                                moduleClassName]
                        else:
                            connectionType = 1
                            # FIXME: we still have to check for 0: iterate
                            # through all inputs, check that none of the
                            # supplier modules are in the list that we're
                            # going to pickle

                        print '%s has connection type %d' % \
                              (outputConnection[0].__class__.__name__,
                               connectionType)
                        
                        connection = pickledConnection(
                            mModule.instanceName, outputIdx,
                            self._moduleDict[outputConnection[0]].instanceName,
                            outputConnection[1],
                            connectionType)
                                                       
                        connectionList.append(connection)

        return (pmsDict, connectionList)

    def genericProgressCallback(self, progressObject,
                                progressObjectName, progress, progressText):
        """progress between 0.0 and 1.0.
        """

        
        if self._inProgressCallback.testandset():

            # first check if execution has been disabled
            # the following bit of code is risky: the ITK to VTK bridges
            # seem to be causing segfaults when we abort too soon
#             if not self._executionEnabled:
#                 try:
#                     progressObject.SetAbortExecute(1)
#                 except Exception:
#                     pass

#                 try:
#                     progressObject.SetAbortGenerateData(1)
#                 except Exception:
#                     pass
                    
#                 progress = 1.0
#                 progressText = 'Execution ABORTED.'
            
            progressP = progress * 100.0
            fullText = '%s: %s' % (progressObjectName, progressText)
            if abs(progressP - 100.0) < 0.01:
                # difference smaller than a hundredth
                fullText += ' [DONE]'

            self.setProgress(progressP, fullText)
            self._inProgressCallback.unlock()
    
#     def vtk_progress_cb(self, process_object):
#         """Default callback that can be used for VTK ProcessObject callbacks.

#         In all VTK-using child classes, this method can be used if such a
#         class wants to show its process graphically.  You'll have to use
#         a lambda callback in order to pass the process_object along.  See
#         vtk_plydta_rdr.py for a simple example.
#         """

#         # if this is called while still in progress, we do nothing...
#         # it means multi-threaded VTK objects are calling back into us (yuck)
#         if self._inProgressCallback.testandset():
#             vtk_progress = process_object.GetProgress() * 100.0
#             progressText = process_object.GetClassName() + ': ' + \
#                            process_object.GetProgressText()
#             if abs(vtk_progress - 100.0) < 0.01:
#                 # difference smaller than a hundredth
#                 progressText += ' [DONE]'

#             self.setProgress(vtk_progress, progressText)
#             self._inProgressCallback.unlock()
            
#     def vtk_poll_error(self):
#         """This method should be called whenever VTK processing might have
#         taken place, e.g. in the execute() method of a devide module.

#         update() will be called on the central vtk_log_window.  This will
#         only show if the filesize of the vtk log file has changed since the
#         last call.
#         """
#         print "vtk_poll_error is DEPRECATED"

    def setProgress(self, progress, message):
        """Progress is in percent.
        """
        self._devide_app.setProgress(progress, message)

    def _makeUniqueInstanceName(self, instanceName=None):
        """Ensure that instanceName is unique or create a new unique
        instanceName.

        If instanceName is None, a unique one will be created.  An
        instanceName (whether created or passed) will be permuted until it
        unique and then returned.
        """
        
        # first we make sure we have a unique instance name
        if not instanceName:
            instanceName = "dvm%d" % (len(self._moduleDict),)

        # now make sure that instanceName is unique
        uniqueName = False
        while not uniqueName:
            # first check that this doesn't exist in the module dictionary
            uniqueName = True
            for mmt in self._moduleDict.items():
                if mmt[1].instanceName == instanceName:
                    uniqueName = False
                    break

            if not uniqueName:
                # this means that this exists already!
                # create a random 3 character string
                chars = 'abcdefghijklmnopqrstuvwxyz'

                tl = ""
                for i in range(3):
                    tl += choice(chars)
                        
                instanceName = "%s%s%d" % (instanceName, tl,
                                           len(self._moduleDict))

        
        return instanceName


    def markModule(self, instance, name):
        """Add instance to self._markedModules dictionary with name as
        key.  Anything other than a module instance will not be added.

        
        """

        if instance in self._moduleDict:
            self._markedModules[name] = instance

    def getMarkedModule(self, name):
        """Return module instance from self._markedModules with key == name.

        If the key does not exist, returns None.
        """

        if name in self._markedModules:
            return self._markedModules[name]
        else:
            return None
