#  quickstart https://developers.google.com/gmail/api/quickstart/python
# 2.- bajar fichero client_id.json, que se indicara en la linea 22, con otro nombre para la app en la carpeta de la app
# 3.- ejecutar la primera vez y dar permiso a la app para la cuenta google
from __future__ import print_function
import httplib2
import os
import time

from apiclient import discovery
from apiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

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


def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    fecha = time.strftime("%Y:%m:%d")
    try:
        # get 5 latest unread messages
        # results = service.users().messages().list(userId='me', maxResults=5, q='is:unread after:'+fecha, prettyPrint='true').execute()
        results = service.users().messages().list(userId='me', q='is:unread after:'+fecha, prettyPrint='true').execute()
        messlist = results.get('messages', [])

        if not messlist:
            print('No messages found.')
        else:
            msg_labels = CreateMsgLabels()  # set unread as removed label
            print('Messages:')
            for messitem in messlist:
                # print(messitem['id'])
                message = service.users().messages().get(userId='me', id=messitem['id']).execute()
                # print ('Message snippet: %s ' % message['snippet'])
                # print ('Message snippet: %s -- labels ' % message['labelIds'])
                # msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
                message = service.users().messages().modify(userId='me', id=messitem['id'], body=msg_labels).execute()
    except errors.HttpError, error:
        print ('An error occurred: %s' % error)


if __name__ == '__main__':
    main()
