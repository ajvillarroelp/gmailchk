#  quickstart https://developers.google.com/gmail/api/quickstart/python
# 2.- bajar fichero client_id.json, que se indicara en la linea 22, con otro nombre para la app en la carpeta de la app
# 3.- ejecutar la primera vez y dar permiso a la app para la cuenta google
from __future__ import print_function
import httplib2
import os
import sys
import time
import signal
from gi.repository import Notify

from apiclient import discovery
from apiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

BaseDir = os.environ['HOME']+"/gmailchk"
BinDir = os.environ['HOME']+"/bin"
CONFFILE = BaseDir+"/config.ini"
DAEMONPIDFILE = BaseDir+"/pid"

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


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials_gmailchk')   # Directory to store credentials
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


def notif_msg(app, msg, iconpath):
    # os.system("notify-send -i "+icon+" Todo \""+msg+"\"")
    n = Notify.Notification.new(app, msg, iconpath)
    n.show()


def main():

    total = len(sys.argv)

    if total < 1:
        print ("error in params")
        sys.exit(2)

    parentpid = sys.argv[1]



    # Register app in the notification library
    Notify.init("GmailCheck")

    # Store pid
    PID = os.getpid()
    f = open(DAEMONPIDFILE, "w")
    f.write(str(PID))
    f.close()

    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    DEBUG = 1
    checkinterval = 60
    lastmsglist = ""
    whilecont = 1
    while (True):
        try:
            # get 5 latest unread messages
            if DEBUG == 1:
                print ("Checking email...\n")

            results = service.users().messages().list(userId='me', maxResults=5, q='is:unread', prettyPrint='true').execute()
            messlist = results.get('messages', [])

            if not messlist:
                print('No messages found.')
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
                if currmsglist != lastmsglist and whilecont > 1:
                    # new mail
                    notif_msg("GmailCheck", "New mail!", "")
                    os.kill(int(parentpid), signal.SIGUSR1)  # send signal to parent
                if whilecont == 1:
                    notif_msg("GmailCheck", "Latest: " + echomesg, "")

                lastmsglist = currmsglist
        except errors.HttpError, error:
            print ('An error occurred: %s' % error)
        whilecont = whilecont + 1
        time.sleep(checkinterval)


if __name__ == '__main__':
    main()
