import wx
import config
import os
import subprocess
import threading
import time
import textwrap


# define all notification methods a user is allowed to choose from here:
SUPPORTED_METHODS = "toaster,simple,generic,gtknotify,knotify,growlnotify,xosd"

def getSupportedNotificationMethods():
    return SUPPORTED_METHODS.split(",")

# notification_method = gtknotify
#
# should be available when GTK+ is installed
def notificationWindow_gtknotify(mw, name, text, buddy, color=""):
    import pynotify
    import cgi
    if not pynotify.is_initted():
        if not pynotify.init('torchat'):
            raise Exception('gtknotify not supported')
    pynotify.Notification(
        cgi.escape(name).encode('ascii', 'xmlcharrefreplace'), 
        cgi.escape(text).encode('ascii', 'xmlcharrefreplace')
    ).show()


# notification_method = knotify
#
# works with KDE4 (maybe somebody could tell me
# how to make this work with KDE3 also)
def notificationWindow_knotify(mw, name, text, buddy, color=""):
    import dbus
    knotify = dbus.SessionBus().get_object("org.kde.knotify", "/Notify")
    knotify.event('warning', 'kde', [], name, text,
            [], [], 0, 0, dbus_interface='org.kde.KNotify')


# notification_method = growlnotify
#
# this is meant for Mac OS X where growl is used by many
# other apps. You need to have growl and growlnotify
def notificationWindow_growlnotify(mw, name, text, buddy, color=""):
    # This seems to fail about half the time
    # iconpath = os.path.join(config.ICON_DIR, "torchat.png")
    #args = ['growlnotify', '-m', text, '--image', iconpath]
    text = "%s\n\n%s" % (name, text)
    args = ['growlnotify', '-m', text]
    subprocess.Popen(args).communicate()


# notification_method = xosd
#
# this needs python-osd installed on the system
# and works only on the X Window System
def notificationWindow_xosd(mw, name, text, buddy, color=""):
    NotificationWindowXosd(mw, name, text, buddy, color).start()

class NotificationWindowXosd(threading.Thread):
    def __init__(self, mw, name, text, buddy, color=""):
        threading.Thread.__init__(self)
        self.name = name.encode("utf-8")
        self.text = text.encode("utf-8")
        
    def run(self):    
        import pyosd
        text = "%s\n%s" % (self.name, self.text)
        text_lines = textwrap.fill(text, 40).split(os.linesep)
        osd = pyosd.osd(lines=len(text_lines), shadow=2, colour="#FFFF00")
        line_number = 0
        for text_line in text_lines:
            osd.display(text_line, line=line_number)
            line_number += 1
        time.sleep(3)

# notification_method = simple
#
# no animations
def notificationWindow_simple(mw, name, text, buddy, color=""):
    NotificationWindowSimple(mw, name, text, buddy, color)

class NotificationWindowSimple(wx.Frame):
    def __init__(self, mw, name, text, buddy, color=""):
        wx.Frame.__init__(self, mw,
            style=wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.STAY_ON_TOP)
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK))
        sizer = wx.BoxSizer()
        self.panel.SetSizer(sizer)

        if buddy.profile_avatar_object <> None:
            bitmap = buddy.profile_avatar_object
        else:
            bitmap = wx.Bitmap(os.path.join(config.ICON_DIR, "torchat.png"), wx.BITMAP_TYPE_PNG)
        static_image = wx.StaticBitmap(self.panel, -1, bitmap)
        sizer.Add(static_image, 0, wx.ALL, 5 )

        self.label = wx.StaticText(self.panel)
        self.label.SetLabel("%s\n\n%s" % (name, text))
        sizer.Add(self.label, 0, wx.ALL, 5 )

        wsizer = wx.BoxSizer()
        wsizer.Add(self.panel, 0, wx.ALL, 0)
        self.SetSizerAndFit(wsizer)
        self.Layout()

        # Position the window
        cx, cy, maxx, maxy = wx.ClientDisplayRect()
        self.w, self.h = self.GetSize()
        self.x = maxx - self.w - 20
        self.y = maxy - self.h - 20
        self.SetPosition((self.x, self.y))
        
        # the following will prevent the focus 
        # stealing on windows
        self.Disable()
        self.Show()
        self.Enable()

        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.onTimer)

        # start animation
        self.timer.Start(5000, True)


    def onTimer(self, evt):
        # Just hide the window
        self.Hide()
        self.Destroy()
        
    def onMouse(self, evt):
        # restart the timer to immediately end the waiting
        self.timer.Start(5000, True)



# notification_method = generic
#
# this is the default and works everywhere
def notificationWindow_generic(mw, name, text, buddy, color=""):
    NotificationWindowGeneric(mw, name, text, buddy, color)

class NotificationWindowGeneric(wx.Frame):
    def __init__(self, mw, name, text, buddy, color=""):
        wx.Frame.__init__(self, mw,
            style=wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.STAY_ON_TOP)
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK))
        sizer = wx.BoxSizer()
        self.panel.SetSizer(sizer)

        if buddy.profile_avatar_object <> None:
            bitmap = buddy.profile_avatar_object
        else:
            bitmap = wx.Bitmap(os.path.join(config.ICON_DIR, "torchat.png"), wx.BITMAP_TYPE_PNG)
        static_image = wx.StaticBitmap(self.panel, -1, bitmap)
        sizer.Add(static_image, 0, wx.ALL, 5 )

        self.label = wx.StaticText(self.panel)
        self.label.SetLabel("%s\n\n%s" % (name, text))
        sizer.Add(self.label, 0, wx.ALL, 5 )

        wsizer = wx.BoxSizer()
        wsizer.Add(self.panel, 0, wx.ALL, 0)
        self.SetSizerAndFit(wsizer)
        self.Layout()

        # initialize animation
        cx, cy, maxx, maxy = wx.ClientDisplayRect()
        self.w, self.h = self.GetSize()
        self.x_end = maxx - self.w - 20
        self.y_end = maxy - self.h - 20

        self.x_pos = -self.w
        self.y_pos = self.y_end
        self.phase = 0

        self.SetPosition((self.x_pos, self.y_pos))
        
        # the following will prevent the focus 
        # stealing on windows
        self.Disable()
        self.Show()
        self.Enable()

        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.onTimer)

        # start animation
        self.timer.Start(10, True)


    def onTimer(self, evt):
        if self.phase == 0:
            if self.x_pos < self.x_end:
                # move right and restart timer
                speed = ((self.x_end - self.x_pos) ^ 2) / 10
                self.x_pos += (1 + speed)
                self.SetPosition((self.x_pos, self.y_pos))
                self.timer.Start(10, True)
                return
            else:
                # we are at the right border.
                # now switch phase and wait a bit
                self.phase = 1
                self.timer.Start(3000, True)
                
                # and from now on we also close on mouse contact
                self.panel.Bind(wx.EVT_MOUSE_EVENTS, self.onMouse)
                return

        if self.phase == 1:
            if self.y_pos > -self.h:
                # move upwards and restart timer
                speed = ((self.y_end - self.y_pos) ^ 2) / 10
                self.y_pos -= (5 + speed)
                self.SetPosition((self.x_pos, self.y_pos))
                self.timer.Start(10, True)
                return
            else:
                # we reached the end of the animation
                self.Hide()
                self.Destroy()
        
    def onMouse(self, evt):
        # restart the timer to immediately end the waiting
        self.timer.Start(10, True)



# notification_method = online
notificationToasterPositions = []
notificationToasterWindows = {}
def notificationWindow_toaster(mw, name, text, buddy, color=""):
    NotificationWindowToaster(mw, name, text, buddy, color)

class NotificationWindowToaster(wx.Frame):
    def __init__(self, mw, name, text, buddy, color):
        wx.Frame.__init__(self, mw,
            style=wx.FRAME_NO_TASKBAR | wx.NO_BORDER | wx.STAY_ON_TOP)
        
        # Set the buddy
        self.buddy  = buddy
        message = "%s\n%s" % (name, text)
        
        # Get the window color
        if not len(color):
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK)
        
        # Recycle old window if we can
        if buddy.address in notificationToasterWindows:
            window = notificationToasterWindows[buddy.address]
            window.resetTimer()
            window.setMessage(message)
            window.setColor(color)
            self.Destroy()
            return
        
        # Layout
        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.panel.SetMinSize((250, 74))
        self.setColor(color)

        sizer = wx.BoxSizer()
        self.panel.SetSizer(sizer)
        
        if buddy.profile_avatar_object <> None:
            bitmap = buddy.profile_avatar_object
        else:
            bitmap = wx.Bitmap(os.path.join(config.ICON_DIR, "torchat.png"), wx.BITMAP_TYPE_PNG)
        static_image = wx.StaticBitmap(self.panel, -1, bitmap)
        sizer.Add(static_image, 0, wx.ALL, 5 )

        self.label = wx.StaticText(self.panel)
        self.setMessage(message)
        sizer.Add(self.label, 0, wx.ALL, 5 )

        wsizer = wx.BoxSizer()
        wsizer.Add(self.panel, 0, wx.ALL, 0)
        self.SetSizerAndFit(wsizer)
        self.Layout()
        
        # we don't need them to overlap
        self.locidx = self.findLocation()
        self.margin = 10
        

        # initialize animation
        self.cx, self.cy, self.tx, self.ty = wx.ClientDisplayRect()
        self.w, self.h = self.GetSize()
        
        self.offsety = self.locidx * self.h + self.locidx * self.margin
        
        self.x_pos = self.tx - self.w - 20
        self.y_pos = self.ty + self.h + 20
        self.y_max = self.ty - 85 - self.offsety
        self.y_end = self.y_pos
        self.phase = 0

        self.SetPosition((self.x_pos, self.y_pos))
        
        # the following will prevent the focus 
        # stealing on windows
        self.Disable()
        self.Show()
        self.Enable()

        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.onTimer)

        # start animation
        self.timer.Start(10, True)
        
        # we need this
        notificationToasterPositions.append(self.locidx)
        notificationToasterWindows[self.buddy.address] = self

    
    def setMessage(self, message):
        self.label.SetLabel(message)
        self.label.Wrap(176)
    
    def setColor(self, color):
        self.panel.SetBackgroundColour(color)
        
    def onTimer(self, evt):
        if self.phase == 0:
            if self.y_pos > self.y_max:
                # move up and restart timer
                speed = ((self.y_pos - self.y_max) ^ 2) / 10
                self.y_pos -= (1 + speed)
                self.SetPosition((self.x_pos, self.y_pos))
                self.timer.Start(10, True)
                return
            else:
                self.phase = 1
                self.timer.Start(3000, True)
                
                # and from now on we also close on mouse contact
                self.panel.Bind(wx.EVT_MOUSE_EVENTS, self.onMouse)
                return

        if self.phase == 1:
            if self.y_pos < self.y_end:
                # move down and restart timer
                speed = ((self.y_end - self.y_pos) ^ 2) / 10
                self.y_pos += (1 + speed)
                self.SetPosition((self.x_pos, self.y_pos))
                self.timer.Start(10, True)
                return
            else:
                # we reached the end of the animation
                self.close()
    
    def findLocation(self):
        locidx  = 0
        
        while locidx in notificationToasterPositions:
            locidx += 1
        
        return locidx
    
    def resetTimer(self):
        self.phase = 0
        self.timer.Start(10, True)
        
    def onMouse(self, evt):
        # restart the timer to immediately end the waiting
        self.timer.Start(10, True)
        
    def close(self):
        if notificationToasterWindows.has_key(self.buddy.address):
            notificationToasterWindows.pop(self.buddy.address)
        if self.locidx in notificationToasterPositions:
            notificationToasterPositions.remove(self.locidx)
        self.Hide()
        self.Destroy()


def notificationWindow(mw, name, text, buddy, color=""):
    method = config.get('gui', 'notification_method')
    try:
        function = globals()["notificationWindow_%s" % method]
    except:
        print "(1) notification method '%s' is not implemented, falling back to 'generic'." % method
        notificationWindow_generic(mw, name, text, buddy, color)
        return
    
    try:
        function(mw, name, text, buddy, color)
    except:
        print "(1) exception while using notification method '%s'" % method
        print "(1) falling back to 'generic'. Traceback follows:"
        config.tb()
        notificationWindow_generic(mw, name, text, buddy, color)


# vim: set tw=0 sts=4 sw=4 expandtab:
