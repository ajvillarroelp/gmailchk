#  quickstart https://developers.google.com/gmail/api/quickstart/python
# 2.- bajar fichero client_id.json, que se indicara en la linea 22, con otro nombre para la app en la carpeta de la app
# 3.- ejecutar la primera vez y dar permiso a la app para la cuenta google
from __future__ import print_function
import httplib2
import os
import sys
import time
import signal
import glob
import subprocess
import codecs
import gi
from gi.repository import Notify

from apiclient import discovery
from apiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

gi.require_version('Notify', '0.7')

BaseDir = os.environ['HOME']+"/.gmailchk"
BinDir = os.environ['HOME']+"/bin"
CONFFILE = BaseDir+"/config.ini"
DAEMONPIDFILE = BaseDir+"/pid"
DETAILSFILE = BaseDir+"/.details"
STATUSFILE = BaseDir+"/.status"
CHKINTERVAL = ""
EMAILAPP = ""
RESETINTERVAL = 11
APP = "GmailCheck"
DEBUG = 1

'''try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
'''
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
#  AV client file in app base directory
CLIENT_SECRET_FILE = 'client_secret_gmailchkclient.json'
APPLICATION_NAME = 'GmailCheck'
flags = None


# def get_credentials():
def get_credentials(account_dir):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    # Directory to store credentials
    # credential_dir = os.path.join(home_dir, '.credentials_gmailchk')
    credential_dir = os.path.join(home_dir, account_dir)
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

##########################################################################


def CreateMsgLabels():
    """  Create object to update labels.
  Returns:
    A label update object."""
    return {'removeLabelIds': ['UNREAD'], 'addLabelIds': []}


##########################################################################

def notif_msg(msg):
    global APP
    # os.system("notify-send -i geary "+APP+" \""+msg+"\"")
    n = Notify.Notification.new("<b>"+APP+"</b>", msg, "geary")
    n.show()


##########################################################################

def writedets(account, msg):
    global DETAILSFILE

    name = account.split('@')
    try:
        f = codecs.open(DETAILSFILE+"_"+name[0], "w", "utf-8")
        f.write("Account: "+account+"\n")
        f.write(msg)
        f.close()
    except:
        print ("Error writing "+DETAILSFILE+"_"+name[0]+" file!")


##########################################################################

def writestatusfile(msg):
    global STATUSFILE

    try:
        f = open(STATUSFILE, "w")
        f.write(msg)
        f.close()
    except:
        print ("Error writing unread to status file!\n")

##########################################################################


def main():
    global flags

    total = len(sys.argv)

    if total < 1:
        print ("error in params")
        sys.exit(2)

    parentpid = sys.argv[1]

    # empty the argument list for the gmail api
    del sys.argv[1:]

    try:
        import argparse
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None

# Register app in the notification library
    Notify.init(APP)

###########################################
# Check existing accouts

    account_list = glob.glob(os.environ['HOME']+'/.credentials_gmailchk_acc*')

    if len(account_list) == 0:
        print ("No accounts defined. Aborting. Run python gmailchk.py")
        notif_msg("No accounts defined. Aborting...")
        sys.exit(2)

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


    # Store pid
    PID = os.getpid()
    f = open(DAEMONPIDFILE, "w")
    f.write(str(PID))
    f.close()

    try:
        os.remove(DETAILSFILE)
    except:
        print ("")

    # lastmsglist = ""
    # list to store the last emails ids for each account
    lastmsglist = {}
    whilecont = 1
    nothingcount = 0
    while (True):
        acc_count = 1
        try:
            emailappstatus = subprocess.check_output("ps -ef | grep "+EMAILAPP+" | grep -v grep", shell=True)
            emailappstatus = emailappstatus.rstrip('\n')
        except:
            emailappstatus = ""

        if emailappstatus != "":
            status = ""
            try:
                f = open(STATUSFILE, "r")
                status = f.read()
                f.close()
            except:
                print ("Error reading status file!\n")
            if status != "sleep":
                writestatusfile("sleep")

            whilecont = whilecont + 1
            time.sleep(int(CHKINTERVAL))

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

                # get 5 latest unread messages
                if DEBUG == 1:
                    # print (userdata)
                    print ("Checking email for account "+accountname+"...\n")

                if not messlist:
                    if DEBUG == 1:
                        print('Account '+accountname+': No messages found.')
                    nothingcount = nothingcount + 1
                else:
                    # print('Messages:')
                    currmsglist = ""
                    firstmesg = ""
                    cont = 1
                    for messitem in messlist:
                        # print(messitem['id'])
                        if cont == 1:
                            message = service.users().messages().get(userId='me', id=messitem['id']).execute()
                            firstmesg = message['snippet']+"\nLink: https://mail.google.com/mail/u/0/#inbox/"+messitem['id']
                        currmsglist = currmsglist+messitem['id']+"-"
                        cont = cont + 1
                        # print ('Message snippet: %s -- labels ' % message['labelIds'])
                        # msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
                    if whilecont == 1:
                        notif_msg("Latest unread for " + accountname + ": " + firstmesg.encode('ASCII', "ignore"))

                        writedets(accountname, firstmesg)

                        writestatusfile("allread")

                    elif currmsglist != lastmsglist[account_item] and whilecont > 1:
                        # new mail
                        if DEBUG == 1:
                            print ("New email for "+accountname+"!\n")
                        notif_msg("New mail for " + accountname)
                        writedets(accountname, firstmesg)
                        # os.kill(int(parentpid), signal.SIGUSR1)  # send signal to parent to put unread icon
                        writestatusfile("unread")
                        nothingcount = 0
                    else:
                        nothingcount = nothingcount + 1
                        if nothingcount % RESETINTERVAL == 0:
                            if DEBUG == 1:
                                print ("Same emails ... sending signal to reset icon")

                            # os.kill(int(parentpid), signal.SIGUSR2)  # send signal to reset icon
                            writestatusfile("allread")

                    # lastmsglist = currmsglist
                    lastmsglist[account_item] = currmsglist
            except errors.HttpError, error:
                print ('An error occurred: %s' % error)

            acc_count = acc_count + 1
        whilecont = whilecont + 1
        time.sleep(int(CHKINTERVAL))


if __name__ == '__main__':
    main()
