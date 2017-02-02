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
import gi
from gi.repository import Notify

from apiclient import discovery
from apiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

gi.require_version('Notify', '0.7')

BaseDir = os.environ['HOME']+"/gmailchk_accountsupport"
BinDir = os.environ['HOME']+"/bin"
CONFFILE = BaseDir+"/config.ini"
DAEMONPIDFILE = BaseDir+"/pid"
CHKINTERVAL = ""
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


def CreateMsgLabels():
    """  Create object to update labels.
  Returns:
    A label update object."""
    return {'removeLabelIds': ['UNREAD'], 'addLabelIds': []}


def notif_msg(msg):
    global APP
    n = Notify.Notification.new(APP, msg, "geary")
    n.show()


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

    # Store pid
    PID = os.getpid()
    f = open(DAEMONPIDFILE, "w")
    f.write(str(PID))
    f.close()

    # lastmsglist = ""
    # list to store the last emails ids for each account
    lastmsglist = {}
    whilecont = 1
    nothingcount = 0
    while (True):
        acc_count = 1
        for account in account_list:
            try:
                account_item = os.path.basename(account)
                credentials = get_credentials(account_item)
                http = credentials.authorize(httplib2.Http())
                service = discovery.build('gmail', 'v1', http=http)

                # get 5 latest unread messages
                if DEBUG == 1:
                    print ("Checking email for account ", acc_count, "...\n")

                results = service.users().messages().list(userId='me', maxResults=5, q='is:unread', prettyPrint='true').execute()
                messlist = results.get('messages', [])

                if not messlist:
                    if DEBUG == 1:
                        print('Account '+str(acc_count)+': No messages found.')
                    nothingcount = nothingcount + 1
                else:
                    # print('Messages:')
                    currmsglist = ""
                    echomesg = ""
                    cont = 1
                    for messitem in messlist:
                        # print(messitem['id'])
                        if cont == 1:
                            message = service.users().messages().get(userId='me', id=messitem['id']).execute()
                            echomesg = message['snippet']
                        currmsglist = currmsglist+messitem['id']+"-"
                        cont = cont + 1
                        # print ('Message snippet: %s -- labels ' % message['labelIds'])
                        # msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
                    if whilecont == 1:
                        notif_msg("Latest: " + echomesg)

                    elif currmsglist != lastmsglist[account_item] and whilecont > 1:
                        # new mail
                        if DEBUG == 1:
                            print ("New email!\n")
                        notif_msg("New mail!")
                        os.kill(int(parentpid), signal.SIGUSR1)  # send signal to parent to put unread icon
                        nothingcount = 0
                    else:
                        nothingcount = nothingcount + 1
                        if nothingcount % 5 == 0:
                            if DEBUG == 1:
                                print ("Same emails ... sending signal to reset icon")
                            os.kill(int(parentpid), signal.SIGUSR2)  # send signal to reset icon

                    # lastmsglist = currmsglist
                    lastmsglist[account_item] = currmsglist
            except errors.HttpError, error:
                print ('An error occurred: %s' % error)

            acc_count = acc_count + 1
        whilecont = whilecont + 1
        time.sleep(int(CHKINTERVAL))


if __name__ == '__main__':
    main()
