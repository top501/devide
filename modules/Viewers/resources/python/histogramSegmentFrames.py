#!/usr/bin/env python
# generated by wxGlade 0.3.3 on Mon Aug 16 00:22:23 2004

import wx
import wx.grid

# with the very ugly two lines below, make sure x capture is not used
# this should rather be an ivar of the wxVTKRenderWindowInteractor!
import vtk.wx.wxVTKRenderWindowInteractor
vtk.wx.wxVTKRenderWindowInteractor.WX_USE_X_CAPTURE = 0
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

class viewFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: viewFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.viewFramePanel = wx.Panel(self, -1)
        self.rwi = wxVTKRenderWindowInteractor(self.viewFramePanel, -1)
        self.label_1 = wx.StaticText(self.viewFramePanel, -1, "Cursor values")
        self.cursorValuesText = wx.TextCtrl(self.viewFramePanel, -1, "")
        self.selectorGrid = wx.grid.Grid(self.viewFramePanel, -1)
        self.selectorTypeChoice = wx.Choice(self.viewFramePanel, -1, choices=["Polygon", "Spline"])
        self.addButton = wx.Button(self.viewFramePanel, -1, "Add selector")
        self.removeButton = wx.Button(self.viewFramePanel, -1, "Remove")
        self.changeHandlesButton = wx.Button(self.viewFramePanel, -1, "+/- Handles")
        self.static_line_1 = wx.StaticLine(self.viewFramePanel, -1)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: viewFrame.__set_properties
        self.SetTitle("frame_1")
        self.selectorGrid.CreateGrid(5, 1)
        self.selectorGrid.EnableEditing(0)
        self.selectorGrid.EnableDragRowSize(0)
        self.selectorGrid.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)
        self.selectorGrid.SetColLabelValue(0, "Type")
        self.selectorTypeChoice.SetSelection(0)
        self.changeHandlesButton.SetToolTipString("Change number of handles for selected selectors.")
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: viewFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_7 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add((480, 0), 0, 0, 0)
        sizer_4.Add(self.rwi, 1, wx.EXPAND, 0)
        sizer_4.Add((0, 320), 0, 0, 0)
        sizer_3.Add(sizer_4, 1, wx.BOTTOM|wx.EXPAND, 7)
        sizer_5.Add(self.label_1, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_5.Add(self.cursorValuesText, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_3.Add(sizer_5, 0, wx.EXPAND, 0)
        sizer_6.Add(self.selectorGrid, 1, wx.EXPAND, 0)
        sizer_7.Add(self.selectorTypeChoice, 0, wx.BOTTOM|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 7)
        sizer_7.Add(self.addButton, 0, wx.BOTTOM, 7)
        sizer_7.Add(self.removeButton, 0, wx.BOTTOM, 7)
        sizer_7.Add(self.changeHandlesButton, 0, 0, 0)
        sizer_6.Add(sizer_7, 0, wx.LEFT|wx.EXPAND, 7)
        sizer_6.Add((0, 160), 0, 0, 0)
        sizer_3.Add(sizer_6, 0, wx.TOP|wx.EXPAND, 7)
        sizer_3.Add(self.static_line_1, 0, wx.TOP|wx.EXPAND, 7)
        sizer_2.Add(sizer_3, 1, wx.ALL|wx.EXPAND, 7)
        self.viewFramePanel.SetAutoLayout(1)
        self.viewFramePanel.SetSizer(sizer_2)
        sizer_2.Fit(self.viewFramePanel)
        sizer_2.SetSizeHints(self.viewFramePanel)
        sizer_1.Add(self.viewFramePanel, 1, wx.EXPAND, 0)
        self.SetAutoLayout(1)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        sizer_1.SetSizeHints(self)
        self.Layout()
        # end wxGlade

# end of class viewFrame

