# -*- coding: UTF-8 -*-

##############################################################################
#                                                                            #
# Copyright (c) 2007-2010 Bernd Kreuss <prof7bit@gmail.com>                  #
#                                                                            #
# This program is licensed under the GNU General Public License V3,          #
# the full source code is included in the binary distribution.               #
#                                                                            #
# Included in the distribution are files from other open source projects:    #
# - TOR Onion Router (c) The Tor Project, 3-clause-BSD                       #
# - SocksiPy (c) Dan Haim, BSD Style License                                 #
# - Gajim buddy status icons (c) The Gajim Team, GNU GPL                     #
#                                                                            #
##############################################################################

# this is a graphical User interface for the TorChat client library.

import config
import wx
import tc_client
import sys
import os
import re
import shutil
import time
import subprocess
import textwrap
import version
import dlg_settings
import translations
import tc_notification
import string
import math
from imaplib import Flags
from datetime import datetime
lang = translations.lang_en
tb = config.tb
tb1 = config.tb1

ICON_NAMES = {tc_client.STATUS_OFFLINE : "offline.png",
              tc_client.STATUS_ONLINE : "online.png",
              tc_client.STATUS_HANDSHAKE : "connecting.png",
              tc_client.STATUS_AWAY : "away.png",
              tc_client.STATUS_XA : "xa.png"}

_icon_images = {} #this is a cache for getStatusBitmap()

def getStatusBitmap(status):
    global _icon_images
    if not status in _icon_images:
        image = wx.Image(os.path.join(config.ICON_DIR, ICON_NAMES[status]), wx.BITMAP_TYPE_PNG)
        image.ConvertAlphaToMask()
        _icon_images[status] = image
    bitmap = _icon_images[status].ConvertToBitmap()
    return bitmap


class TaskbarIcon(wx.TaskBarIcon):
    def __init__(self, main_window):
        wx.TaskBarIcon.__init__(self)
        self.mw = main_window

        #load event icon
        img = wx.Image(os.path.join(config.ICON_DIR, "event.png"))
        img.ConvertAlphaToMask()
        self.event_icon = wx.IconFromBitmap(img.ConvertToBitmap())
        self.showStatus(self.mw.buddy_list.own_status)
        self.timer = wx.Timer(self, -1)
        self.blink_phase = False
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.onLeftClick)
        self.Bind(wx.EVT_TIMER, self.onTimer)

    def showEvent(self):
        self.SetIcon(self.event_icon, self.getToolTipText())

    def showStatus(self, status):
        icon = wx.IconFromBitmap(getStatusBitmap(status))
        self.SetIcon(icon, self.getToolTipText())

    def onLeftClick(self, evt):
        self.mw.Show(not self.mw.IsShown())
        if self.mw.IsShown():
            self.mw.Iconize(False) # never show it minimized (can happen on KDE)

            #bring it to the front
            self.mw.SetFocus()
            self.mw.SetWindowStyle(self.mw.GetWindowStyle() | wx.STAY_ON_TOP)
            self.mw.SetWindowStyle(self.mw.GetWindowStyle() & ~wx.STAY_ON_TOP)

    def CreatePopupMenu(self):
        return TaskbarMenu(self.mw)

    def getToolTipText(self):
        text = "TorChat: %s" % config.getProfileShortName()
        for window in self.mw.chat_windows:
            if not window.IsShown():
                text += os.linesep + window.getTitleShort()
        return text

    def blink(self, start=True):
        if start:
            self.timer.Start(500, False)
        else:
            self.timer.Stop()
            self.showStatus(self.mw.buddy_list.own_status)

    def onTimer(self, evt):
        self.blink_phase = not self.blink_phase
        if self.blink_phase:
            self.showStatus(self.mw.buddy_list.own_status)
        else:
            self.showEvent()

        #stop blinking, if there are no more hidden windows
        found = False
        for window in self.mw.chat_windows:
            if not window.IsShown():
                found = True
                break

        if not found:
            self.blink(False)


class TaskbarMenu(wx.Menu):
    def __init__(self, main_window):
        wx.Menu.__init__(self)
        self.mw = main_window
        self.mw.taskbar_icon.blink(False)

        # show/hide

        item = wx.MenuItem(self, wx.NewId(), lang.MTB_SHOW_HIDE_TORCHAT)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onShowHide, item)

        self.AppendSeparator()

        # (hidden) chat windows

        cnt = 0
        self.wnd = {}
        for window in self.mw.chat_windows:
            if not window.IsShown():
                id = wx.NewId()
                self.wnd[id] = window
                item = wx.MenuItem(self, id, window.getTitleShort())
                item.SetBitmap(getStatusBitmap(window.buddy.status))
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.onChatWindow, item)
                cnt += 1

        if cnt:
            self.AppendSeparator()

        # edit profile

        item = wx.MenuItem(self, wx.NewId(), lang.MPOP_EDIT_MY_PROFILE)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onProfile, item)

        # status

        item = wx.MenuItem(self, wx.NewId(), lang.ST_AVAILABLE)
        item.SetBitmap(getStatusBitmap(tc_client.STATUS_ONLINE))
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onAvailable, item)

        item = wx.MenuItem(self, wx.NewId(), lang.ST_AWAY)
        item.SetBitmap(getStatusBitmap(tc_client.STATUS_AWAY))
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onAway, item)

        item = wx.MenuItem(self, wx.NewId(), lang.ST_EXTENDED_AWAY)
        item.SetBitmap(getStatusBitmap(tc_client.STATUS_XA))
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onXA, item)

        self.AppendSeparator()

        # quit

        item = wx.MenuItem(self, wx.NewId(), lang.MTB_QUIT)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onExit, item)

    def onShowHide(self, evt):
        self.mw.taskbar_icon.onLeftClick(evt)

    def onChatWindow(self, evt):
        self.wnd[evt.GetId()].Show()
        #force update of the tooltip text (window list)
        self.mw.taskbar_icon.showStatus(self.mw.buddy_list.own_status)

    def onExit(self, evt):
        self.mw.exitProgram()

    def onAvailable(self, evt):
        self.mw.status_switch.setStatus(tc_client.STATUS_ONLINE)

    def onAway(self, evt):
        self.mw.status_switch.setStatus(tc_client.STATUS_AWAY)

    def onXA(self, evt):
        self.mw.status_switch.setStatus(tc_client.STATUS_XA)

    def onProfile(self, evt):
        dialog = DlgEditProfile(self.mw, self.mw)
        dialog.ShowModal()


class PopupMenu(wx.Menu):
    def __init__(self, main_window, type):
        wx.Menu.__init__(self)
        self.mw = main_window

        # options for buddy

        if type == "contact":
            self.buddy = self.mw.gui_bl.getSelectedBuddy()
            item = wx.MenuItem(self, wx.NewId(), lang.MPOP_CHAT)
            self.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.mw.gui_bl.onDClick, item)

            item = wx.MenuItem(self, wx.NewId(), lang.MPOP_SEND_FILE)
            self.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.onSendFile, item)

            if self.buddy.getOfflineMessages():
                item = wx.MenuItem(self, wx.NewId(), lang.MPOP_SHOW_OFFLINE_MESSAGES)
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.onShowOffline, item)

                item = wx.MenuItem(self, wx.NewId(), lang.MPOP_CLEAR_OFFLINE_MESSAGES)
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.onClearOffline, item)
            
            item = wx.MenuItem(self, wx.NewId(), lang.MPOP_COPY_ID_TO_CLIPBOARD)
            self.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.onCopyIdToClipboard, item)

            self.AppendSeparator()

            if not self.isCurrentBuddyLoggingActivated():
                item = wx.MenuItem(self, wx.NewId(), lang.MPOP_ACTIVATE_LOG)
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.onActivateLog, item)

                if self.hasOldLog():
                    item = wx.MenuItem(self, wx.NewId(), lang.MPOP_DELETE_EXISTING_LOG)
                    self.AppendItem(item)
                    self.Bind(wx.EVT_MENU, self.onDeleteLog, item)

            else:
                item = wx.MenuItem(self, wx.NewId(), lang.MPOP_STOP_LOG)
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.onStopLog, item)

                item = wx.MenuItem(self, wx.NewId(), lang.MPOP_DELETE_AND_STOP_LOG)
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.onDeleteLog, item)

            self.AppendSeparator()

            item = wx.MenuItem(self, wx.NewId(), lang.MPOP_EDIT_CONTACT)
            self.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.onEdit, item)

            item = wx.MenuItem(self, wx.NewId(), lang.MPOP_DELETE_CONTACT)
            self.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.onDelete, item)

            self.AppendSeparator()

        item = wx.MenuItem(self, wx.NewId(), lang.MPOP_ADD_CONTACT)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onAdd, item)

        #ask support

        item = wx.MenuItem(self, wx.NewId(), lang.MPOP_ASK_AUTHOR % config.get("branding", "support_name"))
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onAskAuthor, item)

        item = wx.MenuItem(self, wx.NewId(), lang.MPOP_EDIT_MY_PROFILE)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onProfile, item)

        self.AppendSeparator()
        
        #change identity
        
        item = wx.MenuItem(self, wx.NewId(), lang.DEC_NEW_IDENTITIY)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onNewIdentity, item)

        #settings

        item = wx.MenuItem(self, wx.NewId(), lang.MPOP_SETTINGS)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onSettings, item)

        #about

        item = wx.MenuItem(self, wx.NewId(), lang.MPOP_ABOUT)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onAbout, item)


        #exit program

        self.AppendSeparator()
        item = wx.MenuItem(self, wx.NewId(), lang.MTB_QUIT)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onQuit, item)

    def onSendFile(self, evt):
        title = lang.DFT_FILE_OPEN_TITLE % self.buddy.getAddressAndDisplayName()
        dialog = wx.FileDialog(self.mw, title, style=wx.OPEN)
        dialog.SetDirectory(config.getHomeDir())
        if dialog.ShowModal() == wx.ID_OK:
            file_name = dialog.GetPath()
            FileTransferWindow(self.mw, self.buddy, file_name)

    def onEdit(self, evt):
        dialog = DlgEditContact(self.mw, self.mw, self.buddy)
        dialog.ShowModal()

    def onDelete(self, evt):
        answer = wx.MessageBox(lang.D_CONFIRM_DELETE_MESSAGE % (self.buddy.address, self.buddy.name),
                               lang.D_CONFIRM_DELETE_TITLE,
                               wx.YES_NO|wx.NO_DEFAULT)
        if answer == wx.YES:
            #remove from list without disconnecting
            #this will send a remove_me message
            #the other buddy will then disconnect,
            #because there is not much it can do with the
            #connections anymore.
            self.mw.buddy_list.removeBuddy(self.buddy, disconnect=False)

    def onShowOffline(self, evt):
        om = self.buddy.getOfflineMessages()
        if om:
            om = lang.MSG_OFFLINE_QUEUED % (self.buddy.address, om)
        else:
            om = lang.MSG_OFFLINE_EMPTY % self.buddy.address
        wx.MessageBox(om, lang.MSG_OFFLINE_TITLE, wx.ICON_INFORMATION)
    
    def onCopyIdToClipboard(self, evt):
        if not wx.TheClipboard.IsOpened():
            address = wx.TextDataObject(self.buddy.address)
            wx.TheClipboard.Open()
            wx.TheClipboard.SetData(address)
            wx.TheClipboard.Close()

    def onClearOffline(self, evt):
        try:
            tc_client.wipeFile(self.buddy.getOfflineFileName())
        except:
            pass

    def getChatWindow(self):
        # this is called by the on*Log() functions,
        # because all logging is done by the chat windows,
        # logging does not belong to the functionality
        # of the Buddy in tc_client.py
        for window in self.mw.chat_windows:
            if window.buddy.address == self.buddy.address:
                print "found"
                return window

        #must open a hidden window
        return ChatWindow(self.mw, self.buddy, "", True)

    def isCurrentBuddyLoggingActivated(self):
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        return os.path.exists(os.path.join(path, '%s.log' % self.buddy.address))

    def hasOldLog(self):
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        return os.path.exists(os.path.join(path, 'disabled_%s.log' % self.buddy.address))

    def onActivateLog(self, evt):
        self.getChatWindow().onActivateLog(evt)

    def onStopLog(self, evt):
        self.getChatWindow().onStopLog(evt)

    def onDeleteLog(self, evt):
        self.getChatWindow().onDeleteLog(evt)

    def onAdd(self, evt):
        dialog = DlgEditContact(self.mw, self.mw)
        dialog.ShowModal()

    def onProfile(self, evt):
        dialog = DlgEditProfile(self.mw, self.mw)
        dialog.ShowModal()

    def onSettings(self, evt):
        dialog = dlg_settings.Dialog(self.mw)
        dialog.ShowModal()
    
    def onNewIdentity(self, evt):
        if not self.mw.buddy_list.changeTorIdentity():
            wx.MessageBox(lang.D_WARN_CONTROL_CONNECTION_FAILED_MESSAGE, lang.D_WARN_CONTROL_CONNECTION_FAILED_TITLE)

    def onAbout(self, evt):
        wx.MessageBox(lang.ABOUT_TEXT % {"version":version.VERSION,
                                         "svn":version.VERSION_SVN,
                                         "copyright":config.COPYRIGHT,
                                         "python":".".join(str(x) for x in sys.version_info),
                                         "wx":wx.version(),
                                         "translators":config.getTranslators()},
                      lang.ABOUT_TITLE)

    def onAskAuthor(self, evt):
        if self.mw.buddy_list.getBuddyFromAddress(config.get("branding", "support_id")):
            wx.MessageBox(lang.DEC_MSG_ALREADY_ON_LIST % config.get("branding", "support_name"))
        else:
            dialog = DlgEditContact(self.mw, self.mw, add_author=True)
            dialog.ShowModal()

    def onQuit(self, evt):
        self.mw.exitProgram()


class DlgEditContact(wx.Dialog):
    def __init__(self, parent, main_window, buddy=None, add_author=False): #no buddy -> Add new
        wx.Dialog.__init__(self, parent, -1)
        self.mw = main_window
        self.bl = self.mw.buddy_list
        self.buddy = buddy
        if buddy is None:
            self.SetTitle(lang.DEC_TITLE_ADD)
            address = ""
            name = ""
        else:
            self.SetTitle(lang.DEC_TITLE_EDIT)
            address = buddy.address
            name = buddy.name

        self.panel = wx.Panel(self)

        #setup the sizers
        sizer = wx.GridBagSizer(vgap = 5, hgap = 5)
        box_sizer = wx.BoxSizer()
        box_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 5)

        #address
        row = 0
        lbl = wx.StaticText(self.panel, -1, lang.DEC_TORCHAT_ID)
        sizer.Add(lbl, (row, 0))

        self.txt_address = wx.TextCtrl(self.panel, -1, address)
        self.txt_address.SetMinSize((250, -1))
        sizer.Add(self.txt_address, (row, 1), (1, 2))

        #name
        row += 1
        lbl = wx.StaticText(self.panel, -1, lang.DEC_DISPLAY_NAME)
        sizer.Add(lbl, (row, 0))

        self.txt_name = wx.TextCtrl(self.panel, -1, name)
        self.txt_name.SetMinSize((250, -1))
        sizer.Add(self.txt_name, (row, 1), (1, 2))

        #add-me message (new buddies)
        if not self.buddy:
            row += 1
            lbl = wx.StaticText(self.panel, -1, lang.DEC_INTRODUCTION)
            sizer.Add(lbl, (row, 0))

            self.txt_intro = wx.TextCtrl(self.panel, -1, "hello, my friend...")
            self.txt_intro.SetMinSize((250, -1))
            sizer.Add(self.txt_intro, (row, 1), (1, 2))

        if add_author:
            self.txt_address.SetValue(config.get("branding", "support_id"))
            self.txt_name.SetValue(config.get("branding", "support_name"))

        #buttons
        row += 1
        self.btn_cancel = wx.Button(self.panel, wx.ID_CANCEL, lang.BTN_CANCEL)
        sizer.Add(self.btn_cancel, (row, 1), flag=wx.EXPAND)

        self.btn_ok = wx.Button(self.panel, wx.ID_OK, lang.BTN_OK)
        self.btn_ok.SetDefault()
        sizer.Add(self.btn_ok, (row, 2), flag=wx.EXPAND)

        #fit the sizers
        self.panel.SetSizer(box_sizer)
        box_sizer.Fit(self)

        #bind the events
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.onCancel)
        self.btn_ok.Bind(wx.EVT_BUTTON, self.onOk)

    def onOk(self, evt):
        address = self.txt_address.GetValue().rstrip().lstrip()
        if len(address) != 16:
            l = len(address)
            wx.MessageBox(lang.DEC_MSG_16_CHARACTERS % l)
            return

        for c in address:
            if c not in "234567abcdefghijklmnopqrstuvwxyz":
                wx.MessageBox(lang.DEC_MSG_ONLY_ALPANUM)
                return

        if self.buddy is None:
            buddy = tc_client.Buddy(address,
                          self.bl,
                          self.txt_name.GetValue())
            res = self.bl.addBuddy(buddy)
            if res == False:
                wx.MessageBox(lang.DEC_MSG_ALREADY_ON_LIST % address)
            else:
                if self.txt_intro.GetValue() <> "":
                    buddy.storeOfflineChatMessage(self.txt_intro.GetValue())
        else:
            address_old = self.buddy.address
            offline_file_name_old = self.buddy.getOfflineFileName()
            self.buddy.address = address
            offline_file_name_new = self.buddy.getOfflineFileName()
            self.buddy.name = self.txt_name.GetValue()
            self.bl.save()
            if address != address_old:
                self.buddy.disconnect()
                try:
                    os.rename(offline_file_name_old, offline_file_name_new)
                except:
                    pass

        self.Close()

    def onCancel(self,evt):
        self.Close()


class DlgEditProfile(wx.Dialog):
    def __init__(self, parent, main_window):
        wx.Dialog.__init__(self, parent, -1, title=lang.DEP_TITLE)
        self.mw = main_window
        self.panel = wx.Panel(self)
        self.remove_avatar_on_ok = False

        #setup the sizers
        sizer = wx.GridBagSizer(vgap = 5, hgap = 5)
        avatar_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.BoxSizer()
        box_sizer.Add(avatar_sizer, 0, wx.EXPAND | wx.ALL, 5)
        box_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        #avatar
        self.avatar = wx.StaticBitmap(self.panel, -1, self.getAvatarBitmap())
        avatar_sizer.Add(self.avatar, 0, wx.EXPAND | wx.ALL, 2)
        
        #avatar buttons
        self.btn_set_avatar = wx.Button(self.panel, -1, lang.DEP_SET_AVATAR)
        avatar_sizer.Add(self.btn_set_avatar, 0, wx.EXPAND | wx.ALL, 2)
        self.btn_remove_avatar = wx.Button(self.panel, -1, lang.DEP_REMOVE_AVATAR)
        avatar_sizer.Add(self.btn_remove_avatar, 0, wx.EXPAND | wx.ALL, 2)

        if not self.mw.buddy_list.own_avatar_data:
            self.btn_remove_avatar.Disable()
            
        #name
        row = 0
        lbl = wx.StaticText(self.panel, -1, lang.DEP_NAME)
        sizer.Add(lbl, (row, 0))

        self.txt_name = wx.TextCtrl(self.panel, -1,
            config.get("profile", "name"))
        self.txt_name.SetMinSize((250, -1))
        sizer.Add(self.txt_name, (row, 1), (1, 2))

        #text
        row += 1
        lbl = wx.StaticText(self.panel, -1, lang.DEP_TEXT)
        sizer.Add(lbl, (row, 0))

        self.txt_text = wx.TextCtrl(self.panel, -1,
            config.get("profile", "text"),
            style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
        self.txt_text.SetMinSize((250, 70))
        sizer.Add(self.txt_text, (row, 1), (1, 2))

        #buttons
        row += 1
        self.btn_cancel = wx.Button(self.panel, wx.ID_CANCEL, lang.BTN_CANCEL)
        sizer.Add(self.btn_cancel, (row, 1), flag=wx.EXPAND)

        self.btn_ok = wx.Button(self.panel, wx.ID_OK, lang.BTN_OK)
        self.btn_ok.SetDefault()
        sizer.Add(self.btn_ok, (row, 2), flag=wx.EXPAND)

        #fit the sizers
        self.panel.SetSizer(box_sizer)
        box_sizer.Fit(self)

        #bind the events
        self.btn_set_avatar.Bind(wx.EVT_BUTTON, self.onAvatar)
        self.btn_remove_avatar.Bind(wx.EVT_BUTTON, self.onAvatarRemove)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.onCancel)
        self.btn_ok.Bind(wx.EVT_BUTTON, self.onOk)
        self.txt_text.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
        self.avatar.Bind(wx.EVT_LEFT_UP, self.onAvatar)

        self.txt_text.SetFocus()

        self.avatar.SetDropTarget(AvatarDropTarget(self))
        self.txt_name.SetDropTarget(AvatarDropTarget(self))
        self.txt_text.SetDropTarget(AvatarDropTarget(self))

        # position the dialog near the mouse
        # (yes, I am paying attention to details)
        w,h = self.GetSize()
        sx, sy, sx1, sy1 = wx.ClientDisplayRect()
        (x,y) = wx.GetMousePosition()
        x = x - w/2
        y = y - h/2
        if x < sx:
            x = sx
        if y < sy:
            y = sy
        if x > sx1 - w:
            x = sx1 - w
        if y > sy1 - h:
            y = sy1 - h
        self.SetPosition((x,y))

    def getAvatarBitmap(self, file_name=None):
        if file_name:
            image = wx.Image(file_name, wx.BITMAP_TYPE_PNG)
            # CROP IMAGE
            width   = image.GetWidth()
            height  = image.GetHeight()
            if height == width:
                cropped = image
            else:
                if height > width:
                    cropped = image.GetSubImage(wx.Rect(0, height/2-width/2, width, width))
                else:
                    cropped = image.GetSubImage(wx.Rect(width/2-height/2, 0, height, height))
            cropped.Rescale(64, 64, wx.IMAGE_QUALITY_HIGH)
            return wx.BitmapFromImage(cropped)
        else:
            if self.mw.buddy_list.own_avatar_data:
                image = wx.ImageFromData(64, 64, self.mw.buddy_list.own_avatar_data)
                if self.mw.buddy_list.own_avatar_data_alpha:
                    image.SetAlphaData(self.mw.buddy_list.own_avatar_data_alpha)
                return wx.BitmapFromImage(image)
            else:
                return wx.Bitmap(os.path.join(config.ICON_DIR, "torchat.png"), wx.BITMAP_TYPE_PNG)

    def onAvatarSelected(self, file_name):
        self.remove_avatar_on_ok = False
        avatar_old = os.path.join(config.getDataDir(), "avatar.png")
        avatar_new = os.path.join(config.getDataDir(), "avatar_new.png")
        if file_name == avatar_old or file_name == avatar_new:
            wx.MessageBox(lang.DEP_WARN_IS_ALREADY, lang.DEP_WARN_TITLE)
        else:
            # onOk() will find the file avatar_new.png and know what to do
            shutil.copy(file_name, avatar_new)
            # set the new bitmap (in this dialog only)
            self.avatar.SetBitmap(self.getAvatarBitmap(avatar_new))
            self.btn_remove_avatar.Enable()
            self.panel.Layout()
            self.panel.Refresh()

    def onAvatarRemove(self, evt):
        self.avatar.SetBitmap(wx.Bitmap(os.path.join(config.ICON_DIR, "torchat.png"), wx.BITMAP_TYPE_PNG))
        self.panel.Layout()
        self.panel.Refresh()
        self.remove_avatar_on_ok = True
        self.btn_remove_avatar.Disable()
        
    def onAvatar(self, evt):
        title = lang.DEP_AVATAR_SELECT_PNG
        dialog = wx.FileDialog(self, title, style=wx.OPEN)
        dialog.SetWildcard("%s (*.png)|*.png|%s (*.*)|*.*" % (lang.DEP_PNG_FILES, lang.DEP_ALL_FILES))
        dialog.SetDirectory(config.getHomeDir())
        if dialog.ShowModal() == wx.ID_OK:
            self.onAvatarSelected(dialog.GetPath())
        pass

    def onEnter(self, evt):
        self.onOk(evt)

    def onCancel(self, evt):
        avatar_new = os.path.join(config.getDataDir(), "avatar_new.png")
        if os.path.exists(avatar_new):
            tc_client.wipeFile(avatar_new)

        self.Close()

    def onOk(self, evt):
        config.set("profile", "name", self.txt_name.GetValue())
        config.set("profile", "text", self.txt_text.GetValue())

        # replace the avatar if a new one has been selected
        # or remove it and send an empty avatar if it has been removed
        avatar_old = os.path.join(config.getDataDir(), "avatar.png")
        avatar_new = os.path.join(config.getDataDir(), "avatar_new.png")
        
        if self.remove_avatar_on_ok:
            tc_client.wipeFile(avatar_old)
            tc_client.wipeFile(avatar_new)
            self.mw.buddy_list.own_avatar_data = ""
            self.mw.buddy_list.own_avatar_data_alpha = ""
            for buddy in self.mw.buddy_list.list:
                buddy.sendAvatar(True)
        else:
            if os.path.exists(avatar_new):
                shutil.copy(avatar_new, avatar_old)
                tc_client.wipeFile(avatar_new)
                self.mw.gui_bl.loadOwnAvatarData() # this will also send it

        for buddy in self.mw.buddy_list.list:
            buddy.sendProfile()
            buddy.sendStatus()
        
        self.mw.onProfileUpdated()
        
        self.Close()


class BuddyList(wx.ListCtrl):
    def __init__(self, parent, main_window):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.LC_NO_HEADER)
        self.mw = main_window
        self.bl = self.mw.buddy_list

        self.InsertColumn(0, "buddy")

        self.r_down = False
        self.last_mouse_time = time.time()
        self.tool_tip = None
        self.tool_tip_index = -1
        self.has_mouse = False

        self.il = wx.ImageList(16, 16)
        self.il_idx = {}
        for status in [tc_client.STATUS_OFFLINE,
                       tc_client.STATUS_HANDSHAKE,
                       tc_client.STATUS_ONLINE,
                       tc_client.STATUS_AWAY,
                       tc_client.STATUS_XA]:
            self.il_idx[status] = self.il.Add(getStatusBitmap(status))

        img_event = wx.Image(os.path.join(config.ICON_DIR, "event.png"))
        img_event.ConvertAlphaToMask()
        self.il_idx[100] = self.il.Add(img_event.ConvertToBitmap())

        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.blink_phase = False

        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.old_sum = ""
        self.timer.Start(milliseconds=500, oneShot=False)

        self.Bind(wx.EVT_LEFT_DCLICK, self.onDClick)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onRClick)
        self.Bind(wx.EVT_RIGHT_DOWN, self.onRDown)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.onMouse)
        self.Bind(wx.EVT_ENTER_WINDOW, self.onMouseEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.onMouseLeave)

        self.SetDropTarget(DropTarget(self.mw, None))

        if config.getint("gui", "color_text_use_system_colors") == 0:
            self.SetBackgroundColour(config.get("gui", "color_text_back"))
            self.SetForegroundColour(config.get("gui", "color_text_fore"))

        self.onListChanged()
        
        self.loadOwnAvatarData()

    def loadOwnAvatarData(self):
        file_name = os.path.join(config.getDataDir(), "avatar.png")
        if os.path.exists(file_name):
            print "(2) reading own avatar file %s" % file_name
            image = wx.Image(file_name, wx.BITMAP_TYPE_PNG)
            width   = image.GetWidth()
            height  = image.GetHeight()
            if height == width:
                cropped = image
            else:
                if height > width:
                    cropped = image.GetSubImage(wx.Rect(0, height/2-width/2, width, width))
                else:
                    cropped = image.GetSubImage(wx.Rect(width/2-height/2, 0, height, height))
            cropped.Rescale(64, 64, wx.IMAGE_QUALITY_HIGH)
            self.bl.own_avatar_data = cropped.GetData()
            print "(2) uncompressed image data: %i bytes" % len(self.bl.own_avatar_data)
            if cropped.HasAlpha():
                self.bl.own_avatar_data_alpha = cropped.GetAlphaData()
                print "(2) uncompressed aplha data: %i bytes" % len(self.bl.own_avatar_data_alpha)
            else:
                self.bl.own_avatar_data_alpha = ""
            for buddy in self.bl.list:
                buddy.sendAvatar()
    
    def sortListByStatus(self, value1, value2):
        try:
            buddy1 = self.bl.list[value1]
            buddy2 = self.bl.list[value2]
            
            i1 = int(buddy1.getStatusOrder())
            i2 = int(buddy2.getStatusOrder())
            n1 = str(buddy1.getDisplayName().lower())
            n2 = str(buddy2.getDisplayName().lower())
        except ValueError:
            return cmp(value1, value1)
        else:
            return cmp((i1, n1), (i2, n2))
        
    def setStatusIcon(self, index, image_idx):
        # we also store the image index in the ItemData because
        # we can then avoid setting it twice and avoid flickering
        key = self.GetItemData(index)
        old_image_idx = self.bl.list[key].image_idx;
        #old = self.GetItemData(index)
        #if image_idx <> old:
        if old_image_idx <> image_idx:
            self.SetItemImage(index, image_idx)
            self.bl.list[key].image_idx = image_idx
            #self.SetItemData(index, image_idx)

    def blinkBuddy(self, buddy, blink=True):
        name = buddy.getDisplayName()
        for index in xrange(0, self.GetItemCount()):
            if self.getBuddyFromIndex(index) == buddy:
                if blink:
                    self.setStatusIcon(index, self.il_idx[100])
                    '''if self.blink_phase:
                        self.setStatusIcon(index, self.il_idx[100])
                    else:
                        self.setStatusIcon(index, self.il_idx[buddy.status])'''
                else:
                    self.setStatusIcon(index, self.il_idx[buddy.status])

    def onTimer(self, evt):
        self.blink_phase = not self.blink_phase
        # blink all buddies with hidden chat windows
        for window in self.mw.chat_windows:
            if not window.IsShown():
                self.blinkBuddy(window.buddy, True)
            else:
                self.blinkBuddy(window.buddy, False)

        # tooltips:
        if self.has_mouse and self.mw.IsActive():
            if time.time() - self.last_mouse_time > 0.5:
                index, flags = self.HitTest(self.ScreenToClient(wx.GetMousePosition()))
                if index == -1:
                    # not over any item (anymore)
                    self.closeToolTip()

                else:
                    # hovering over item
                    if self.tool_tip is None:
                        self.openToolTip(index)
        else:
            self.closeToolTip()

    def closeToolTip(self):
        if self.tool_tip <> None:
            self.tool_tip.Hide()
            self.tool_tip.Destroy()
            self.tool_tip = None
            self.tool_tip_index = -1

    def openToolTip(self, index):
        self.closeToolTip()
        self.tool_tip = BuddyToolTip(self, index)
        self.tool_tip_index = index

        #TODO: wx.PopupWindow stealing focus under wine
        #find a better way to prevent this
        wx.CallAfter(self.mw.SetFocus)

    def onDClick(self, evt):
        index = self.GetFirstSelected()
        if index <> -1:
            buddy = self.getBuddyFromIndex(index)
            found_window = False
            for window in self.mw.chat_windows:
                if window.buddy.address == buddy.address:
                    found_window = True
                    break
                
            if not found_window:
                window = ChatWindow(self.mw, buddy)
            
            if not window.IsShown():
                window.Show()
            
            window.txt_out.SetFocus()

        evt.Skip()

    def onRClick(self, evt):
        index, flags = self.HitTest(evt.GetPosition())
        if index != -1:
            self.onMouseLeave(evt)
            self.mw.PopupMenu(PopupMenu(self.mw, "contact"))

    def onRDown(self, evt):
        index, flags = self.HitTest(evt.GetPosition())
        if index == -1:
            self.onMouseLeave(evt)
            self.mw.PopupMenu(PopupMenu(self.mw, "empty"))
        else:
            evt.Skip()

    def getSelectedBuddy(self):
        index = self.GetFirstSelected()
        return self.getBuddyFromIndex(index)
        '''addr = self.GetItemText(index)[0:16]
        return self.bl.getBuddyFromAddress(addr)'''

    def getBuddyFromXY(self, position):
        index, flags = self.HitTest(position)
        if index != -1:
            return self.getBuddyFromIndex(index)
            '''addr = self.GetItemText(index)[0:16]
            return self.bl.getBuddyFromAddress(addr)'''
        else:
            return None

    def onBuddyStatusChanged(self, buddy):
        assert isinstance(buddy, tc_client.Buddy)
        index = self.getIndexFromBuddy(buddy)
        self.SetItemImage(index, self.il_idx[buddy.status])
        # Lets sort by status
        self.SortItems(self.sortListByStatus)
        #notify the chat window
        for window in self.mw.chat_windows:
            if window.buddy.address == buddy.address:
                window.onBuddyStatusChanged()
                break

        # if a tooltip for this buddy is currently shown then refresh it
        if self.tool_tip <> None and index == self.tool_tip_index:
            self.openToolTip(index)

    def onBuddyProfileChanged(self, buddy):
        assert isinstance(buddy, tc_client.Buddy)

        #notify the chat window
        for window in self.mw.chat_windows:
            if window.buddy.address == buddy.address:
                window.onBuddyProfileChanged(buddy)
                break

        # if a tooltip for this buddy is currently shown then refresh it
        index = self.getIndexFromBuddy(buddy)
        if self.tool_tip <> None and index == self.tool_tip_index:
            self.openToolTip(index)

    def onBuddyAvatarChanged(self, buddy):
        print "(2) converting %s avatar data into wx.Bitmap" % buddy.address
        try:
            image = wx.ImageFromData(64, 64, buddy.profile_avatar_data)
            if buddy.profile_avatar_data_alpha:
                print "(2) %s avatar has alpha channel" % buddy.address
                image.SetAlphaData(buddy.profile_avatar_data_alpha)
            buddy.profile_avatar_object = wx.BitmapFromImage(image)

        except:
            print "(2)  could not convert %s avatar data to wx.Bitmap" % buddy.address
            tb()

        # notify the chat window
        for window in self.mw.chat_windows:
            if window.buddy.address == buddy.address:
                window.onBuddyAvatarChanged(buddy)
                break

        # if a tooltip for this buddy is currently shown then refresh it
        '''line = buddy.getDisplayName()
        index = self.FindItem(0, line)'''
        index = self.getIndexFromBuddy(buddy)
        if self.tool_tip <> None and index == self.tool_tip_index:
            self.openToolTip(index)

    def onListChanged(self):
        # usually called via callback from the client
        # whenever the client has saved the changed list

        # TODO: This whole method seems a bit ugly
        self.DeleteAllItems()

        #add new items to the list
        for key, buddy in enumerate(self.bl.list):
            label = buddy.getDisplayName()
            #index = self.FindItem(0, label)
            index = self.getIndexFromBuddy(buddy)
            if index == -1:
                image_idx = self.il_idx[tc_client.STATUS_OFFLINE]
                self.bl.list[key].image_idx = image_idx
                self.bl.list[key].bl_key = key
                index = self.InsertImageStringItem(sys.maxint, label, image_idx)
                self.SetItemData(index, key)
                self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
                self.onBuddyStatusChanged(buddy)
        
        # Lets sort by status
        self.SortItems(self.sortListByStatus)
                

    def onMouse(self, evt):
        self.has_mouse = True
        self.last_mouse_time = time.time()
        if self.tool_tip <> None:
            index, flags = self.HitTest(self.ScreenToClient(wx.GetMousePosition()))
            if index == -1:
                self.closeToolTip()
            elif index <> self.tool_tip_index:
                self.openToolTip(index)
            else:
                self.tool_tip.setPos(wx.GetMousePosition())
        evt.Skip()

    def onMouseEnter(self, evt):
        self.has_mouse = True

    def onMouseLeave(self, evt):
        self.has_mouse = False
        self.closeToolTip()
    
    def getIndexFromBuddy(self, buddy):
        index = self.FindItemData(-1, buddy.bl_key);
        return index
        
    def getBuddyFromIndex(self, index):
        key = self.GetItemData(index)
        buddy = self.bl.list[key]
        #wx.MessageBox(buddy.name, 'Info', wx.OK | wx.ICON_INFORMATION)
        return buddy
        '''name = self.GetItemText(index)
        for buddy in self.bl.list:
            if buddy.getDisplayName() == name:
                return buddy'''

class BuddyToolTip(wx.PopupWindow):
    def __init__(self, list, index):
        wx.PopupWindow.__init__(self, list)
        self.buddy = list.getBuddyFromIndex(index)
        self.mw = list.mw

        self.panel = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK))
        sizer = wx.BoxSizer()
        self.panel.SetSizer(sizer)

        if self.buddy.profile_avatar_object <> None:
            bitmap = self.buddy.profile_avatar_object
        else:
            bitmap = wx.Bitmap(os.path.join(config.ICON_DIR, "torchat.png"), wx.BITMAP_TYPE_PNG)
        self.avatar = wx.StaticBitmap(self.panel, -1, bitmap)
        sizer.Add(self.avatar, 0, wx.ALL, 5)

        name = self.buddy.name
        if self.buddy.profile_name <> u"":
            name = self.buddy.profile_name

        text =  "%s\n%s" % (self.buddy.address, name)

        if self.buddy.profile_text <> u"":
            text = "%s\n\n%s" % (text, textwrap.fill(self.buddy.profile_text, 30))

        if self.buddy.conn_in:
            text = "%s\n\n%s" % (text, lang.BPOP_CLIENT_SOFTWARE % (self.buddy.client, self.buddy.version))
        else:
            if self.buddy.status == tc_client.STATUS_HANDSHAKE:
                text = "%s\n\n%s" % (text, lang.BPOP_CONNECTED_AWAITING_RETURN_CONN)
            else:
                text = "%s\n\n%s" % (text, lang.BPOP_BUDDY_IS_OFFLINE)


        self.label = wx.StaticText(self.panel)
        self.label.SetLabel(text)
        sizer.Add(self.label, 0, wx.ALL, 5)

        # sizer for whole window, containing the panel
        wsizer = wx.BoxSizer()
        wsizer.Add(self.panel, 0, wx.ALL, 0)
        self.SetSizerAndFit(wsizer)
        self.Layout()

        self.setPos(wx.GetMousePosition())
        self.Show()

    def setPos(self, pos):
        self.SetPosition((pos.x +10, pos.y + 10))


class StatusSwitchList(wx.Menu):
    def __init__(self, status_switch):
        wx.Menu.__init__(self)
        self.status_switch = status_switch

        item = wx.MenuItem(self, wx.NewId(), lang.ST_AVAILABLE)
        item.SetBitmap(getStatusBitmap(tc_client.STATUS_ONLINE))
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.status_switch.onAvailable, item)

        item = wx.MenuItem(self, wx.NewId(), lang.ST_AWAY)
        item.SetBitmap(getStatusBitmap(tc_client.STATUS_AWAY))
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.status_switch.onAway, item)

        item = wx.MenuItem(self, wx.NewId(), lang.ST_EXTENDED_AWAY)
        item.SetBitmap(getStatusBitmap(tc_client.STATUS_XA))
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.status_switch.onXA, item)


class StatusSwitch(wx.Button):
    def __init__(self, parent, main_window):
        wx.Button.__init__(self, parent)
        self.parent = parent
        self.main_window = main_window
        self.status = self.main_window.buddy_list.own_status
        self.Bind(wx.EVT_BUTTON, self.onClick)
        self.setStatus(self.main_window.buddy_list.own_status)

    def onClick(self, evt):
        self.PopupMenu(StatusSwitchList(self))

    def onAvailable(self, evt):
        self.setStatus(tc_client.STATUS_ONLINE)

    def onAway(self, evt):
        self.setStatus(tc_client.STATUS_AWAY)

    def onXA(self, evt):
        self.setStatus(tc_client.STATUS_XA)

    def setStatus(self, status):
        self.status = status
        self.main_window.setStatus(status)
        if status == tc_client.STATUS_AWAY:
            status_text = lang.ST_AWAY
        if status == tc_client.STATUS_XA:
            status_text = lang.ST_EXTENDED_AWAY
        if status == tc_client.STATUS_ONLINE:
            status_text = lang.ST_AVAILABLE
        if status == tc_client.STATUS_OFFLINE:
            status_text = lang.ST_OFFLINE
        self.SetLabel(status_text)

class MyInfoBar(wx.Panel):
    def __init__(self, parent, mw):
        wx.Panel.__init__(self, parent, -1)
        
        self.mw         = mw
        self.parent     = parent
        self.avatar     = wx.StaticBitmap(self, -1, wx.EmptyBitmap(64, 64))
        self.infolabel  = wx.StaticText(self)
        
        self.hasavatar  = False
        self.hasinfo    = False
        
        self.Bind(wx.EVT_LEFT_UP, self.onClick)
        self.avatar.Bind(wx.EVT_LEFT_UP, self.onClick)
        self.infolabel.Bind(wx.EVT_LEFT_UP, self.onClick)
        
        self.updateInfo()
        self.doLayout()
        
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        
    def doLayout(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.avatar, 0, wx.ALL, 5)
        sizer.Add(self.infolabel, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.Layout()
    
    def getAvatarBitmap(self):
        if self.mw.buddy_list.own_avatar_data:
            image = wx.ImageFromData(64, 64, self.mw.buddy_list.own_avatar_data)
            if self.mw.buddy_list.own_avatar_data_alpha:
                image.SetAlphaData(self.mw.buddy_list.own_avatar_data_alpha)
            return wx.BitmapFromImage(image)
        else:
            return wx.Bitmap(os.path.join(config.ICON_DIR, "torchat.png"), wx.BITMAP_TYPE_PNG)
    
    def onClick(self, evt):
        dialog = DlgEditProfile(self, self.mw)
        dialog.ShowModal()
 
    def getInfo(self):
        info = ""
        name = config.get("profile", "name")
        text = config.get("profile", "text")
        addr = config.get("client", "own_hostname")
        
        if not name == "":
            info = info + name + "  (" + addr + ")"
        else:
            info = info + addr
        
        if not text == "":
            if not info == "":
                info = info + "\n"
            info = info + text

        if info == "":
            info = "..."
            self.hasinfo = False
        else:
            self.hasinfo = True
        
        return info
    
    def updateInfo(self):
        self.avatar.SetBitmap(self.getAvatarBitmap())
        self.avatar.Refresh()
        self.infolabel.SetLabel("%s" % (self.getInfo()))
        self.Layout()
        self.Refresh()
    
    def getSplitterHeight(self):
        bitmap = self.avatar.GetBitmap()
        return 7+bitmap.GetHeight()
        
class BuddyInfoBar(wx.Panel):
    def __init__(self, parent, buddy):
        wx.Panel.__init__(self, parent, -1)
        
        self.parent     = parent
        self.buddy      = buddy
        self.avatar     = wx.StaticBitmap(self, -1, wx.EmptyBitmap(64, 64))
        self.infolabel  = wx.TextCtrl(self, wx.ID_ANY, style = wx.TE_NO_VSCROLL|wx.TE_READONLY|wx.TE_MULTILINE|wx.NO_BORDER)
        self.infolabel.SetBackgroundColour(self.GetBackgroundColour())
        
        self.hasavatar  = False
        self.hasinfo    = False
        
        self.updateInfo()
        self.doLayout()
        
    def doLayout(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.avatar, 0, wx.ALL, 5)
        sizer.Add(self.infolabel, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.Layout()
    
    def getAvatarBitmap(self):
        if self.buddy.profile_avatar_object <> None:
            bitmap = self.buddy.profile_avatar_object
            self.hasavatar = True;
        else:
            bitmap = wx.Bitmap(os.path.join(config.ICON_DIR, "torchat.png"), wx.BITMAP_TYPE_PNG)
            self.hasavatar = False;
        return bitmap
    
    def getInfo(self):
        info = u""
        name = self.buddy.profile_name
        text = self.buddy.profile_text
        addr = self.buddy.address
        
        if not name == "":
            info = info + name + "  (" + addr + ")"
        else:
            info = info + addr
        
        if not text == "":
            if not info == "":
                info = info + os.linesep
            info = info + text

        if info == "":
            info = "..."
            self.hasinfo = False
        else:
            self.hasinfo = True
        
        return info
    
    def updateInfo(self):
        self.avatar.SetBitmap(self.getAvatarBitmap())
        self.avatar.Refresh()
        self.infolabel.SetLabel(self.getInfo())
        self.Layout()
        self.Refresh()
    
    def getSplitterHeight(self):
        if self.hasavatar or self.hasinfo:
            bitmap = self.avatar.GetBitmap()
            return 7+bitmap.GetHeight()
        else:
            return 1
    
class ChatWindow(wx.Frame):
    def __init__(self, main_window, buddy, message="",
                                    hidden=False,
                                    notify_offline_sent=False):
        wx.Frame.__init__(
            self,
            main_window,
            -1,
            size=(
                config.getint("gui", "chat_window_width"),
                config.getint("gui", "chat_window_height")
            )
        )

        self.mw = main_window
        self.buddy = buddy
        self.unread = 0
        self.dialogOpen = False
        self.updateTitle()
        
        # global chatlogs
        if config.getint("options", "enable_chatlogs_globaly"):
            self.log("")
        
        self.splitter = wx.SplitterWindow(
            self, -1,
            style=wx.SP_NOBORDER |
                  wx.SP_LIVE_UPDATE
        )
        
        self.splitter_top = wx.SplitterWindow(
            self.splitter, -1,
            style=wx.SP_NOBORDER|wx.SP_LIVE_UPDATE
        )
        
        self.panel_buddy = BuddyInfoBar(self.splitter_top, self.buddy)
        self.panel_upper = wx.Panel(self.splitter_top, -1)
        self.panel_lower = wx.Panel(self.splitter, -1)
        
        self.splitter.SetMinimumPaneSize(50)
        self.splitter.SetSashGravity(1)
        self.splitter.SetSashSize(3)
        
        self.splitter_top.SetMinimumPaneSize(1)
        self.splitter_top.SetSashGravity(0)
        self.splitter_top.SetSashSize(3)
        
        self.manualslash = False

        # incoming text (upper area)
        self.txt_in = wx.TextCtrl(
            self.panel_upper,
            -1,
            style=wx.TE_READONLY |
                  wx.TE_MULTILINE |
                  wx.TE_AUTO_URL |
                  wx.TE_AUTO_SCROLL |
                  wx.TE_RICH2 |
                  wx.BORDER_SUNKEN
        )

        # outgoing text (lower area)
        self.txt_out = wx.TextCtrl(
            self.panel_lower,
            -1,
            style=wx.TE_MULTILINE |
                  wx.TE_RICH2 |
                  wx.BORDER_SUNKEN
        )
        self.doLayout() # set the sizers

        # restore peviously saved sash position
        lower = config.getint("gui", "chat_window_height_lower")
        w,h = self.GetSize()
        if lower > h - 50:
            lower = h - 50
        self.splitter.SetSashPosition(h - lower)

        self.setFontAndColor()
        self.insertBackLog()

        om = self.buddy.getOfflineMessages()
        if om:
            om = os.linesep + "*** " + lang.NOTICE_DELAYED_MSG_WAITING + om + os.linesep
            self.writeHintLine(om)

        self.txt_in.AppendText(os.linesep) #scroll to end + 1 empty line

        if notify_offline_sent:
            self.notifyOfflineSent()

        if message != "":
            self.process(message)

        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_SHOW, self.onShow)
        self.txt_out.Bind(wx.EVT_KEY_DOWN, self.onKey)
        self.txt_in.Bind(wx.EVT_TEXT_URL, self.onURL)

        self.Bind(wx.EVT_ACTIVATE, self.onActivate)
        self.txt_in.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)
        
        self.splitter_top.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.onSplitterSashPositionChanged)

        # file drop target
        self.txt_in.SetDropTarget(DropTarget(self.mw, self.buddy))

        # Only the upper part of the chat window will
        # accept files. The lower part only text and URLs
        self.txt_out.DragAcceptFiles(False)
        
        # Set focus to txt-out - DISABLED
        #self.panel_upper.Bind(wx.EVT_CHILD_FOCUS, self.onSpecialChildFocus);
        #self.Bind(wx.EVT_CHILD_FOCUS, self.onChildFocus)
        #self.panel_buddy.infolabel.Bind(wx.EVT_TEXT_ENTER, self.onSpecialChildFocus)

        if not hidden:
            self.Show()

        self.mw.chat_windows.append(self)
        self.onBuddyStatusChanged()
    
    def onSpecialChildFocus(self, evt):
        self.txt_out.SetFocus()
        evt.Skip()

    def doLayout(self):
        outer_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_upper = wx.BoxSizer(wx.VERTICAL)
        sizer_lower = wx.BoxSizer(wx.HORIZONTAL)

        sizer_upper.Add(self.txt_in, 1, wx.ALL|wx.EXPAND, 0)
        self.panel_upper.SetSizer(sizer_upper)
        
        sizer_lower.Add(self.txt_out, 1, wx.ALL|wx.EXPAND, 0)
        self.panel_lower.SetSizer(sizer_lower)
        
        self.splitter_top.SplitHorizontally(self.panel_buddy, self.panel_upper)
        self.splitter.SplitHorizontally(self.splitter_top, self.panel_lower)

        outer_sizer.Add(self.splitter, 1, wx.ALL|wx.EXPAND, 0)
        
        self.SetSizer(outer_sizer)
        self.Layout()
        self.splitter_top.SetSashPosition(self.panel_buddy.getSplitterHeight(), True)
        
    def onShow(self, evt):
        # always make sure we are at the end when showing the window
        wx.CallAfter(self.txt_in.AppendText, "")
        wx.CallAfter(self.workaroundScrollBug)

    def insertBackLogContents(self, file_name):
        maxlines = 1000
        f = open(file_name)
        l = self.calculateBacklogLines(f)
        lines = f.readlines()
        
        if l > maxlines:
            loglink = "file:///" + file_name.replace(' ', '%20')
            self.writeHintLine("#")
            self.writeHintLine("# Log file too big")
            self.writeHintLine("# Only showing last %i lines" % (maxlines))
            self.writeHintLine("# Full log: %s" % (loglink))
            self.writeHintLine("#")
            self.writeHintLine("")
        
        limit = lines[-maxlines:]
        
        for line in limit:
            self.writeHintLine(line.rstrip().decode("UTF-8"))
            
        f.close()

    def insertBackLog(self):
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        old = os.path.join(path, "disabled_%s.log" % self.buddy.address)
        cur = os.path.join(path, "%s.log" % self.buddy.address)
        if os.path.exists(cur):
            self.insertBackLogContents(cur)
            self.writeHintLine(os.linesep + "*** " + lang.LOG_IS_ACTIVATED % cur)
        else:
            if os.path.exists(old):
                self.insertBackLogContents(old)
                self.writeHintLine(os.linesep + "*** " + lang.LOG_IS_STOPPED_OLD_LOG_FOUND % old)
    
    def calculateBacklogLines(self, f):             
        lines = 0
        buf_size = 1024 * 1024
        read_f = f.read # loop optimization
    
        buf = read_f(buf_size)
        while buf:
            lines += buf.count('\n')
            buf = read_f(buf_size)
        
        f.seek(0)
    
        return lines
    
    def setFontAndColor(self):
        font = wx.Font(
            config.getint("gui", "chat_font_size"),
            wx.SWISS,
            wx.NORMAL,
            wx.NORMAL,
            False,
            config.get("gui", "chat_font_name")
        )
        self.txt_out.SetFont(font)
        self.txt_in.SetFont(font)
        if config.getint("gui", "color_text_use_system_colors") == 0:
            self.txt_out.SetBackgroundColour(config.get("gui", "color_text_back"))
            self.txt_in.SetBackgroundColour(config.get("gui", "color_text_back"))
            self.txt_out.SetForegroundColour(config.get("gui", "color_text_fore"))
            self.txt_out.SetDefaultStyle(wx.TextAttr(config.get("gui", "color_text_fore")))

    def updateTitle(self):
        if self.unread == 1:
            title = "* "
        elif self.unread > 1:
            title = "*[%i] " % self.unread
        else:
            title = ""

        title += self.buddy.getDisplayNameOrAddress()
        #if self.buddy.name != "":
        #    title += " (%s)" % self.buddy.name
        
        self.SetTitle(title + " -- Torchat %s" % config.getProfileShortName())
        #self.SetTitle(title + " %s" % config.getProfileLongName())

    def getTitleShort(self):
        t = self.GetTitle()
        return t[:-19]

    def workaroundScrollBug(self):
        # workaround scroll bug on windows
        # https://sourceforge.net/tracker/?func=detail&atid=109863&aid=665381&group_id=9863
        if config.isWindows():
            self.txt_in.ScrollLines(-1)
            self.txt_in.ShowPosition(self.txt_in.GetLastPosition())
            self.txt_in.ScrollLines(1)
            
        self.txt_in.AppendText("")
    
    def getNicknameColor(self, nickname):
        colors = config.get("gui", "nickname_colors").split(',')
        charsum = 0
        for c in nickname:
            charsum = charsum + ord(c)
        index = charsum%len(colors)
        return colors[index]

    def writeColored(self, color, name, text):
        # this method will write to the chat window and
        # will also write to the log file if logging is enabled.
        
        # Capture groupchat nicknames and give them a bunch of different colors
        regex = re.compile("^(<([^>]+)> )",re.IGNORECASE|re.UNICODE)
        match = regex.search(text)
        if match:
            nick  = match.group(1)
            name  = match.group(2)
            color = self.getNicknameColor(name)
            text  = text.replace(nick, "")
        
        self.txt_in.SetDefaultStyle(wx.TextAttr(config.get("gui", "color_time_stamp")))
        self.txt_in.write("%s " % time.strftime(config.get("gui", "time_stamp_format")))
        self.txt_in.SetDefaultStyle(wx.TextAttr(color))
        self.txt_in.write("%s: " % name)
        if config.getint("gui", "color_text_use_system_colors") == 0:
            self.txt_in.SetDefaultStyle(wx.TextAttr(config.get("gui", "color_text_fore")))
        else:
            self.txt_in.SetDefaultStyle(wx.TextAttr(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)))
        self.txt_in.write(text + os.linesep)
        
        self.workaroundScrollBug()
        
        # write log
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()

        if os.path.exists(os.path.join(path, "%s.log" % self.buddy.address)):
            logtext = "%s %s: %s" % (time.strftime("(%Y-%m-%d %H:%M)"), name, text)
            self.log(logtext)

    def writeHintLine(self, line):
        self.txt_in.SetDefaultStyle(wx.TextAttr(config.get("gui", "color_time_stamp")))
        self.txt_in.write(line + os.linesep)
        if config.getint("gui", "color_text_use_system_colors") == 0:
            self.txt_in.SetDefaultStyle(wx.TextAttr(config.get("gui", "color_text_fore")))
        else:
            self.txt_in.SetDefaultStyle(wx.TextAttr(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)))

        self.workaroundScrollBug()
    
    def writeSystemLine(self, line):
        self.txt_in.SetDefaultStyle(wx.TextAttr(config.get("gui", "color_time_stamp")))
        self.txt_in.write("%s " % time.strftime(config.get("gui", "time_stamp_format")))
        self.txt_in.write(line + os.linesep)
        if config.getint("gui", "color_text_use_system_colors") == 0:
            self.txt_in.SetDefaultStyle(wx.TextAttr(config.get("gui", "color_text_fore")))
        else:
            self.txt_in.SetDefaultStyle(wx.TextAttr(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)))

        self.workaroundScrollBug()
        
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        
        if os.path.exists(os.path.join(path, "%s.log" % self.buddy.address)):
            logtext = "%s %s" % (time.strftime("(%Y-%m-%d %H:%M)"), line)
            self.log(logtext)

    def notify(self, name, message):
        #needs unicode
        if not self.IsActive():
            if config.getint("gui", "notification_flash_window"):
                self.RequestUserAttention(wx.USER_ATTENTION_INFO)
            self.unread += 1
            self.updateTitle()

            if config.getint("gui", "notification_popup"):
                if not self.isNotifyDisabled():
                    message = textwrap.fill(message, 40)
                    tc_notification.notificationWindow(self.mw, name, message, self.buddy)

        if not self.IsShown():
            self.mw.taskbar_icon.blink()

    def notifyOfflineSent(self):
        #all should be unicode here
        message = "[%s]" % lang.NOTICE_DELAYED_MSG_SENT
        self.writeColored(config.get("gui", "color_nick_myself"), "myself", message)
        self.notify("to %s" % self.buddy.address, message)

    def process(self, message):
        #message must be unicode
        if self.buddy.name != "":
            name = self.buddy.name
        else:
            name = self.buddy.address
        self.writeColored(config.get("gui", "color_nick_buddy"), name, message)
        self.notify(name, message)

    def onActivate(self, evt):
        self.unread = 0
        self.updateTitle()
        evt.Skip()
        
    def onChildFocus(self, evt):
        # no matter which child just got focus, we give
        # it back to the lower text panel since this is the
        # only control that should ever own the keyboard.
        if not self.dialogOpen:
            self.txt_out.SetFocus()
        
        evt.Skip()
        

    def onClose(self, evt):
        if config.getint("options", "confirm_close_chat"):
            dlg = wx.MessageDialog(self, lang.D_WARN_CLOSE_CHATWINDOW_MESSAGE, lang.D_WARN_CLOSE_CHATWINDOW_TITLE, wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                self.doClose()
        else:
            self.doClose()
    
    def doClose(self):
        w,h = self.GetSize()
        config.set("gui", "chat_window_width", w)
        config.set("gui", "chat_window_height", h)
        config.set("gui", "chat_window_height_lower", h - self.splitter.GetSashPosition())
        self.mw.chat_windows.remove(self)
        self.Hide()
        self.Destroy()

    def onKey(self, evt):
        #TODO: in wine there is/was a problem with shift-enter. Is this fixed now?
        #TODO: There was an unconfirmed report that the enter key would not work at all in Windows 7, is this true?
        print "(3) key pressed: %i" % evt.GetKeyCode() # debug the windows 7 problem
        if evt.GetKeyCode() == wx.WXK_RETURN and not evt.ShiftDown():
            self.onSend(evt)
        else:
            if evt.ControlDown():
                # ENABLE COPY
                if evt.GetKeyCode() == ord('C'):
                    self.onCopy(evt)
                # CLOSE
                if evt.GetKeyCode() == ord('W'):
                    self.onClose(evt)
            # shift-enter will produce 0x0b (vertical tab) (only on windows!)
            # we will deal with this later in the onSend method
            evt.Skip()

    def onSend(self, evt):
        text = self.txt_out.GetValue().rstrip().lstrip().replace("\x0b", os.linesep)
        
        if text == "":
            return
            
        self.txt_out.SetValue("")
        
        if self.buddy.status not in  [tc_client.STATUS_OFFLINE, tc_client.STATUS_HANDSHAKE]:
            self.buddy.sendChatMessage(text)
            self.writeColored(config.get("gui", "color_nick_myself"),
                              "myself",
                              text)
        else:
            self.buddy.storeOfflineChatMessage(text)
            self.writeColored(config.get("gui", "color_nick_myself"),
                              "myself",
                              "[%s] %s" % (lang.NOTICE_DELAYED, text))

    def onURL(self, evt):
        # All URL mouse events trigger this
        # Get URL
        start = evt.GetURLStart()
        end = evt.GetURLEnd()
        url = self.txt_in.GetRange(start, end)
        # Get URL Type
        if url.find('file:///') == 0:
            if evt.GetMouseEvent().GetEventType() == wx.wxEVT_LEFT_DOWN:
                wx.LaunchDefaultBrowser(url)
            else:
                evt.Skip()
        else:
            # Filter by mouse event
            if evt.GetMouseEvent().GetEventType() == wx.wxEVT_LEFT_DCLICK:
                # Open url in default browser
                # TODO: Open in torbrowser
                wx.LaunchDefaultBrowser(url)
            elif evt.GetMouseEvent().GetEventType() == wx.wxEVT_LEFT_DOWN:
                #left button down, copy to clipboard
                if not wx.TheClipboard.IsOpened():
                    clipdata = wx.TextDataObject()
                    clipdata.SetText(url)
                    wx.TheClipboard.Open()
                    wx.TheClipboard.SetData(clipdata)
                    wx.TheClipboard.Close()
            else:
                evt.Skip()

    def onContextMenu(self, evt):
        menu = wx.Menu()

        id = wx.NewId()
        item = wx.MenuItem(menu, id, '&Copy\tCtrl+C')
        self.Bind(wx.EVT_MENU, self.onCopy, id=id)
        menu.AppendItem(item)
        sel_from, sel_to = self.txt_in.GetSelection()
        empty = (sel_from == sel_to)
        if empty:
            item.Enable(False)

        id = wx.NewId()
        item = wx.MenuItem(menu, id, lang.MPOP_SEND_FILE)
        self.Bind(wx.EVT_MENU, self.onSendFile, id=id)
        menu.AppendItem(item)

        id = wx.NewId()
        item = wx.MenuItem(menu, id, lang.MPOP_EDIT_CONTACT)
        self.Bind(wx.EVT_MENU, self.onEditBuddy, id=id)
        menu.AppendItem(item)

        menu.AppendSeparator()

        if not self.isLoggingActivated():
            item = wx.MenuItem(menu, wx.NewId(), lang.MPOP_ACTIVATE_LOG)
            menu.AppendItem(item)
            menu.Bind(wx.EVT_MENU, self.onActivateLog, item)

            if self.hasOldLog():
                item = wx.MenuItem(menu, wx.NewId(), lang.MPOP_DELETE_EXISTING_LOG)
                menu.AppendItem(item)
                menu.Bind(wx.EVT_MENU, self.onDeleteLog, item)

        else:
            item = wx.MenuItem(menu, wx.NewId(), lang.MPOP_STOP_LOG)
            menu.AppendItem(item)
            menu.Bind(wx.EVT_MENU, self.onStopLog, item)

            item = wx.MenuItem(menu, wx.NewId(), lang.MPOP_DELETE_AND_STOP_LOG)
            menu.AppendItem(item)
            menu.Bind(wx.EVT_MENU, self.onDeleteLog, item)
        
        menu.AppendSeparator()
        
        if not self.isNotifyDisabled():
            item = wx.MenuItem(menu, wx.NewId(), "Disable pop-up notifications")
            menu.AppendItem(item)
            menu.Bind(wx.EVT_MENU, self.onDisableNotifications, item)
        else:
            item = wx.MenuItem(menu, wx.NewId(), "Enable pop-up notifications")
            menu.AppendItem(item)
            menu.Bind(wx.EVT_MENU, self.onEnableNotifications, item)

        self.PopupMenu(menu)
        menu.Destroy()

    def onCopy(self, evt):
        print "onCopy called"
        sel_from, sel_to = self.txt_in.GetSelection()
        if sel_from == sel_to:
            return
        text = self.txt_in.GetRange(sel_from, sel_to)
        clipdata = wx.TextDataObject()
        clipdata.SetText(text)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

    def onSendFile(self, evt):
        title = lang.DFT_FILE_OPEN_TITLE % self.buddy.getAddressAndDisplayName()
        dialog = wx.FileDialog(self, title, style=wx.OPEN)
        dialog.SetDirectory(config.getHomeDir())
        if dialog.ShowModal() == wx.ID_OK:
            file_name = dialog.GetPath()
            FileTransferWindow(self.mw, self.buddy, file_name)

    def onEditBuddy(self, evt):
        dialog = DlgEditContact(self, self.mw, self.buddy)
        self.dialogOpen = True
        dialog.ShowModal()
        self.onBuddyChanged()

    def onBuddyStatusChanged(self):
        bmp = getStatusBitmap(self.buddy.status)
        icon = wx.IconFromBitmap(bmp)
        self.SetIcon(icon)
        self.onBuddyChanged()

    def onBuddyAvatarChanged(self, buddy):
        self.buddy = buddy
        self.onBuddyChanged()
        pass

    def onBuddyProfileChanged(self, buddy):
        self.buddy = buddy
        self.onBuddyChanged()
        pass

    def isLoggingActivated(self):
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        return os.path.exists(os.path.join(path, '%s.log' % self.buddy.address))
    
    def isNotifyDisabled(self):
        excluded_users = config.get("gui", "notification_excluded_users").split(",")
        try:
            i = excluded_users.index(self.buddy.address)
        except ValueError:
            i = -1
        if i < 0:
            return False
        else:
            return True

    def hasOldLog(self):
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        return os.path.exists(os.path.join(path, 'disabled_%s.log' % self.buddy.address))
    
    def onDisableNotifications(self, evt):
        buddy_address = self.buddy.address
        if not self.isNotifyDisabled():
            excluded_users = config.get("gui", "notification_excluded_users").split(",")
            excluded_users.append(buddy_address)
            config.set("gui", "notification_excluded_users", ",".join(excluded_users))
    
    def onEnableNotifications(self, evt):
        buddy_address = self.buddy.address
        if self.isNotifyDisabled():
            excluded_users = config.get("gui", "notification_excluded_users").split(",")
            index = excluded_users.index(buddy_address)
            excluded_users.pop(index)
            config.set("gui", "notification_excluded_users", ",".join(excluded_users))
        
    def onActivateLog(self, evt):
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        old = os.path.join(path, "disabled_%s.log" % self.buddy.address)
        cur = os.path.join(path, "%s.log" % self.buddy.address)
        if os.path.exists(old):
            shutil.move(old, cur)
        self.log("") # this will create it
        self.writeColored(config.get("gui", "color_nick_myself"), "***", "[%s]" % lang.LOG_STARTED)

    def onStopLog(self, evt):
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        old = os.path.join(path, "disabled_%s.log" % self.buddy.address)
        cur = os.path.join(path, "%s.log" % self.buddy.address)
        if os.path.exists(cur):
            self.writeColored(config.get("gui", "color_nick_myself"), "***", "[%s]" % lang.LOG_STOPPED)
            shutil.move(cur, old)

    def onDeleteLog(self, evt):
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        old = os.path.join(path, "disabled_%s.log" % self.buddy.address)
        cur = os.path.join(path, "%s.log" % self.buddy.address)
        tc_client.wipeFile(old)
        tc_client.wipeFile(cur)
        self.writeHintLine("*** %s" % lang.LOG_DELETED)

    def log(self, msg):
        path = config.get("logging", "chatlog_path")
        if path == "":
            path = config.getDataDir()
        file_name = os.path.join(path, "%s.log" % self.buddy.address)
        if not os.path.exists(file_name):
            f = open(file_name, "w")
            os.chmod(file_name, 0600)
            f.write(("*** " + lang.LOG_HEADER + os.linesep + os.linesep).encode("UTF-8"))
        else:
            f = open(file_name, "a")

        if msg <> "":
            f.write((msg + os.linesep).encode("UTF-8"))
        f.close()
    
    def onSplitterSashPositionChanged(self, evt):
        newpos = self.splitter_top.GetSashPosition()
        if not newpos == self.panel_buddy.getSplitterHeight():
            self.manualslash = True
    
    def onBuddyChanged(self):
        self.updateTitle()
        self.panel_buddy.updateInfo()
        if not self.manualslash:
            self.splitter_top.SetSashPosition(self.panel_buddy.getSplitterHeight(), True)


class BetterFileDropTarget(wx.FileDropTarget):
    def getFileName(self, filenames):
        if len(filenames) == 0:
            return None

        file_name = filenames[0]

        # --- begin evil hack
        if not os.path.exists(file_name):
            #sometimes the file name is in utf8
            #but inside a unicode string!
            #TODO: must report this bug to wx
            print "(2) dropped file not found with dropped file_name, trying UTF-8 hack"
            try:
                file_name_utf8 = ""
                for c in file_name:
                    file_name_utf8 += chr(ord(c))
                file_name = file_name_utf8.decode("utf-8")
            except:
                tb()
                wx.MessageBox("there is a strange bug in wx for your platform with wx.FileDropTarget and non-ascii characters in file names")
                return None
        # --- end evil hack

        print "(2) file dropped: %s" % file_name
        return file_name


class DropTarget(BetterFileDropTarget):
    #TODO: file dopping does not work in wine at all
    def __init__(self, mw, buddy):
        wx.FileDropTarget.__init__(self)
        self.mw = mw
        self.buddy = buddy

    def OnDropFiles(self, x, y, filenames):
        if len(filenames) > 1:
            wx.MessageBox(lang.D_WARN_FILE_ONLY_ONE_MESSAGE,
                          lang.D_WARN_FILE_ONLY_ONE_TITLE)
            return

        file_name = self.getFileName(filenames)

        if file_name is None:
            return

        """
        if not self.window.buddy.isFullyConnected():
            wx.MessageBox(lang.D_WARN_BUDDY_OFFLINE_MESSAGE,
                          lang.D_WARN_BUDDY_OFFLINE_TITLE)
            return
        """

        if self.buddy:
            buddy = self.buddy
        else:
            # this is the drop target for the buddy list
            # find the buddy
            buddy = self.mw.gui_bl.getBuddyFromXY((x,y))
            if buddy:
                print "(2) file dropped at buddy %s" % buddy.address
            else:
                print "(2) file dropped on empty space, ignoring"
                return

        FileTransferWindow(self.mw, buddy, file_name)


class AvatarDropTarget(BetterFileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        file_name = self.getFileName(filenames)
        if file_name is None:
            return

        root, ext = os.path.splitext(file_name)
        if ext.lower() <> ".png":
            wx.MessageBox(lang.DEP_WARN_MUST_BE_PNG, lang.DEP_WARN_TITLE)
            return

        self.window.onAvatarSelected(file_name)


class FileTransferWindow(wx.Frame):
    def __init__(self, main_window, buddy, file_name, receiver=None):
        #if receiver is given (a FileReceiver instance) we initialize
        #a Receiver Window, else we initialize a sender window and
        #let the client library create us a FileSender instance
        wx.Frame.__init__(self, main_window, -1)
        self.mw = main_window
        self.buddy = buddy

        self.bytes_total = 1
        self.bytes_complete = 0
        self.file_name = file_name
        self.file_name_save = ""
        self.completed = False
        self.error = False
        self.error_msg = ""
        self.autosave = False
        self.alldone = False
        self.bytesdiff = 0;
        self.prevtime = datetime.now();
        self.transferrate = 0

        if not receiver:
            self.is_receiver = False
            self.transfer_object = self.buddy.sendFile(self.file_name,
                                                       self.onDataChange)
        else:
            self.is_receiver = True
            receiver.setCallbackFunction(self.onDataChange)
            self.transfer_object = receiver
            self.bytes_total = receiver.file_size
            self.file_name = file_name

        self.panel = wx.Panel(self)
        self.outer_sizer = wx.BoxSizer()
        grid_sizer = wx.GridBagSizer(vgap = 5, hgap = 5)
        grid_sizer.AddGrowableCol(0)
        self.outer_sizer.Add(grid_sizer, 1, wx.EXPAND | wx.ALL, 5)

        self.text = wx.StaticText(self.panel, -1, "")
        self.text.SetMinSize((300,-1))
        grid_sizer.Add(self.text, (0, 0), (1, 4), wx.EXPAND)

        self.progress_bar = wx.Gauge(self.panel)
        grid_sizer.Add(self.progress_bar, (1, 0), (1, 4), wx.EXPAND)

        if self.is_receiver:
            # the first button that is created will have the focus, so
            # we create the save button first. 
            # SetDefault() does not seem to work in a wx.Frame.
            self.btn_save = wx.Button(self.panel, wx.ID_SAVEAS, lang.BTN_SAVE_AS)
            self.btn_save.Bind(wx.EVT_BUTTON, self.onSave)
            # Notify user
            self.chatMessage('You are receiving "' + self.file_name + '"')
            # Attempt to auto-save the file
            if self.autoSave():
                self.btn_save.SetLabel("Auto saving")
                self.btn_save.Enable(False)
        else:
            self.chatMessage('You are sending "' + self.file_name + '"')
                
            
        self.btn_cancel = wx.Button(self.panel, wx.ID_CANCEL, lang.BTN_CANCEL)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.onCancel)

        if self.is_receiver:
            grid_sizer.Add(self.btn_cancel, (2, 2))
            grid_sizer.Add(self.btn_save, (2, 3))
        else:
            grid_sizer.Add(self.btn_cancel, (2, 3))
                
        self.panel.SetSizer(self.outer_sizer)
        self.updateOutput()
        self.outer_sizer.Fit(self)

        self.Disable()
        self.Show()
        self.Enable()

    def updateOutput(self):
        if self.bytes_complete == -1:
            self.error = True
            self.completed = True
            self.bytes_complete = 0
        
        percent = 100.0 * self.bytes_complete / self.bytes_total
        peer_name = self.buddy.address
        if self.buddy.name != "":
            peer_name += " (%s)" % self.buddy.name
        title = "%04.1f%% - %s" % (percent, os.path.basename(self.file_name))
        self.SetTitle(title)
        self.progress_bar.SetValue(percent)

        if self.is_receiver:
            text = lang.DFT_RECEIVE \
                % (os.path.basename(self.file_name),
                   peer_name, percent,
                   self.bytes_complete,
                   self.bytes_total)
        else:
            text = lang.DFT_SEND \
                % (os.path.basename(self.file_name),
                   peer_name, percent,
                   self.bytes_complete,
                   self.bytes_total)
        
        # Append transfer rate
        text = "%s\n%.2f KB/s%s" % (text, self.transferrate, self.getETA())
        
        
        try:
            # the client has no translation files,
            # it will send these english error messages
            error_msg_trans = {
                "waiting for connection" : lang.DFT_WAITING,
                "starting transfer" : lang.DFT_STARTING,
                "transfer complete" : lang.DFT_COMPLETE,
                "transfer aborted" : lang.DFT_ABORTED,
                "error" : lang.DFT_ERROR
            }[self.error_msg]
        except:
            error_msg_trans = self.error_msg

        # error_msg might also contain info messages like
        # "waiting", etc. which are not fatal errors
        text = "%s\n%s" % (text, error_msg_trans)
        

        # a fatal error
        if self.error:
            self.btn_cancel.SetLabel(lang.BTN_CLOSE)
            if self.is_receiver:
                self.btn_save.Enable(False)

        self.text.SetLabel(text)

        if self.bytes_complete == self.bytes_total:
            self.completed = True
            self.progress_bar.SetValue(100)
            if self.is_receiver:
                if self.file_name_save != "":
                    if not self.alldone:
                        self.alldone = True
                        self.chatMessage('Received "file:///' + self.file_name_save.replace(' ', '%20') + '"')
                    self.btn_cancel.SetLabel(lang.BTN_CLOSE)
                    self.transfer_object.close() #this will actually save the file
                    if self.autosave:
                        self.Close();
                else:
                    if not self.alldone:
                        self.alldone = True
                        self.chatMessage('Received file "' + self.file_name + '" is ready to be saved...')
            else:
                # Prevent displaying of multiple messages while the event is still firing...
                if not self.alldone:
                    self.alldone = True
                    self.chatMessage('Successfully sent file "' + self.file_name + '"')
                #self.btn_cancel.SetLabel(lang.BTN_CLOSE)
                self.Close();

    def onDataChange(self, total, complete, error_msg=""):
        #will be called from the FileSender/FileReceiver-object in the
        #protocol module to update gui (called from a non-GUI thread!)
        
        deltabytes = complete - self.bytes_complete
        
        self.bytes_total = total
        self.bytes_complete = complete
        self.error_msg = error_msg
        
        self.updateTransferStats(deltabytes)

        #we must use wx.Callafter to make calls into wx
        #because we are *NOT* in the context of the GUI thread here
        wx.CallAfter(self.updateOutput)
    
    def updateTransferStats(self, bytesdiff):
        self.bytesdiff += bytesdiff
        now = datetime.now();
        timedelta = now - self.prevtime
        seconds = self.getTimeDeltaInSeconds(timedelta)
        
        if seconds > 1.0:
            self.transferrate = (self.bytesdiff/1024)/seconds
            self.bytesdiff = 0
            self.prevtime = now
    
    def getTimeDeltaInSeconds(self, timedelta):
        return timedelta.seconds + timedelta.microseconds/1E6
    
    def getETA(self):
        text = ""
        if self.transferrate > 0:
            kilobytes = (self.bytes_total-self.bytes_complete)/1024
            timetotal = kilobytes/self.transferrate
            
            seconds = int(math.floor(timetotal%60))
            minutes = int(math.floor((timetotal/60)%60))
            hours = int(math.floor(timetotal/3600))
            days = int(math.floor(timetotal/86400))
            
            if days > 0:
                text = "%id, %ih, %im and %is" % (days, hours, minutes, seconds)
            else:
                if hours > 0:
                    text = "%ih, %im and %is" % (hours, minutes, seconds)
                else:
                    if minutes > 0:
                        text = "%i minutes and %i seconds" % (minutes, seconds)
                    else:
                        text = "%i seconds" % (seconds)
            
            text = ", %s" % (text)
                
        return text

    def onCancel(self, evt):
        try:
            # this is not always a real "cancel":
            # FileReceiver.close() *after* successful transmission
            # will save the file (if file name is known)
            self.transfer_object.close()
        except:
            pass
        self.Close()
    
    def autoSave(self):
        basepath = config.getUserCustomDir()
        
        # Check if the path exists, if not, autosave cannot continue
        if basepath == "":
            return False
        
        # We want to store files in a user folder
        if self.buddy.name != "":
            buddy_dir   = self.buddy.name + ' ' + self.buddy.address
        else:
            buddy_dir   = self.buddy.address
        
        # Create full path, strip invalid chars from username
        fullpath    = os.path.join(basepath, re.sub('[\/\\\:\*\?\"\<\>\|]+', '', buddy_dir)); 
        
        if not os.path.isdir(fullpath):
            try:
                os.makedirs(fullpath)
            except OSError:
                return False
        
        # We need more info the file
        fullname = self.file_name;
        basename, extension = os.path.splitext(fullname)
        # Create the filepath
        filepath   =  os.path.join(fullpath, fullname)
        # Create a counter
        counter = 1;
        
        while os.path.exists(filepath):
            filepath =  os.path.join(fullpath, basename + ' (renamed ' + str(counter) + ')' + extension)
            counter += 1
        
        # Tell the FileReciever we want to save the file on our location
        self.transfer_object.setFileNameSave(filepath)
        if not self.transfer_object.file_handle_save:
            error = self.transfer_object.file_save_error
            wx.MessageBox(lang.D_WARN_FILE_SAVE_ERROR_MESSAGE % (filepath, error),
                          lang.D_WARN_FILE_SAVE_ERROR_TITLE)
            self.file_name_save = ""
            return False
        
        # Set our save file destination
        self.file_name_save = filepath
        self.autosave = True
        
        return True
    
    def chatMessage(self, message, notify=True):
        chatwindow = None
        for window in self.mw.chat_windows:
            if window.buddy.address == self.buddy.address:
                chatwindow = window
        
        if chatwindow == None:
            chatwindow = ChatWindow(self.mw, self.buddy, "", True)
            chatwindow.Show()
            
        chatwindow.writeSystemLine(message)
        if notify:
            chatwindow.notify(self.buddy.name, message)

    def onSave(self, evt):
        title = lang.DFT_FILE_SAVE_TITLE % self.buddy.getAddressAndDisplayName()
        dialog = wx.FileDialog(self, title, defaultFile=self.file_name, style=wx.SAVE)
        
        
        if config.isPortable():
            dialog.SetDirectory(config.getDataDir())
        else:
            dialog.SetDirectory(config.getHomeDir())
            
        
        if dialog.ShowModal() == wx.ID_OK:
            self.file_name_save = dialog.GetPath()

            if os.path.exists(self.file_name_save):
                overwrite = wx.MessageBox(lang.D_WARN_FILE_ALREADY_EXISTS_MESSAGE % self.file_name_save,
                                          lang.D_WARN_FILE_ALREADY_EXISTS_TITLE,
                                          wx.YES_NO)
                if overwrite != wx.YES:
                    self.file_name_save = ""
                    return

            self.transfer_object.setFileNameSave(self.file_name_save)
            if not self.transfer_object.file_handle_save:
                error = self.transfer_object.file_save_error
                wx.MessageBox(lang.D_WARN_FILE_SAVE_ERROR_MESSAGE % (self.file_name_save, error),
                              lang.D_WARN_FILE_SAVE_ERROR_TITLE)
                self.file_name_save = ""
                return

            self.btn_save.Enable(False)
            if self.completed:
                self.chatMessage(u'Saved file "file:///' + self.file_name_save.replace(' ', '%20') + '"')
                self.onCancel(evt)
        else:
            pass


class MainWindow(wx.Frame):
    def __init__(self, socket=None):
        wx.Frame.__init__(
            self,
            None,
            -1,
            "TorChat",
            size=(
                config.getint("gui", "main_window_width"),
                config.getint("gui", "main_window_height")
            )
        )
        self.conns = []
        self.chat_windows = []
        self.buddy_list = tc_client.BuddyList(self.callbackMessage, socket)
        
        self.updateTitle()

        self.Bind(wx.EVT_CLOSE, self.onClose)

        # setup gui elements
        self.taskbar_icon = TaskbarIcon(self)
        self.main_panel = wx.Panel(self)
        
        self.splitter = wx.SplitterWindow(
            self.main_panel, -1,
            style=wx.SP_NOBORDER|wx.SP_LIVE_UPDATE
        )
        
        self.splitter.SetMinimumPaneSize(1)
        self.splitter.SetSashGravity(0)
        self.splitter.SetSashSize(3)
        
        self.panel_list = wx.Panel(self.splitter, -1)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_list = wx.BoxSizer(wx.VERTICAL)
        
        self.gui_bl = BuddyList(self.panel_list, self)
        self.my_info = MyInfoBar(self.splitter, self)
        self.status_switch = StatusSwitch(self.main_panel, self)

        sizer_list.Add(self.gui_bl, 1, wx.EXPAND)
        self.panel_list.SetSizer(sizer_list)
        
        self.splitter.SplitHorizontally(self.my_info, self.panel_list)
        
        sizer.Add(self.splitter, 1, wx.EXPAND)
        sizer.Add(self.status_switch, 0, wx.EXPAND)
        self.main_panel.SetSizer(sizer)
        sizer.FitInside(self)
        
        self.Layout()
        
        self.splitter.SetSashPosition(self.my_info.getSplitterHeight())

        icon = wx.Icon(name=os.path.join(config.ICON_DIR, "torchat.ico"),
                       type=wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        
        self.setMenu();

        if not config.getint("gui", "open_main_window_hidden"):
            self.Show()

    def setMenu(self):
        '''menubar = wx.MenuBar()
        # CREATE MENUS
        tcMenu = wx.Menu() # Torchat
        clMenu = wx.Menu() # Contacts
        hpMenu = wx.Menu() # Help
        
        # MENU ITEMS
        tcItemPrefs = tcMenu.Append(wx.ID_PREFERENCES, '&Options\tCtrl+O', 'Preferences')
        tcMenu.AppendSeparator()
        tcItemQuit = tcMenu.Append(wx.ID_EXIT, '&Quit\tCtrl+Q', 'Quit application')
        
        #settings
        
        item = wx.MenuItem(self, wx.NewId(), lang.MPOP_SETTINGS)
        self.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.onSettings, item)
        
        # EVENTS
        self.Bind(wx.EVT_MENU, self.onPrefs, tcItemPrefs)
        self.Bind(wx.EVT_MENU, self.onQuit, tcItemQuit)
        
        # ADD MENU ITEMS
        menubar.Append(tcMenu, '&Torchat')
        
        self.SetMenuBar(menubar)'''
        
        # TOOLBAR
        
        toolbar = self.CreateToolBar()
        prefTool = toolbar.AddLabelTool(wx.ID_PREFERENCES, lang.TOOL_SETTINGS_LABEL, wx.Bitmap('icons/settings.png'), shortHelp=lang.TOOL_SETTINGS_HELP)
        addCTool = toolbar.AddLabelTool(wx.ID_ADD, lang.TOOL_ADD_CONTACT_LABEL, wx.Bitmap('icons/add.png'), shortHelp=lang.TOOL_ADD_CONTACT_HELP)
        EditTool = toolbar.AddLabelTool(wx.ID_EDIT, lang.TOOL_EDIT_PROFILE_LABEL, wx.Bitmap('icons/edit.png'), shortHelp=lang.TOOL_EDIT_PROFILE_HELP)
        IdntTool = toolbar.AddLabelTool(wx.ID_REFRESH, lang.TOOL_NEW_IDENTITY_LABEL, wx.Bitmap('icons/newidentity.png'), shortHelp=lang.TOOL_NEW_IDENTITY_HELP)
        self.Bind(wx.EVT_TOOL, self.onPrefs, prefTool)
        self.Bind(wx.EVT_TOOL, self.onAddContact, addCTool)
        self.Bind(wx.EVT_TOOL, self.onEditProfile, EditTool)
        self.Bind(wx.EVT_TOOL, self.onNewIdentity, IdntTool)
        self.Bind(wx.EVT_TOOL, self.onQuit, id=wx.ID_EXIT)
        toolbar.Realize()
        
        accel_tbl = wx.AcceleratorTable([
                                         (wx.ACCEL_CTRL, ord('O'), wx.ID_PREFERENCES),
                                         (wx.ACCEL_CTRL, ord('Q'), wx.ID_EXIT),
                                         (wx.ACCEL_CTRL, ord('E'), wx.ID_EDIT),
                                         (wx.ACCEL_CTRL, ord('N'), wx.ID_ADD)
                                        ])
        self.SetAcceleratorTable(accel_tbl)
    
    def updateTitle(self):
        if len(config.get('profile', 'name')) > 0:
            title = config.get('profile', 'name') + ' (' +config.getProfileLongName()+')'
        else:
            title = config.getProfileLongName()
        self.SetTitle("TorChat: %s" % title)
            
    def setStatus(self, status):
        self.buddy_list.setStatus(status)
        self.taskbar_icon.showStatus(status)

    def callbackMessage(self, callback_type, callback_data):
        #we must always use wx.CallAfter() to interact with
        #the GUI-Thread because this method will be called
        #in the context of one of the connection threads

        if callback_type == tc_client.CB_TYPE_CHAT:
            buddy, message = callback_data
            for window in self.chat_windows:
                if window.buddy.address == buddy.address:
                    wx.CallAfter(window.process, message)
                    return
            #no window found, so we create a new one
            hidden = config.getint("gui", "open_chat_window_hidden")
            wx.CallAfter(ChatWindow, self, buddy, message, hidden)

            #we let this thread block until the window
            #shows up in our chat window list
            found = False
            while not found:
                time.sleep(1)
                for window in self.chat_windows:
                    if window.buddy.address == buddy.address:
                        found = True
                        break

        if callback_type == tc_client.CB_TYPE_OFFLINE_SENT:
            buddy = callback_data
            for window in self.chat_windows:
                if window.buddy.address == buddy.address:
                    wx.CallAfter(window.notifyOfflineSent)
                    return

            hidden = config.getint("gui", "open_chat_window_hidden")
            wx.CallAfter(ChatWindow, self, buddy, "", hidden, notify_offline_sent=True)

        if callback_type == tc_client.CB_TYPE_FILE:
            #this happens when an incoming file transfer was initialized
            #we must now create a FileTransferWindow and return its
            #event handler method to the caller
            receiver = callback_data
            buddy = receiver.buddy
            file_name = receiver.file_name

            #we cannot get return values from wx.CallAfter() calls
            #so we have to CallAfter() and then just wait for
            #the TransferWindow to appear.
            wx.CallAfter(FileTransferWindow, self,
                                             buddy,
                                             file_name,
                                             receiver)

        if callback_type == tc_client.CB_TYPE_STATUS:
            # this is called when the status of one of the
            # buddies has changed. callback_data is the Buddy instance
            wx.CallAfter(self.gui_bl.onBuddyStatusChanged, callback_data)

        if callback_type == tc_client.CB_TYPE_AVATAR:
            # this is called when the avatar of one of the
            # buddy has changed. callback_data is the Buddy instance
            wx.CallAfter(self.gui_bl.onBuddyAvatarChanged, callback_data)

        if callback_type == tc_client.CB_TYPE_PROFILE:
            # this is called when the profile of one of the
            # buddy has changed. callback_data is the Buddy instance
            wx.CallAfter(self.gui_bl.onBuddyProfileChanged, callback_data)

        if callback_type == tc_client.CB_TYPE_LIST_CHANGED:
            try:
                wx.CallAfter(self.gui_bl.onListChanged)
            except:
                # might be too early and there is no gui_bl object yet.
                # But this does not matter because gui_bl itself will
                # call this at least once after initialization.
                pass

        if callback_type == tc_client.CB_TYPE_REMOVE:
            # called when the client is removing the buddy from the list
            # callback_data is the buddy
            for window in self.chat_windows:
                if window.buddy.address == callback_data.address:
                    wx.CallAfter(window.Close)

    def onPrefs(self, evt):
        dialog = dlg_settings.Dialog(self)
        dialog.ShowModal()
    
    def onAddContact(self, evt):
        dialog = DlgEditContact(self, self)
        dialog.ShowModal()
    
    def onEditProfile(self, evt):
        dialog = DlgEditProfile(self, self)
        dialog.ShowModal()
    
    def onNewIdentity(self, evt):
        if not self.buddy_list.changeTorIdentity():
            wx.MessageBox(lang.D_WARN_CONTROL_CONNECTION_FAILED_MESSAGE, lang.D_WARN_CONTROL_CONNECTION_FAILED_TITLE)
    
    def onClose(self, evt):
        self.Show(False)
    
    def onQuit(self, evt):
        self.exitProgram();

    def exitProgram(self):
        w,h = self.GetSize()
        config.set("gui", "main_window_width", w)
        config.set("gui", "main_window_height", h)
        found_unread = False
        for window in self.chat_windows:
            if not window.IsShown() or window.unread:
                found_unread = True
                break

        if found_unread:
            answer = wx.MessageBox(lang.D_WARN_UNREAD_MESSAGE,
                                   lang.D_WARN_UNREAD_TITLE,
                                   wx.YES_NO|wx.NO_DEFAULT)

            if answer == wx.NO:
                return

        self.taskbar_icon.RemoveIcon()
        self.buddy_list.stopClient() #this will also stop portable Tor

        # All my threads wouldn't join properly. Don't know why.
        # sys.exit() would spew lots of tracebacks *sometimes*,
        # so let's do it the easy way and just kill ourself:
        config.killProcess(os.getpid())
    
    def onProfileUpdated(self):
        self.my_info.updateInfo()
        self.updateTitle()
        self.splitter.SetSashPosition(self.my_info.getSplitterHeight())
