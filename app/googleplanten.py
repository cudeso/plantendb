from __future__ import print_function
import time

from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

import json
import sys

from app import app

class GooglePlanten():
    def __init__(self):
        self.DOCS_FILE_ID = app.config['DOCS_FILE_ID']
        self.SHEETS_FILE_ID = app.config['SHEETS_FILE_ID']
        self.SHEETS_RANGE = app.config['SHEETS_RANGE']
        self.TEMPLATE_PREFIX = app.config['TEMPLATE_PREFIX']
        self.IMAGE_SIZE = app.config['IMAGE_SIZE']
        self.CLIENT_ID_FILE = 'credentials.json'
        self.TOKEN_STORE_FILE = 'token.json'
        self.SCOPES = (  # iterable or space-delimited string
                'https://www.googleapis.com/auth/drive',
               # 'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/documents',
                'https://www.googleapis.com/auth/spreadsheets.readonly',
        )
        self.SOURCE = 'sheets' 

        self.HTTP = self.get_http_client()

        self.DRIVE = discovery.build('drive', 'v3', http=self.HTTP)
        self.DOCS = discovery.build('docs', 'v1', http=self.HTTP)
        self.SHEETS = discovery.build('sheets', 'v4', http=self.HTTP)


    def get_http_client(self):
        """Uses project credentials in CLIENT_ID_FILE along with requested OAuth2
            scopes for authorization, and caches API tokens in TOKEN_STORE_FILE.
        """
        self.store = file.Storage(self.TOKEN_STORE_FILE)
        self.creds = self.store.get()
        if not self.creds or self.creds.invalid:
            self.flow = client.flow_from_clientsecrets(self.CLIENT_ID_FILE, self.SCOPES)
            self.creds = tools.run_flow(self.flow, self.store)
        return self.creds.authorize(Http())


    def get_placeholder_image_index(self, documentid, placeholder):

        indexpos = False
        res = self.DOCS.documents().get(documentId=documentid, fields='').execute()
        for value in res.get('body').get('content'):
            if 'paragraph' in value:
                for el in value.get('paragraph').get('elements'):
                    if 'textRun' in el:
                        if placeholder in el.get('textRun').get('content'):
                            indexpos = el.get("startIndex")
                            break
        
        return indexpos


    def _copy_template(self, tmpl_id, source, service, template_extra_subject):
        """(private) Copies letter template document using Drive API then
            returns file ID of (new) copy.
        """
        body = {'name': '%s (%s)' % (self.TEMPLATE_PREFIX, template_extra_subject)}
        return service.files().copy(body=body, fileId=tmpl_id,
                fields='id').execute().get('id')


    def merge_template(self, plant, tmpl_id, source, service, template_extra_subject):
        """Copies template document and merges data into newly-minted copy then
            returns its file ID.
        """
        # copy template and set context data struct for merging template values
        copy_id = self._copy_template(tmpl_id, source, service, template_extra_subject)
        context = plant.iteritems() if hasattr({}, 'iteritems') else plant.items()

        # "search & replace" API requests for mail merge substitutions
        reqs = [{'replaceAllText': {
                    'containsText': {
                        'text': '{{%s}}' % key, 
                        'matchCase': True,
                    },
                    'replaceText': '%s' % str(value).strip(),
                }} for key, value in context]

        # send requests to Docs API to do actual merge
        self.DOCS.documents().batchUpdate(body={'requests': reqs},
                documentId=copy_id, fields='').execute()
        return copy_id


    def replace_placeholder_image(self, documentid, image, image_uc, indexpos):
        IMAGE_SIZE = 120

        # Add the image
        image = image.strip()
        image_uc = image_uc.strip()
        requests = [{
            'insertInlineImage': {
                'uri': '%s' % image_uc,
                'objectSize': {
                    'height': {
                        'magnitude': '%s' % IMAGE_SIZE,
                        'unit': 'PT'
                    }
                },
                'location': {
                    'index': '%s' % indexpos
                }

            }
        }] 
        #print(requests)
        #r = self.DOCS.documents().batchUpdate(body={'requests': requests}, documentId=documentid, fields='').execute()
        r = self.DOCS.documents().batchUpdate(body={'requests': requests}, 
                documentId=documentid).execute()
        time.sleep(4)
        #print(r)

        # Remove the placeholder text
        requests = [{'replaceAllText': {
            'containsText': {
                'text': '%s' % image, 
                'matchCase': True,
            },
            'replaceText': '',
        }}]
        self.DOCS.documents().batchUpdate(body={'requests': requests}, documentId=documentid, fields='').execute()    
        requests = [{'replaceAllText': {
            'containsText': {
                'text': ', ,'
            },
            'replaceText': '',
        }}]
        self.DOCS.documents().batchUpdate(body={'requests': requests}, documentId=documentid, fields='').execute()    


         
    def set_permissions_image(self, image):
        image_key = image.split("=")[1]
        filereqs = {
            'role': 'reader',
            'type': 'anyone'
        }
        #print("-- Update permissions file id %s " % image_key)
        a = self.DRIVE.permissions().create(fileId=image_key, body=filereqs).execute()
        print("Result of image permissions:", a)

    def update_sheet_last_editor(self):
        # Update the first cell, which makes us last editor
        # Required to set permissions correctly, otherwise we 
        # receive an error when replacing the placeholders with images
        range = 'A1:A1'
        data = self.SHEETS.spreadsheets().values().get(spreadsheetId=self.SHEETS_FILE_ID,        
            range=range).execute().get('values')
        
        body = {
            'values': data
        }
        result = self.SHEETS.spreadsheets().values().update(
            spreadsheetId=self.SHEETS_FILE_ID, range=range,
            valueInputOption='RAW', body=body).execute()
        print('Update sheet to correctly set last editors. {0} cells updated.'.format(result.get('updatedCells')))


    def get_sheets_data(self):
        """ Returns data from Google Sheets source.
        """
        data = self.SHEETS.spreadsheets().values().get(spreadsheetId=self.SHEETS_FILE_ID,
                range=self.SHEETS_RANGE).execute().get('values')[1:]
        
        merge = {
            'id': None,
            'timestamp': None,
            'plantnaamnl': None,
            'plantnaamlt': None,
            'foto': None,
            'soortplant': None,
            'hoogte': None,
            'bodemvereisten': None,
            'zonschaduw': None,
            'bloei': None,
            'bloeikleur': None,
            'bladvorm': None,
            'herfstverkleuring': None,
            'vermeerdering': None,
            'verzorging': None,
            'bijzonderheden': None,
            'stamtakken': None,
            'groeiwijze': None,
            'winterbeeld': None,
            'vruchten': None,
            'bodemvereistenopmerkingen': None
        }      
        COLUMNS = ['id','timestamp', 'plantnaamnl', 'soortplant', 'foto', 'plantnaamlt', 'hoogte', 'bodemvereisten', 'zonschaduw', 'bloei', 'bloeikleur', 'bladvorm', 'herfstverkleuring', 'vermeerdering', 'verzorging', 'bijzonderheden', 'stamtakken', 'groeiwijze', 'winterbeeld', 'vruchten', 'bodemvereistenopmerkingen' ]
        merged_data = []

        row_id = 1
        for row in data:
            row.insert(0, row_id)
            merged_data.append(dict(zip(COLUMNS, row)))
            row_id = row_id + 1

        merged_data = sorted(merged_data, key=lambda k:k['plantnaamlt'], reverse=False)

        return_merged_data = []
        
        for row in merged_data:
            for key in merge:
                if key not in row:
                    row[key] = ""
            return_merged_data.append(row)

        #print(return_merged_data)
        return return_merged_data


    def delete_fiches(self):
        results = self.DRIVE.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if items:
            print('Files:')
            for item in items:
                if self.TEMPLATE_PREFIX in item['name']:
                    self.DRIVE.files().delete(fileId=item['id']).execute()

