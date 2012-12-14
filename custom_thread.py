import wx
from wx.lib.pubsub import pub
import threading

# handle uncaught exception imports
import sys


class PlotThread(threading.Thread):
    def __init__(self, target, args):
        threading.Thread.__init__(self)
        self.tar = target
        self.args = args
        self.start()

    def run(self):
        try:
            output = self.tar(*self.args)  # threaded call
            wx.CallAfter(pub.sendMessage, "plot_update", ())
        except:
            wx.CallAfter(pub.sendMessage, "plot_error", ())


class UpdateThread(threading.Thread):
    def __init__(self, target, args, update=''):
        threading.Thread.__init__(self)
        self.update = update
        self.tar = target
        self.args = args
        self.start()

    def run(self):
        try:
            output = self.tar(*self.args)  # threaded call
            wx.CallAfter(pub.sendMessage, self.update, ())
        except:
            wx.CallAfter(pub.sendMessage, "update_after_error", (None,))


class RunThread(threading.Thread):
    def __init__(self, target, args, attr='', label='', label_text=''):
        threading.Thread.__init__(self)
        self.label = label
        self.label_text = label_text
        self.tar = target
        self.args = args
        self.attr = attr
        self.start()

    def run(self):
        try:
            output = self.tar(*self.args)  # threaded call

            # Only for loading files. Not for when running PrimerSeq.
            if self.attr and self.label and self.label_text:
                wx.CallAfter(pub.sendMessage, "update", ((self.attr, output), (self.label, self.label_text)))
            else:
                wx.CallAfter(pub.sendMessage, "update", (None,))  # need to make this call more elegant
        except:
            wx.CallAfter(pub.sendMessage, "update_after_error", (None,))  # need to make this call more elegant



class RunPrimerSeqThread(threading.Thread):
    def __init__(self, target, args, attr='', label='', label_text='', my_excepthook=None):
        threading.Thread.__init__(self)
        self.label = label
        self.label_text = label_text
        self.tar = target
        self.args = args
        self.attr = attr
        self.my_excepthook = my_excepthook
        self.start()

    def run(self):
        try:
            output = self.tar(*self.args)  # threaded call
            wx.CallAfter(pub.sendMessage, "update_after_run", (self.args[0]['output'],))  # need to make this call more elegant
        except:
            # if self.my_excepthook:
            wx.CallAfter(pub.sendMessage, "update_after_error", (None,))  # need to make this call more elegant
            # else:
            #    raise


