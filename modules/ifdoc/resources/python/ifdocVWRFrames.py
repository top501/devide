#!/usr/bin/env python
# generated by wxGlade 0.3.1 on Mon Sep 01 22:54:44 2003

from wxPython.wx import *
# with the very ugly two lines below, make sure x capture is not used
# this should rather be an ivar of the wxVTKRenderWindowInteractor!
import vtk.wx.wxVTKRenderWindowInteractor
vtk.wx.wxVTKRenderWindowInteractor.WX_USE_X_CAPTURE = 0
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

class viewerFrame(wxFrame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: viewerFrame.__init__
        kwds["style"] = wxDEFAULT_FRAME_STYLE
        wxFrame.__init__(self, *args, **kwds)
        self.panel_1 = wxPanel(self, -1)
        self.showControlsButtonId  =  wxNewId()
        self.button_2 = wxButton(self.panel_1, self.showControlsButtonId , "Show Controls")
        self.resetCameraButtonId  =  wxNewId()
        self.resetCameraButton_copy = wxButton(self.panel_1, self.resetCameraButtonId , "Reset Camera")
        self.introspectPipelineButtonId  =  wxNewId()
        self.button_5_copy = wxButton(self.panel_1, self.introspectPipelineButtonId , "Introspect")
        self.threedRWI = wxVTKRenderWindowInteractor(self.panel_1, -1)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: viewerFrame.__set_properties
        self.SetTitle("ifdoc Viewer")
        self.SetSize((704, 596))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: viewerFrame.__do_layout
        sizer_1 = wxBoxSizer(wxVERTICAL)
        sizer_8 = wxBoxSizer(wxVERTICAL)
        sizer_2 = wxBoxSizer(wxHORIZONTAL)
        sizer_15 = wxBoxSizer(wxVERTICAL)
        sizer_15.Add(self.button_2, 0, wxBOTTOM|wxEXPAND, 4)
        sizer_15.Add(self.resetCameraButton_copy, 0, wxBOTTOM|wxEXPAND, 4)
        sizer_15.Add(self.button_5_copy, 0, wxBOTTOM|wxEXPAND, 4)
        sizer_2.Add(sizer_15, 0, wxRIGHT|wxEXPAND, 4)
        sizer_2.Add(self.threedRWI, 1, wxEXPAND, 0)
        sizer_8.Add(sizer_2, 1, wxALL|wxEXPAND, 7)
        self.panel_1.SetAutoLayout(1)
        self.panel_1.SetSizer(sizer_8)
        sizer_8.Fit(self.panel_1)
        sizer_8.SetSizeHints(self.panel_1)
        sizer_1.Add(self.panel_1, 1, wxEXPAND, 0)
        self.SetAutoLayout(1)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

# end of class viewerFrame


class controlFrame(wxFrame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: controlFrame.__init__
        kwds["style"] = wxDEFAULT_FRAME_STYLE
        wxFrame.__init__(self, *args, **kwds)
        self.panel_4 = wxPanel(self, -1)
        self.autoAnimateButtonId  =  wxNewId()
        self.button_1 = wxButton(self.panel_4, self.autoAnimateButtonId , "Auto Animate")
        self.label_3_copy = wxStaticText(self.panel_4, -1, "Step through:")
        self.timeStepSliderId  =  wxNewId()
        self.timeStepSlider = wxSlider(self.panel_4, self.timeStepSliderId , 0, 0, 10, style=wxSL_HORIZONTAL|wxSL_AUTOTICKS)
        self.timeStepSpinCtrlId  =  wxNewId()
        self.timeStepSpinCtrl = wxSpinCtrl(self.panel_4, self.timeStepSpinCtrlId , "", min=0, max=100)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: controlFrame.__set_properties
        self.SetTitle("ifdoc Control")
        self.timeStepSlider.SetSize((150, 15))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: controlFrame.__do_layout
        sizer_6 = wxBoxSizer(wxVERTICAL)
        sizer_9 = wxBoxSizer(wxVERTICAL)
        sizer_14 = wxBoxSizer(wxVERTICAL)
        sizer_11 = wxStaticBoxSizer(wxStaticBox(self.panel_4, -1, "Animation"), wxVERTICAL)
        sizer_12_copy = wxBoxSizer(wxHORIZONTAL)
        sizer_11.Add(self.button_1, 0, wxALL, 7)
        sizer_12_copy.Add(self.label_3_copy, 0, wxRIGHT|wxALIGN_CENTER_VERTICAL, 3)
        sizer_12_copy.Add(self.timeStepSlider, 0, wxRIGHT|wxALIGN_CENTER_VERTICAL, 3)
        sizer_12_copy.Add(self.timeStepSpinCtrl, 0, wxALIGN_CENTER_VERTICAL, 0)
        sizer_11.Add(sizer_12_copy, 1, wxLEFT|wxRIGHT|wxBOTTOM, 7)
        sizer_14.Add(sizer_11, 1, wxEXPAND, 0)
        sizer_9.Add(sizer_14, 1, wxALL|wxEXPAND, 7)
        self.panel_4.SetAutoLayout(1)
        self.panel_4.SetSizer(sizer_9)
        sizer_9.Fit(self.panel_4)
        sizer_9.SetSizeHints(self.panel_4)
        sizer_6.Add(self.panel_4, 1, 0, 0)
        self.SetAutoLayout(1)
        self.SetSizer(sizer_6)
        sizer_6.Fit(self)
        sizer_6.SetSizeHints(self)
        self.Layout()
        # end wxGlade

# end of class controlFrame


class MyFrame(wxFrame):
    def __init__(self, *args, **kwds):
        # content of this block not found: did you rename this class?
        pass

    def __set_properties(self):
        # content of this block not found: did you rename this class?
        pass

    def __do_layout(self):
        # content of this block not found: did you rename this class?
        pass

# end of class MyFrame


class MyFrame1(wxFrame):
    def __init__(self, *args, **kwds):
        # content of this block not found: did you rename this class?
        pass

    def __set_properties(self):
        # content of this block not found: did you rename this class?
        pass

    def __do_layout(self):
        # content of this block not found: did you rename this class?
        pass

# end of class MyFrame1

