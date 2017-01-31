#!/usr/bin/python
import os
import signal
import sys

from gi.repository import Gtk, Gio,GLib, GObject
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify

BaseDir = os.environ['HOME']+"/gmailchk"
BinDir = os.environ['HOME']+"/bin"
CONFFILE = BaseDir+"/config.ini"
DAEMONPIDFILE = BaseDir+"/pid"


def notif_msg(app, msg, iconpath):
    # os.system("notify-send -i "+icon+" Todo \""+msg+"\"")
    n = Notify.Notification.new(app, msg, iconpath)
    n.show()


##########################################################
def cbk_reset(widget):
    global BaseDir
    global win

    notif_msg("GmailCheck", "Resetting to Unread!", "")
    win.set_icon_from_file(BaseDir+"/geary.svg")
    os.system("python "+BaseDir+"/setasread.py")


###########################################################
'''def cbk_turnoffmon(widget):
    global BaseDir
    os.system("bash "+BinDir+"/dualdisplayoff.sh")
'''

###########################################################


def cbk_settings(widget):
    print "Settings"

'''    dialog = Gtk.Dialog(title="Settings", buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
    vboxdiag = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.NONE)

    vboxdiag.pack_start(listbox, True, True, 0)

    row = Gtk.ListBoxRow()
    hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
    row.add(hbox1)

    label1 = Gtk.Label("White List:", xalign=0)
    hbox1.pack_start(label1, True, True, 0)

    entry1 = Gtk.Entry()
    entry1.set_text(whitelist)
    hbox1.pack_start(entry1, True, True, 0)

    listbox.add(row)

    row = Gtk.ListBoxRow()
    hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
    row.add(hbox2)

    label2 = Gtk.Label("X,Y origin: ", xalign=0)
    hbox2.pack_start(label2, True, True, 0)

    entry2 = Gtk.Entry()
    entry2.set_text(coords)
    hbox2.pack_start(entry2, True, True, 0)

    listbox.add(row)

    row = Gtk.ListBoxRow()
    hbox3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
    row.add(hbox3)

    label3 = Gtk.Label("Window Height: ", xalign=0)
    hbox3.pack_start(label3, True, True, 0)

    entry3 = Gtk.Entry()
    entry3.set_text(height)
    hbox3.pack_start(entry3, True, True, 0)

    listbox.add(row)

    row = Gtk.ListBoxRow()
    hbox4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
    row.add(hbox4)

    label4 = Gtk.Label("External Script: ", xalign=0)
    hbox4.pack_start(label4, True, True, 0)

    entry4 = Gtk.Entry()
    entry4.set_text(extscript)
    hbox4.pack_start(entry4, True, True, 0)

    listbox.add(row)

    box = dialog.get_content_area()
    box.add(vboxdiag)
    vboxdiag.show_all()

    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        _whitelist=entry1.get_text()
        _coords=entry2.get_text()
        _height=entry3.get_text()
        _extscript=entry4.get_text()
        if _whitelist!= "" and _coords!= "" and _height!="":
            whitelist=_whitelist
            coords=_coords
            height=_height
            extscript=_extscript
            f = open(CONFFILE,"w")
            f.write("whitelist="+_whitelist+"\n")
            f.write("coords="+_coords+"\n")
            f.write("height="+_height+"\n")
            f.write("extscript="+_extscript+"\n")
            f.close()
        else:
            messagedialog = Gtk.MessageDialog(message_format="Error: One parameter is empty!\nTry again.")

            messagedialog.set_property("message-type", Gtk.MessageType.ERROR)
            messagedialog.add_button("OK", Gtk.ButtonsType.OK)

            messagedialog.run()
            messagedialog.destroy()
    dialog.destroy()'''

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


def sighand(signum, frame):
    try:
        f = open(DAEMONPIDFILE, "r")
        PID = f.read()
        f.close()
        PID.rstrip('\n')
        print "AA "+PID+" -- "+DAEMONPIDFILE
        os.kill(int(PID), signal.SIGTERM)
    except:
        print ""
    Gtk.main_quit()
    sys.exit(0)


def signotify(signum, frame):
    global win
    global BaseDir
    print "Signalled.."
    win.set_icon_from_file(BaseDir+"/umread.geary.png")


def sigreset(signum, frame):
    global win
    global BaseDir

    notif_msg("GmailCheck", "Resetting to Unread!", "")
    win.set_icon_from_file(BaseDir+"/geary.svg")
    os.system("python "+BaseDir+"/setasread.py")

##########################################################


debug = 0

# set the timeout handler
signal.signal(signal.SIGALRM, sigreset)
signal.alarm(3600)

# Set the signal handler
signal.signal(signal.SIGUSR1, signotify)
signal.signal(signal.SIGTERM, sighand)
signal.signal(signal.SIGINT, sighand)


###########################################
# Register app in the notification library
Notify.init("GmailCheck")

win = Gtk.Window()
win.set_icon_from_file(BaseDir+"/geary.svg")
ind = appindicator.Indicator.new("Gmail Check", "geary", appindicator.IndicatorCategory.APPLICATION_STATUS)
ind.set_icon_theme_path(BaseDir)
ind.set_status(appindicator.IndicatorStatus.ACTIVE)

menu = Gtk.Menu()
winmenu = Gtk.Menu()
displaymenu = Gtk.Menu()

reset_item = Gtk.MenuItem("Reset Unreads")
reset_item.connect("activate", cbk_reset)

separator = Gtk.SeparatorMenuItem()

setting_item = Gtk.MenuItem("Settings")
setting_item.connect("activate", cbk_settings)

quit_item = Gtk.MenuItem("Quit")
quit_item.connect("activate", cbk_quit)

reset_item.show()
setting_item.show()
separator.show()
quit_item.show()

menu.append(reset_item)
menu.append(separator)
menu.append(setting_item)
menu.append(quit_item)

ind.set_menu(menu)

win.connect("delete-event", Gtk.main_quit)

parentpid = os.getpid()
os.system("python "+BaseDir+"/gmailchk_daemon.py "+str(parentpid)+" &")
# print "python "+BaseDir+"/gmailchk_daemon.py "+str(PID)+" &"
Gtk.main()
