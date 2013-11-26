#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''sketch python'''

import wx
from wx.lib.masked import NumCtrl
import os
import Image, ImageChops, ImageFilter

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        '''
        create the window
        '''
        self.FrameWidth = 840
        self.FrameHeight = 570
        self.ImagePanelWidth = 720
        self.ImagePanelHeight = 500
        wx.Frame.__init__(self, parent, title=title, size=(self.FrameWidth, self.FrameHeight),
            style=wx.DEFAULT_FRAME_STYLE^wx.MAXIMIZE_BOX^wx.RESIZE_BORDER)

        filemenu = wx.Menu()

        menuOpen = filemenu.Append(wx.ID_OPEN, 'Open', 'Open a image')
        filemenu.AppendSeparator()
        menuSave = filemenu.Append(wx.ID_SAVE, 'Save', 'Save')
        filemenu.AppendSeparator()
        menuExit = filemenu.Append(wx.ID_EXIT, 'Exit', 'Exit')

        self.Bind(wx.EVT_MENU, self.OnClose, menuExit)
        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
        self.Bind(wx.EVT_MENU, self.OnSave, menuSave)

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, 'File')        

        self.CtrlPanel = wx.Panel(self,-1,pos=(0,10),size=(100,500)) 
        self.ImageBackPanel = wx.Panel(self,-1,pos=(110,10),size=(self.ImagePanelWidth,self.ImagePanelHeight)) 
        self.ImagePanel = wx.Panel(self.ImageBackPanel,-1) # 

        # Drag && Drop
        dt = FileDropTarget(self.ImageBackPanel)
        self.ImageBackPanel.SetDropTarget(dt)
        #

        convertButton = wx.Button(self.CtrlPanel, -1, label='Convert', pos=(10,10), size=(70, 35))
        self.Bind(wx.EVT_BUTTON, self.ConvertImage, convertButton)

        wx.StaticText(self.CtrlPanel, -1, label=u'输入模糊半径\n\n 范围1-10', pos=(7, 60))
        self.input = wx.lib.masked.numctrl.NumCtrl(self.CtrlPanel, -1, value=2, pos=(60,85), style=1, min=1, max=10,
                autoSize=False, invalidBackgroundColour = 'Red', selectOnEntry=True)
        self.input.SetSize((40,20))

        self.SetMenuBar(menuBar)
        self.Show()
        self.Centre()

    def OnClose(self, e): #menu close
        self.Close()

    def OnOpen(self, e):  # menu open
        dirname = ''
        dlg = wx.FileDialog(self, 'Choose a file', dirname, '', '*.jpg;*.png;*.gif;*.bmp')
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            path = os.path.join(dirname, filename)
            self.OnImage(path)
        dlg.Destroy()

    def OnSave(self, e):
        file_wildcard = "JPEG(*.jpg)|*.jpg|PNG(*.png)|*.png|GIF(*.gif)|*.gif|BMP(*.bmp)|*.bmp|All files(*.*)|*.*"   
        dlg = wx.FileDialog(self,   
                            "Save as ...", 
                            os.getcwd(),  
                            style = wx.SAVE | wx.OVERWRITE_PROMPT,  
                            wildcard = file_wildcard)  
        if dlg.ShowModal() == wx.ID_OK:  
            filename = dlg.GetPath()  

            self.ImageConverted.save(filename)

        dlg.Destroy() 

    def OnImage(self, path): # the path is ready
        '''
        get and process image data
        resize image
        '''
        image = Image.open(path, 'r')
        width = image.size[0]
        height = image.size[1]
        # scale rate
        c = 1
        if (width > self.ImagePanelWidth) or (height > self.ImagePanelHeight):
            wc = width/float(self.ImagePanelWidth)
            hc = height/float(self.ImagePanelHeight)
            if wc >= hc:
                c = wc
            else :
                c= hc
        width = int(width/c); height = int(height/c)
        imageSize = (width, height)
        self.OpenImage = image = image.resize(imageSize)
        self.OnImagePanel(image)

    def OnImagePanel(self, image):
        '''
        put method;; used by ConvertImage()
        image --- PIL obj
        '''
        bitmap = self.ConvertToWxImage(image)
        self.ImagePanel.Destroy()
        self.ImagePanel = wx.Panel(self.ImageBackPanel,-1,pos=(0,0),size=image.size)
        wx.StaticBitmap(parent=self.ImagePanel, bitmap=bitmap)
        self.ImagePanel.Centre()
        self.ImagePanel.Refresh()

    def ConvertToWxImage(self, image):
        self.ImageConverted = image
        temp = wx.EmptyImage(image.size[0], image.size[1])
        temp.SetData(image.convert("RGB").tostring())
        temp.SetAlphaData(image.convert("RGBA").tostring()[3::4])        
        bitmap = wx.BitmapFromImage(temp)
        return bitmap

    def ConvertImage(self, e):
        '''
        convert the origin image to sketch image
        '''
        if not(self.rightRadius()):
            return
        
        image = self.OpenImage
        disColourImg = image.convert("L")
        invertImg = ImageChops.invert(disColourImg)
        gaussblurImg = invertImg.filter(ImageFilter.GaussianBlur(radius=self.input.GetValue()))
        dodgeImg = self.dodgeColor(disColourImg, gaussblurImg)
        self.OnImagePanel(dodgeImg)

    def dodgeColor(self, baseImg, mixImg):
        '''
        dodge two iamges' color
        '''
        width = baseImg.size[0]
        height = baseImg.size[1]
        basePix = baseImg.load()
        mixPix = mixImg.load()
        dodgeImg = Image.new('L',(width,height))
        dodgePix = dodgeImg.load()

        for y in range(height):
            for x in range(width):

                base = basePix[x,y]
                mix = mixPix[x,y]

                tempPix = base+(base*mix)/(255-mix)

                dodgePix[x,y] = tempPix

        return dodgeImg

    def rightRadius(self):
        '''
        text box value judge  in range 1-10
        '''

        value = self.input.GetValue()
        if value > 10 or value < 1:
            return False
        return True



# Define File Drop Target class
class FileDropTarget(wx.FileDropTarget):
    """ This object implements Drop Target functionality for Files """
    def __init__(self, obj):
        """ Initialize the Drop Target, passing in the Object Reference to
          indicate what should receive the dropped files """
        # Initialize the wxFileDropTarget Object
        wx.FileDropTarget.__init__(self)
        # Store the Object Reference for dropped files
        self.obj = obj

    def OnDropFiles(self, x, y, filenames):
        """ Implement File Drop """
        print filenames[0]
        frame.OnImage(filenames[0])



app = wx.App(False)
frame = MainWindow(None, 'Drop && Drag')
app.MainLoop()