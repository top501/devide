# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from moduleBase import moduleBase
from moduleMixins import \
     introspectModuleMixin
import moduleUtils

import gdcm
import vtk
import vtkgdcm
import wx

class DICOMReader(introspectModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        self._reader = vtkgdcm.vtkGDCMImageReader()

        moduleUtils.setupVTKObjectProgress(self, self._reader,
                                           'Reading DICOM data')

        self._view_frame = None
        self._file_dialog = None
        self._config.dicom_filenames = []

        self.sync_module_logic_with_config()

    def close(self):
        introspectModuleMixin.close(self)

        # we just delete our binding.  Destroying the view_frame
        # should also take care of this one.
        del self._file_dialog

        if self._view_frame is not None:
            self._view_frame.Destroy()

        del self._reader

        moduleBase.close(self) 


    def get_input_descriptions(self):
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('DICOM data (vtkStructuredPoints)',
                'VTK Medical Image Properties',
                'Direction Cosines')
    
    def get_output(self, idx):
        if idx == 0:
            return self._reader.GetOutput()
        elif idx == 1:
            return self._reader.GetMedicalImageProperties()
        else:
            return self._reader.GetDirectionCosines()

    def logic_to_config(self):
        # we deliberately don't do any processing here, as we want to
        # limit all DICOM parsing to the execute_module
        pass
        

    def config_to_logic(self):
        # we deliberately don't add filenames to the reader here, as
        # we would need to sort them, which would imply scanning all
        # of them during this step
        pass


    def view_to_config(self):
        lb = self._view_frame.dicom_files_lb
        lb.GetStrings()
        
        # just clear out the current list
        # and copy everything
        self._config.dicom_filenames[:] = lb.GetStrings()[:]

    def config_to_view(self):
        # get listbox, clear it out, add filenames from the config
        lb = self._view_frame.dicom_files_lb
        lb.Clear()
        lb.AppendItems(self._config.dicom_filenames)
    
    def execute_module(self):
        # get filenames from config, sort them, then add them to the
        # reader
      
        # have to  cast to normal strings (from unicode)
        filenames = [str(i) for i in self._config.dicom_filenames]

        # we only sort and derive slice-based spacing if there are
        # more than 1 filenames
        if len(filenames) > 1:
            sorter = gdcm.IPPSorter()
            sorter.SetComputeZSpacing(True)
            ret = sorter.Sort(filenames)
            if not ret:
                raise RuntimeError(
                'Could not sort DICOM filenames to load.')

            # impose derived spacing on the reader
            spacing = list(self._reader.GetDataSpacing())
            spacing[2] = sorter.GetZSpacing()
            self._reader.SetDataSpacing(spacing)

            # then give the reader the sorted list of files
            sa = vtk.vtkStringArray()
            for fn in sorter.GetFilenames(): 
                sa.InsertNextValue(fn)

            self._reader.SetFileNames(sa)

        elif len(filenames) == 1:
            self._reader.SetFileName(filenames[0])

        else:
            raise RuntimeError(
                    'No DICOM filenames to read.')

        # now do the actual reading
        self._reader.Update()

        if False:
            # first determine axis labels based on IOP ####################
            iop = self._reader.GetImageOrientationPatient()
            row = iop[0:3]
            col = iop[3:6]
            # the cross product (plane normal) based on the row and col will
            # also be in the RAH system (I THINK)
            norm = [0,0,0]
            vtk.vtkMath.Cross(row, col, norm)

            xl = misc_utils.major_axis_from_iop_cosine(row)
            yl = misc_utils.major_axis_from_iop_cosine(col)
            zl = misc_utils.major_axis_from_iop_cosine(norm)

            lut = {'L' : 0, 'R' : 1, 'P' : 2, 'A' : 3, 'F' : 4, 'H' : 5}

            if xl and yl and zl:
                # add this data as a vtkFieldData
                fd = self._reader.GetOutput().GetFieldData()

                axis_labels_array = vtk.vtkIntArray()
                axis_labels_array.SetName('axis_labels_array')

                for l in xl + yl + zl:
                    axis_labels_array.InsertNextValue(lut[l])

                fd.AddArray(axis_labels_array)

            # window/level ###############################################
        

    def _create_view_frame(self):
        import modules.readers.resources.python.DICOMReaderViewFrame
        reload(modules.readers.resources.python.DICOMReaderViewFrame)

        self._view_frame = moduleUtils.instantiateModuleViewFrame(
            self, self._moduleManager,
            modules.readers.resources.python.DICOMReaderViewFrame.\
            DICOMReaderViewFrame)

        # make sure the listbox is empty
        self._view_frame.dicom_files_lb.Clear()

        object_dict = {'vtkGDCMImageReader' : self._reader}
        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, self._view_frame, self._view_frame.view_frame_panel,
            object_dict, None)

        moduleUtils.createECASButtons(self, self._view_frame,
                                      self._view_frame.view_frame_panel)

        # now add the event handlers
        self._view_frame.add_files_b.Bind(wx.EVT_BUTTON,
                self._handler_add_files_b)
        self._view_frame.remove_files_b.Bind(wx.EVT_BUTTON,
                self._handler_remove_files_b)


        # follow moduleBase convention to indicate that we now have
        # a view
        self.view_initialised = True

    def view(self, parent_window=None):
        if self._view_frame is None:
            self._create_view_frame()
            self.sync_module_view_with_logic()
            
        self._view_frame.Show(True)
        self._view_frame.Raise()

    def _handler_add_files_b(self, event):
        if not self._file_dialog:
            self._file_dialog = wx.FileDialog(
                self._view_frame,
                'Select files to add to the list', "", "",
                "DICOM files (*.dcm)|*.dcm|All files (*)|*",
                wx.OPEN | wx.MULTIPLE)
            
        if self._file_dialog.ShowModal() == wx.ID_OK:
            new_filenames = self._file_dialog.GetPaths()

            # only add filenames that are not in there yet...
            lb = self._view_frame.dicom_files_lb

            # create new dictionary with current filenames as keys
            dup_dict = {}.fromkeys(lb.GetStrings(), 1)

            fns_to_add = [fn for fn in new_filenames
                          if fn not in dup_dict]

            lb.AppendItems(fns_to_add)

    def _handler_remove_files_b(self, event):
        lb = self._view_frame.dicom_files_lb
        sels = list(lb.GetSelections())

        # we have to delete from the back to the front
        sels.sort()
        sels.reverse()

        for sel in sels:
            lb.Delete(sel)
