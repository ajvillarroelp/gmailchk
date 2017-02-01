#!/usr/bin/python
import os
import signal
import sys
import subprocess

from gi.repository import Gtk, Gio,GLib, GObject
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify

BaseDir = os.environ['HOME']+"/gmailchk"
BinDir = os.environ['HOME']+"/bin"
CONFFILE = BaseDir+"/config.ini"
READICON = BaseDir+"/geary.svg"
UNREADICON = BaseDir+"/unread.geary.png"
DAEMONPIDFILE = BaseDir+"/pid"
CHKINTERVAL = ""
APP = "GmailCheck"


def notif_msg(msg, iconpath):
    global APP
    global READICON
    n = Notify.Notification.new(APP, msg, READICON)
    n.show()


###########################################################
'''def cbk_turnoffmon(widget):
    global BaseDir
    os.system("bash "+BinDir+"/dualdisplayoff.sh")
'''

###########################################################


def cbk_settings(widget):
    global CHKINTERVAL
    print "Settings"

    dialog = Gtk.Dialog(title="Settings", buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
    vboxdiag = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.NONE)

    vboxdiag.pack_start(listbox, True, True, 0)

    row = Gtk.ListBoxRow()
    hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
    row.add(hbox1)

    label1 = Gtk.Label("Interval:", xalign=0)
    hbox1.pack_start(label1, True, True, 0)

    entry1 = Gtk.Entry()
    entry1.set_text(CHKINTERVAL)
    hbox1.pack_start(entry1, True, True, 0)

    listbox.add(row)
    box = dialog.get_content_area()
    box.add(vboxdiag)
    vboxdiag.show_all()

    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        _chkintv = entry1.get_text()
        # _coords=entry2.get_text()
        # _height=entry3.get_text()
        # _extscript=entry4.get_text()
        if _chkintv != "":
            CHKINTERVAL = _chkintv
            # coords=_coords
            # height=_height
            # extscript=_extscript
            f = open(CONFFILE, "w")
            f.write("checkinterval="+CHKINTERVAL+"\n")
            f.close()
        else:
            messagedialog = Gtk.MessageDialog(message_format="Error: One parameter is empty!\nTry again.")

            messagedialog.set_property("message-type", Gtk.MessageType.ERROR)
            messagedialog.add_button("OK", Gtk.ButtonsType.OK)

            messagedialog.run()
            messagedialog.destroy()
    dialog.destroy()

##########################################################


def cbk_quit(widget):

    # Get pid of the daemon and kill it
    try:
        f = open(DAEMONPIDFILE, "r")
        PID = f.read()
        f.close()
        PID.rstrip('\n')

        os.kill(int(PID), signal.SIGTERM)

        os.remove(DAEMONPIDFILE)
    except:
        print ""
    # sys.exit(0)
    Gtk.main_quit()


def sighand():
    try:
        f = open(DAEMONPIDFILE, "r")
        PID = f.read()
        f.close()
        PID.rstrip('\n')
        # print "AA "+PID+" -- "+DAEMONPIDFILE
        os.kill(int(PID), signal.SIGTERM)
        os.remove(DAEMONPIDFILE)
    except:
        print ""
    Gtk.main_quit()
    sys.exit(0)


def sigsetunreadicon():
    global win
    global BaseDir
    global ind
    print "Signal received change icon to unread .."
    ind.set_icon("unread.geary")


def sigreset():
    global win
    global BaseDir
    global ind

    print "Signal change to all read"
    ind.set_icon("geary")
    #notif_msg("GmailCheck", "Resetting to Unread!", "")
    os.system("python "+BaseDir+"/setasread.py")
    return True

##########################################################


debug = 0

# set the timeout handler
signal.signal(signal.SIGUSR1, sigreset)

# Read config
try:
    CHKINTERVAL = subprocess.check_output("grep checkinterval "+CONFFILE+" | cut -d= -f 2", shell=True)
except:
    CHKINTERVAL = "300"


###########################################
# Register app in the notification library
Notify.init(APP)

win = Gtk.Window()
win.set_icon_from_file(BaseDir+"/geary.svg")
ind = appindicator.Indicator.new("Gmail Check", "geary", appindicator.IndicatorCategory.APPLICATION_STATUS)
ind.set_icon_theme_path(BaseDir)
ind.set_status(appindicator.IndicatorStatus.ACTIVE)

menu = Gtk.Menu()
winmenu = Gtk.Menu()
displaymenu = Gtk.Menu()

#separator = Gtk.SeparatorMenuItem()

setting_item = Gtk.MenuItem("Settings")
setting_item.connect("activate", cbk_settings)

quit_item = Gtk.MenuItem("Quit")
quit_item.connect("activate", cbk_quit)

setting_item.show()
#separator.show()
quit_item.show()

#menu.append(separator)
menu.append(setting_item)
menu.append(quit_item)

ind.set_menu(menu)

win.connect("delete-event", Gtk.main_quit)

parentpid = os.getpid()

# start daemon checker
os.system("python "+BaseDir+"/gmailchk_daemon.py "+str(parentpid)+" &")
# print "python "+BaseDir+"/gmailchk_daemon.py "+str(PID)+" &"

# Install signal to change when unread messages
GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR1, sigsetunreadicon)

# Install signal to reset icon
GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR2, sigreset)

# Install signal to kill daemon at exit
GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGINT, sighand)
GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGTERM, sighand)

# Periodically reset the icon to all read
#id = GLib.timeout_add_seconds(120, sigreset)

Gtk.main()
