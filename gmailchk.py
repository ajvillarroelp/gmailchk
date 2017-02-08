#!/usr/bin/python
import httplib2

import os
import signal
import sys
import subprocess
import glob
import codecs

from apiclient import discovery
from apiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import gi

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify

gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

BaseDir = os.environ['HOME']+"/.gmailchk"
BinDir = os.environ['HOME']+"/bin"
CONFFILE = BaseDir+"/config.ini"
READICON = BaseDir+"/geary.svg"
EMAILAPP = ""
UNREADICON = BaseDir+"/unread.geary.png"
DAEMONPIDFILE = BaseDir+"/pid"
DETAILSFILE = BaseDir+"/.details"
STATUSFILE = BaseDir+"/.status"
CHFLAG = False
CHKINTERVAL = ""
APP = "GmailCheck"
MARGIN = 5
DEBUG = 1

# GObject.threads_init()

###########################################################
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
#  AV client file in app base directory
CLIENT_SECRET_FILE = 'client_secret_gmailchkclient.json'
APPLICATION_NAME = 'GmailCheck'


def get_credentials(acc_dir):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    # Directory to store credentials
    # credential_dir = os.path.join(home_dir, '.credentials_gmailchk')
    credential_dir = os.path.join(home_dir, acc_dir)
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-gmailchk.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

###########################################################


def notif_msg(msg, iconpath):
    global APP
    global READICON
    n = Notify.Notification.new("<b>"+APP+"</b>", msg, READICON)
    n.show()


###########################################################


def cbk_details(widget):
    global ind

    print ("Details")
    # dialog = Gtk.Dialog(title="Details", buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
    dialog = Gtk.Dialog(title="Details", buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK))
    vboxdiag = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.set_size_request(600, 200)

    detailview = Gtk.TextView()

    detailview.set_border_window_size(Gtk.TextWindowType.LEFT, MARGIN)
    detailview.set_border_window_size(Gtk.TextWindowType.RIGHT, MARGIN)
    detailview.set_border_window_size(Gtk.TextWindowType.TOP, MARGIN)
    detailview.set_border_window_size(Gtk.TextWindowType.BOTTOM, MARGIN)

    detailview.set_wrap_mode(True)
    scroll.add(detailview)
    vboxdiag.pack_start(scroll, True, True, 0)

    detailsfile_list = glob.glob(BaseDir + '/.details*')
    if len(account_list) == 0:
        return False
    content = ""
    for fname in detailsfile_list:

        try:
            f = codecs.open(fname, "r", "utf-8")
            fcontent = f.read()
            f.close()
        except:
            print ""
        content = content + "\n" + fcontent + "\n"

    textbuffer = detailview.get_buffer()
    textbuffer.set_text(content)

    box = dialog.get_content_area()
    box.add(vboxdiag)
    vboxdiag.show_all()

    response = dialog.run()

    # Reset red icon to normal
    try:
        currstatus = subprocess.check_output("cat "+STATUSFILE, shell=True)
        currstatus = currstatus.rstrip('\n')
    except:
        currstatus = "allread"

    if currstatus != "allread":
        sigreset()

    dialog.destroy()
###########################################################


def cbk_settings(widget):
    global CHKINTERVAL
    global EMAILAPP
    print ("Settings")

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

    row = Gtk.ListBoxRow()
    hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
    row.add(hbox2)

    label2 = Gtk.Label("EmailApp:", xalign=0)
    hbox2.pack_start(label2, True, True, 0)

    entry2 = Gtk.Entry()
    entry2.set_text(EMAILAPP)
    hbox2.pack_start(entry2, True, True, 0)

    listbox.add(row)

    box = dialog.get_content_area()
    box.add(vboxdiag)
    vboxdiag.show_all()

    response = dialog.run()

    if response == Gtk.ResponseType.OK:
        _chkintv = entry1.get_text()
        _emailapp = entry2.get_text()
        # _coords=entry2.get_text()
        # _extscript=entry4.get_text()
        if _chkintv != "" and _emailapp != "":
            CHKINTERVAL = _chkintv
            EMAILAPP = _emailapp
            # coords=_coords
            # height=_height
            # extscript=_extscript
            f = open(CONFFILE, "w")
            f.write("checkinterval="+CHKINTERVAL+"\n")
            f.write("emailapp="+EMAILAPP+"\n")
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

###########################################################


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

###########################################################


def sigsetunreadicon():
    global win
    global BaseDir
    global ind
    global detmenu_item
    global details_item
    print "Signal received change icon to unread .."
    ind.set_icon("unread.geary")

    # Set tooltip to mail snippet
    detailsfile_list = glob.glob(BaseDir + '/.details*')
    content = ""
    for fname in detailsfile_list:
        try:
            f = codecs.open(fname, "r", "utf-8")
            fcontent = f.read()
            f.close()
        except:
            print ""
        content = content + "\n" + fcontent + "\n"
    detmenu_item.set_label(content)
    details_item.set_tooltip_text(content)
    # details_item.set_sensitive(True)


###########################################################

def sigreset():
    global win
    global BaseDir
    global ind
    global details_item

    print "Signal change to all read"

    ind.set_icon("geary")
    # notif_msg("GmailCheck", "Resetting to Unread!", "")
    os.system("python "+BaseDir+"/setasread.py")
    try:
        f = open(STATUSFILE, "w")
        f.write("allread")
        f.close()
    except:
        print ("Error writing allread to status file!\n")
    return True


###########################################################

def chkdaemon():
    global BaseDir
    global STATUSFILE
    global CHFLAG
    global ind

    # while True:
    if DEBUG == 1:
        print ("chkdaemon: going to check...")
    isUp = ""
    try:
        isUp = subprocess.check_output("ps -ef | grep gmailchk_daemon | grep -v grep | wc -l", shell=True)
        isUp = isUp.rstrip('\n')
    except:
        isUp = ""
    if isUp == "":
        notif_msg("Checking daemon is not running. Aborting...")
        # Abortando
        sighand()
# ---------------------------------------
    status = ""
    try:
        f = open(STATUSFILE, "r")
        status = f.read()
        f.close()
    except:
        print ("Error reading status file!\n")
        status = "allread"
    if DEBUG == 1:
        print ("chkdaemon: vars: ", status, CHFLAG)
    if status == "unread" and not CHFLAG:
        CHFLAG = True
        sigsetunreadicon()
    elif status == "allread" and CHFLAG:
        CHFLAG = False
        sigreset()

    iconname = ind.get_icon()
    if status == "sleep":
        if iconname == "geary":
            ind.set_icon("gearysleep")
    else:
        if iconname == "gearysleep":
            ind.set_icon("geary")

    return True
##########################################################
# MAIN

# set the timeout handler
# signal.signal(signal.SIGUSR1, sigreset)


account_list = glob.glob(os.environ['HOME']+'/.credentials_gmailchk_acc*')

addaccountflag = 0
##########################################################
# Check arguments
total = len(sys.argv)

if total > 1:
    if sys.argv[1] == "--add_account":
        addaccountflag = 1
    elif sys.argv[1] == "--setup":
        print "\nInstalling required files to ~/.gmailchk..."
        if not os.path.exists(BaseDir):
            os.makedirs(BaseDir)
        os.system("cp geary.svg "+BaseDir)
        os.system("cp geary.svg ~/.icons")
        os.system("cp unread.geary.png "+BaseDir)
        os.system("cp config.ini "+BaseDir)
        os.system("bash setlinks.sh")
        os.system("cp client_secret_gmailchkclient.json "+BaseDir)
        print "Finished.\nNow run python gmailchk.py --add_account\n"
        sys.exit(0)

    # empty the argument list for the gmail api
    del sys.argv[1:]

##########################################################
# Read config
try:
    CHKINTERVAL = subprocess.check_output("grep checkinterval "+CONFFILE+" | cut -d= -f 2", shell=True)
    CHKINTERVAL = CHKINTERVAL.rstrip('\n')
except:
    CHKINTERVAL = "300"

try:
    EMAILAPP = subprocess.check_output("grep emailapp "+CONFFILE+" | cut -d= -f 2", shell=True)
    EMAILAPP = EMAILAPP.rstrip('\n')
except:
    EMAILAPP = ""

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

###########################################
# first time create base account

if len(account_list) == 0 or addaccountflag == 1:
    nextacc = len(account_list) + 1
    credentials = get_credentials(".credentials_gmailchk_acc"+str(nextacc))
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    print "\nAccount created! To delete it remove the entire directory ~/.credentials_gmailchk_acc"+str(nextacc)
    sys.exit(0)

###########################################
# Register app in the notification library
Notify.init(APP)

win = Gtk.Window()
win.set_icon_from_file(BaseDir+"/geary.svg")
ind = appindicator.Indicator.new("Gmail Check", "geary", appindicator.IndicatorCategory.APPLICATION_STATUS)
ind.set_icon_theme_path(BaseDir)
ind.set_status(appindicator.IndicatorStatus.ACTIVE)

menu = Gtk.Menu()

details_item = Gtk.MenuItem("Latest Messages")
details_item.connect("activate", cbk_details)

separator = Gtk.SeparatorMenuItem()

setting_item = Gtk.MenuItem("Settings")
setting_item.connect("activate", cbk_settings)

quit_item = Gtk.MenuItem("Quit")
quit_item.connect("activate", cbk_quit)

details_item.show()

setting_item.show()
separator.show()
quit_item.show()

menu.append(details_item)
menu.append(setting_item)
menu.append(separator)
menu.append(quit_item)

ind.set_menu(menu)

win.connect("delete-event", Gtk.main_quit)

# Install signal to change when unread messages
# GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR1, sigsetunreadicon)

# Install signal to reset icon
# GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGUSR2, sigreset)

# Install signal to kill daemon at exit
GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGINT, sighand)
GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGTERM, sighand)

# Periodically reset the icon to all read
id = GLib.timeout_add_seconds(10, chkdaemon)

parentpid = os.getpid()

# start daemon checker
os.system("python "+BaseDir+"/gmailchk_daemon.py "+str(parentpid)+" &")
# print "python "+BaseDir+"/gmailchk_daemon.py "+str(PID)+" &"

Gtk.main()
