#!/usr/bin/python
import httplib2

import os
import signal
import sys
import subprocess
import glob
import codecs
import threading
import time
import gi

from apiclient import discovery
from apiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from gi.repository import GLib
gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3 as appindicator
gi.require_version('Notify', '0.7')
from gi.repository import Notify

VERSION = "1.3"
BaseDir = os.environ['HOME'] + "/.gmailchk"
BinDir = os.environ['HOME'] + "/bin"
CONFFILE = BaseDir + "/config.ini"
READICON = BaseDir + "/geary.svg"
EMAILAPP = ""
UNREADICON = BaseDir + "/unread.geary.png"
DAEMONPIDFILE = BaseDir + "/pid"
DETAILSFILE = BaseDir + "/.details"
STATUSFILE = BaseDir + "/.status"
CHFLAG = False
CHKINTERVAL = ""
RESETINTERVAL = 10
APP = "GmailCheck"
MARGIN = 5
DEBUG = 1

GObject.threads_init()

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


def notif_msg(msg):
    global APP
    try:
        icon = BaseDir + "/geary.png"
        os.system("notify-send -i " + icon + " " + APP + " \"" + msg + "\"")
        # n = Notify.Notification.new("<b>" + APP + "</b>", msg, "geary")
        # n.show()
    except:
        print "error in notif_msg..."

###########################################################


def cbk_reset(widget):

    global ind
    print "Signal change to all read"
    ind.set_icon("geary")

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
    if len(detailsfile_list) == 0:
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
            f.write("checkinterval=" + CHKINTERVAL + "\n")
            f.write("emailapp=" + EMAILAPP + "\n")
            f.close()
        else:
            messagedialog = Gtk.MessageDialog(message_format="Error: One parameter is empty!\nTry again.")

            messagedialog.set_property("message-type", Gtk.MessageType.ERROR)
            messagedialog.add_button("OK", Gtk.ButtonsType.OK)

            messagedialog.run()
            messagedialog.destroy()
    dialog.destroy()

##########################################################


def cbk_about(widget):
    global VERSION
    aboutdialog = Gtk.AboutDialog()
    aboutdialog.set_name(APP)
    aboutdialog.set_version(VERSION)
    aboutdialog.set_comments("Simple gmail checker")
    aboutdialog.set_authors(["Antonio Villarroel"])
    aboutdialog.run()
    aboutdialog.destroy()


def cbk_quit(widget):
    # sys.exit(0)
    Gtk.main_quit()

###########################################################


def sighand():
    Gtk.main_quit()
    sys.exit(0)

###########################################################


def truncline(msg):
    limit = 40
    final = ""
    lista = msg.split("\n")
    for item in lista:
        if len(item) <= limit:
            final = final + item
        else:
            tmpitem = item
            while len(tmpitem) > limit:
                left = tmpitem[:limit]
                right = tmpitem[limit:]
                final = final + left + "\n"
                if len(right) <= limit:
                    final = final + right + "\n"
                    break
                tmpitem = right
        # print "AA ", final.encode('ASCII', "ignore")
    return final


def sigsetunreadicon(snippet):
    global ind
    global BaseDir
    global tag1_item
    global account_list

    print "Signal received change icon to unread .."
    ind.set_icon("unread.geary")

    tag1_item.set_label(truncline(snippet))
    tag1_item.show()

###########################################################


def sigreset():
    global ind

    print "Signal change to all read"

    ind.set_icon("geary")
    # os.system("python " + BaseDir + "/setasread.py")
    # setasread()


##########################################################################

def writedets(account, msg):
    global DETAILSFILE

    name = account.split('@')
    try:
        f = codecs.open(DETAILSFILE + "_" + name[0], "w", "utf-8")
        f.write("Account: " + account + "\n")
        f.write(msg)
        f.close()
    except:
        print ("Error writing " + DETAILSFILE + "_" + name[0] + " file!")


###########################################################
def chkemaildaemon():
    global DEBUG
    global EMAILAPP
    global ind
    global CHKINTERVAL
    global RESETINTERVAL
    global account_list

    # list to store the last emails ids for each account
    lastmsglist = {}
    whilecont = 1
    nothingcount = 0
    while (True):
        acc_count = 1
        if DEBUG == 1:
            print ("chkemaildaemon: going to check...")
        try:
            emailappstatus = subprocess.check_output("ps -ef | grep " + EMAILAPP + " | grep -v grep", shell=True)
            emailappstatus = emailappstatus.rstrip('\n')
        except:
            emailappstatus = ""

        iconname = ind.get_icon()
        if emailappstatus != "":
            if iconname == "geary":
                ind.set_icon("gearysleep")
            # Sleep if email app is running
            if DEBUG == 1:
                print ("chkemaildaemon: email app running, sleeping...")
            whilecont = whilecont + 1
            time.sleep(int(CHKINTERVAL))
            continue
        else:
            if iconname == "gearysleep":
                ind.set_icon("geary")

        for account in account_list:
            try:
                account_item = os.path.basename(account)
                credentials = get_credentials(account_item)
                http = credentials.authorize(httplib2.Http())
                service = discovery.build('gmail', 'v1', http=http)

                userdata = service.users().getProfile(userId='me').execute()
                accountname = userdata["emailAddress"]
                results = service.users().messages().list(userId='me', maxResults=1, q='is:unread', prettyPrint='true').execute()
                messlist = results.get('messages', [])

                # get latest unread message
                if DEBUG == 1:
                    # print (userdata)
                    print ("Checking email for account " + accountname + "...\n")

                if not messlist:
                    if DEBUG == 1:
                        print('Account ' + accountname + ': No messages found.')
                    nothingcount = nothingcount + 1
                else:
                    # print('Messages:')
                    currmsglist = ""
                    firstmesg = ""
                    snipmsg = ""
                    cont = 1
                    for messitem in messlist:
                        # print(messitem['id'])
                        if cont == 1:
                            message = service.users().messages().get(userId='me', id=messitem['id']).execute()
                            snipmsg = message['snippet']
                            firstmesg = message['snippet'] + "\nLink: https://mail.google.com/mail/u/0/#inbox/" + messitem['id']
                        currmsglist = currmsglist + messitem['id'] + "-"
                        cont = cont + 1
                        # print ('Message snippet: %s -- labels ' % message['labelIds'])
                        # msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
                    if whilecont == 1:
                        notif_msg("Latest unread for " + accountname + ": " + firstmesg.encode('ASCII', "ignore"))

                        writedets(accountname, firstmesg)
                        # writestatusfile("allread")

                    elif currmsglist != lastmsglist[account_item] and whilecont > 1:
                        # new mail
                        if DEBUG == 1:
                            print ("New email for " + accountname + "!\n")
                        notif_msg("New mail for " + accountname)
                        writedets(accountname, firstmesg)
                        # writestatusfile("unread")
                        # change icon to unread messages
                        sigsetunreadicon(snipmsg)

                        nothingcount = 0
                    else:
                        nothingcount = nothingcount + 1
                        if nothingcount % RESETINTERVAL == 0:
                            if DEBUG == 1:
                                print ("Same emails ... sending signal to reset icon")
                            # writestatusfile("allread")
                            # change icon to unread messages
                            sigreset()

                    # lastmsglist = currmsglist
                    lastmsglist[account_item] = currmsglist
            except errors.HttpError, error:
                print ('An error occurred: %s' % error)

            acc_count = acc_count + 1
        whilecont = whilecont + 1
        time.sleep(int(CHKINTERVAL))


##########################################################

def CreateMsgLabels():
    """  Create object to update labels.
  Returns:
    A label update object."""
    return {'removeLabelIds': ['UNREAD'], 'addLabelIds': []}

##########################################################


def setasread():
    global BaseDir
    global account_list

    fecha = time.strftime("%Y:%m:%d")

    for account in account_list:
        try:
            account_item = os.path.basename(account)
            credentials = get_credentials(account_item)
            http = credentials.authorize(httplib2.Http())
            service = discovery.build('gmail', 'v1', http=http)

            results = service.users().messages().list(userId='me', q='is:unread after:' + fecha, prettyPrint='true').execute()
            messlist = results.get('messages', [])

            if not messlist:
                print('No messages found.')
            else:
                msg_labels = CreateMsgLabels()  # set unread as removed label

                for messitem in messlist:
                    # print(messitem['id'])
                    message = service.users().messages().get(userId='me', id=messitem['id']).execute()
                    # print ('Message snippet: %s ' % message['snippet'])
                    # print ('Message snippet: %s -- labels ' % message['labelIds'])
                    # msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
                    message = service.users().messages().modify(userId='me', id=messitem['id'], body=msg_labels).execute()
        except errors.HttpError, error:
            print ('An error occurred: %s' % error)

##########################################################
# MAIN

# set the timeout handler
# signal.signal(signal.SIGUSR1, sigreset)


account_list = glob.glob(os.environ['HOME'] + '/.credentials_gmailchk_acc*')

addaccountflag = 0
##########################################################
# Check arguments
total = len(sys.argv)

if total > 1:
    if sys.argv[1] == "--add_account":
        addaccountflag = 1
    elif sys.argv[1] == "--help":
        print "\nCommand line options\ngmailchk.py [--setup] [--add_account]"
        sys.exit(0)
    elif sys.argv[1] == "--setup":
        print "\nInstalling required files to ~/.gmailchk..."
        if not os.path.exists(BaseDir):
            os.makedirs(BaseDir)
        os.system("cp geary.svg " + BaseDir)
        os.system("cp geary.svg ~/.icons")
        os.system("cp *.png " + BaseDir)
        os.system("cp config.ini " + BaseDir)
        #os.system("bash setlinks.sh")
        os.system("cp client_secret_gmailchkclient.json " + BaseDir)
        print "Finished.\nNow run python gmailchk.py --add_account\n"
        sys.exit(0)

    # empty the argument list for the gmail api
    del sys.argv[1:]

# Check that email accounts had been setup
account_list = glob.glob(os.environ['HOME'] + '/.credentials_gmailchk_acc*')

if len(account_list) == 0:
    print ("No accounts defined. Aborting. Run python gmailchk.py --add_account")
    notif_msg("No accounts defined. Aborting...")
    sys.exit(2)

##########################################################
# Read config
try:
    CHKINTERVAL = subprocess.check_output("grep checkinterval " + CONFFILE + " | cut -d= -f 2", shell=True)
    CHKINTERVAL = CHKINTERVAL.rstrip('\n')
except:
    CHKINTERVAL = "300"

try:
    EMAILAPP = subprocess.check_output("grep emailapp " + CONFFILE + " | cut -d= -f 2", shell=True)
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
    credentials = get_credentials(".credentials_gmailchk_acc" + str(nextacc))
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    print "\nAccount created! To delete it remove the entire directory ~/.credentials_gmailchk_acc" + str(nextacc)
    sys.exit(0)

###########################################
# Register app in the notification library
Notify.init(APP)

win = Gtk.Window()
win.set_icon_from_file(BaseDir + "/geary.svg")
ind = appindicator.Indicator.new("Gmail Check", "geary", appindicator.IndicatorCategory.APPLICATION_STATUS)
ind.set_icon_theme_path(BaseDir)
ind.set_status(appindicator.IndicatorStatus.ACTIVE)

menu = Gtk.Menu()


separator = Gtk.SeparatorMenuItem()

setting_item = Gtk.MenuItem("Settings")
setting_item.connect("activate", cbk_settings)

about_item = Gtk.MenuItem("About")
about_item.connect("activate", cbk_about)

quit_item = Gtk.MenuItem("Quit")
quit_item.connect("activate", cbk_quit)

tag1_item = Gtk.MenuItem("")
tag1_item.connect("activate", cbk_reset)
# details_item.show()

setting_item.show()
separator.show()
about_item.show()
quit_item.show()

menu.append(setting_item)
menu.append(separator)
menu.append(about_item)
menu.append(quit_item)
menu.append(separator)
menu.append(tag1_item)
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
# id = GLib.timeout_add_seconds(10, chkdaemon)

# threading.Thread(target=chkdaemon).start()
d = threading.Thread(target=chkemaildaemon, name='Daemon')
d.setDaemon(True)
d.start()

# start daemon checker
# os.system("python " + BaseDir + "/gmailchk_daemon.py " + str(parentpid) + " &")
# print "python "+BaseDir+"/gmailchk_daemon.py "+str(PID)+" &"

Gtk.main()
