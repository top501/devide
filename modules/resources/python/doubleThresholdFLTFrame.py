#!/usr/bin/env python
# generated by wxGlade 0.2.1 on Mon Jan 27 21:13:04 2003

from wxPython.wx import *

class doubleThresholdFLTFrame(wxFrame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: doubleThresholdFLTFrame.__init__
        kwds["style"] = wxCAPTION|wxMINIMIZE_BOX|wxMAXIMIZE_BOX|wxSYSTEM_MENU|wxRESIZE_BORDER
        wxFrame.__init__(self, *args, **kwds)
        self.panel_1 = wxPanel(self, -1)
        self.label_1 = wxStaticText(self.panel_1, -1, "Lower threshold")
        self.lowerThresholdSliderId  =  wxNewId()
        self.lowerThresholdSlider = wxSlider(self.panel_1, self.lowerThresholdSliderId , 0, -2500, 2500, style=wxSL_HORIZONTAL|wxSL_AUTOTICKS|wxSL_LABELS)
        self.lowerThresholdTextId  =  wxNewId()
        self.lowerThresholdText = wxTextCtrl(self.panel_1, self.lowerThresholdTextId , "", style=wxTE_PROCESS_ENTER)
        self.label_2 = wxStaticText(self.panel_1, -1, "Upper threshold")
        self.upperThresholdSliderId  =  wxNewId()
        self.upperThresholdSlider = wxSlider(self.panel_1, self.upperThresholdSliderId , 0, -2500, 2500, style=wxSL_HORIZONTAL|wxSL_AUTOTICKS|wxSL_LABELS)
        self.upperThresholdTextId  =  wxNewId()
        self.upperThresholdText = wxTextCtrl(self.panel_1, self.upperThresholdTextId , "", style=wxTE_PROCESS_ENTER)
        self.realtimeUpdateCheckboxId  =  wxNewId()
        self.realtimeUpdateCheckbox = wxCheckBox(self.panel_1, self.realtimeUpdateCheckboxId , "Real-time updating of output during slider activity")
        self.replaceInCheckBox = wxCheckBox(self.panel_1, -1, "Replace IN values with:")
        self.replaceInText = wxTextCtrl(self.panel_1, -1, "")
        self.replaceOutCheckBox = wxCheckBox(self.panel_1, -1, "Replace OUT values with:")
        self.replaceOutText = wxTextCtrl(self.panel_1, -1, "")
        self.label_3 = wxStaticText(self.panel_1, -1, "Output data type")
        self.outputDataTypeChoice = wxChoice(self.panel_1, -1, choices=["choice 1"])
        self.label_1_copy_1 = wxStaticText(self.panel_1, -1, "Examine the")
        self.objectChoiceId  =  wxNewId()
        self.objectChoice = wxChoice(self.panel_1, self.objectChoiceId , choices=["vtkImageThreshold"])
        self.label_2_copy_1 = wxStaticText(self.panel_1, -1, "or")
        self.pipelineButtonId  =  wxNewId()
        self.pipelineButton = wxButton(self.panel_1, self.pipelineButtonId , "Pipeline")
        self.cancel_button = wxButton(self.panel_1, wxID_CANCEL, "Cancel")
        self.SYNC_ID  =  wxNewId()
        self.sync_button = wxButton(self.panel_1, self.SYNC_ID , "Sync")
        self.APPLY_ID  =  wxNewId()
        self.apply_button = wxButton(self.panel_1, self.APPLY_ID , "Apply")
        self.EXECUTE_ID  =  wxNewId()
        self.execute_button = wxButton(self.panel_1, self.EXECUTE_ID , "Execute")
        self.ok_button = wxButton(self.panel_1, wxID_OK, "OK")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: doubleThresholdFLTFrame.__set_properties
        self.SetTitle("Double Threshold Filter")
        self.replaceInCheckBox.SetValue(1)
        self.replaceOutCheckBox.SetValue(1)
        self.outputDataTypeChoice.SetSelection(0)
        self.objectChoice.SetSelection(0)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: doubleThresholdFLTFrame.__do_layout
        sizer_1 = wxBoxSizer(wxVERTICAL)
        sizer_5 = wxBoxSizer(wxVERTICAL)
        sizer_2 = wxBoxSizer(wxHORIZONTAL)
        sizer_4 = wxBoxSizer(wxHORIZONTAL)
        sizer_3 = wxBoxSizer(wxHORIZONTAL)
        grid_sizer_2 = wxFlexGridSizer(2, 2, 0, 0)
        grid_sizer_1 = wxFlexGridSizer(2, 3, 2, 2)
        grid_sizer_1.Add(self.label_1, 0, wxLEFT|wxRIGHT|wxALIGN_BOTTOM, 2)
        grid_sizer_1.Add(self.lowerThresholdSlider, 0, wxEXPAND, 0)
        grid_sizer_1.Add(self.lowerThresholdText, 0, wxALIGN_BOTTOM, 0)
        grid_sizer_1.Add(self.label_2, 0, wxLEFT|wxRIGHT|wxALIGN_BOTTOM, 2)
        grid_sizer_1.Add(self.upperThresholdSlider, 0, wxEXPAND, 0)
        grid_sizer_1.Add(self.upperThresholdText, 0, wxALIGN_BOTTOM, 0)
        grid_sizer_1.AddGrowableCol(1)
        sizer_5.Add(grid_sizer_1, 1, wxALL|wxEXPAND, 4)
        sizer_5.Add(self.realtimeUpdateCheckbox, 0, wxALL, 4)
        grid_sizer_2.Add(self.replaceInCheckBox, 0, 0, 0)
        grid_sizer_2.Add(self.replaceInText, 0, wxEXPAND, 0)
        grid_sizer_2.Add(self.replaceOutCheckBox, 0, 0, 0)
        grid_sizer_2.Add(self.replaceOutText, 0, wxEXPAND, 0)
        grid_sizer_2.AddGrowableCol(1)
        sizer_5.Add(grid_sizer_2, 0, wxALL|wxEXPAND, 4)
        sizer_3.Add(self.label_3, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        sizer_3.Add(self.outputDataTypeChoice, 1, 0, 0)
        sizer_5.Add(sizer_3, 0, wxLEFT|wxRIGHT|wxBOTTOM|wxEXPAND, 4)
        sizer_4.Add(self.label_1_copy_1, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        sizer_4.Add(self.objectChoice, 0, wxALIGN_CENTER_VERTICAL, 0)
        sizer_4.Add(self.label_2_copy_1, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        sizer_4.Add(self.pipelineButton, 0, wxALIGN_CENTER_VERTICAL, 0)
        sizer_5.Add(sizer_4, 0, wxALL|wxEXPAND, 4)
        sizer_2.Add(self.cancel_button, 0, wxALL, 2)
        sizer_2.Add(self.sync_button, 0, wxALL, 2)
        sizer_2.Add(self.apply_button, 0, wxALL, 2)
        sizer_2.Add(self.execute_button, 0, wxALL, 2)
        sizer_2.Add(self.ok_button, 0, wxALL, 2)
        sizer_5.Add(sizer_2, 0, wxALL, 5)
        self.panel_1.SetAutoLayout(1)
        self.panel_1.SetSizer(sizer_5)
        sizer_5.Fit(self.panel_1)
        sizer_5.SetSizeHints(self.panel_1)
        sizer_1.Add(self.panel_1, 1, wxEXPAND, 0)
        self.SetAutoLayout(1)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        sizer_1.SetSizeHints(self)
        self.Layout()
        # end wxGlade

# end of class doubleThresholdFLTFrame


