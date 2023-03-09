from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import os.path
# import quopri
import re


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_PATH = 'protected/credentials.json'
TOKEN_PATH = 'protected/token.json'


class MailParser:
    def __init__(self, subject, pattern_restaurant, pattern_date, 
                 pattern_cost, date_split_symbol):
        self.subject = subject
        self.pattern_restaurant = pattern_restaurant
        self.pattern_date = pattern_date
        self.pattern_cost = pattern_cost
        self.date_split_symbol = date_split_symbol
        # input and run
        self.after_date = input("after date: ")
        self.get_creds()
        self.build_and_retrive_info()
    
    def get_creds(self):
        """get creds for building service.
        """
        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(TOKEN_PATH):
            self.creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, SCOPES)
                self.creds = flow.run_local_server(port=0)
                flow.stop()
            # Save the credentials for the next run
            with open(TOKEN_PATH, 'w') as token:
                token.write(self.creds.to_json())

    def build_and_retrive_info(self):
        try:
            # Call the Gmail API
            service = build('gmail', 'v1', credentials=self.creds)
            query = f"subject:{self.subject} after:{self.after_date} "
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            if not messages:
                print('No messages found.')
                return
            for message in reversed(messages):
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                self.snippet = msg['snippet']
                # print(quopri.decodestring(str(msg['payload']['parts']['body']['data']).encode('utf-8')).decode('utf-8'))                
                self.parse_and_print()
        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f'An error occurred: {error}')

    def parse_and_print(self):
        # retaurant       
        match_restaurant = re.search(self.pattern_restaurant, self.snippet)
        restaurant = match_restaurant.group(1) if match_restaurant else ''
        # date
        match_date = re.search(self.pattern_date, self.snippet)
        date = match_date.group(0) if match_date else ''
        year, month, day = date.split(self.date_split_symbol)
        formatted_date = f"{year}/{month.zfill(2)}/{day.zfill(2)}"
        # cost
        match_cost = re.search(self.pattern_cost, self.snippet)
        cost = match_cost.group(1) if match_cost else ''
        # output
        print(f"{restaurant},{formatted_date},{cost}")
        

class UbereatsMailParser(MailParser):
    def __init__(self):
        super().__init__(
            subject= "透過 Uber Eats 系統送出的訂單",
            pattern_restaurant = "以下是您在(.+)訂購的電子明細。",
            pattern_date = "\d{4}/\d{1,2}/\d{1,2}",
            pattern_cost = "總計\$(\d+)\.00",
            date_split_symbol = "/"
        )


class FoodpandaMailParser(MailParser):
    def __init__(self):
        super().__init__(
            subject= "你的訂單已成功訂購",
            pattern_restaurant = "我們已收到您在 (.+) 下的訂單囉！",
            pattern_date = "\d{4}-\d{1,2}-\d{1,2}",
            pattern_cost = "訂單總額	$ \d+\.00",  # no cost info. in snippet!
            date_split_symbol = "-"
        )
    

if __name__ == '__main__':
    UbereatsMailParser()
    # FoodpandaMailParser()  # NOT COOL :(

