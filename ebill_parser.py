from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import os.path
import quopri
import base64
import email
import re


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_PATH = 'protected/credentials.json'
TOKEN_PATH = 'protected/token.json'


class MailParser:
    def __init__(self, subject, date_split_symbol,
                 pattern_restaurant, pattern_date, pattern_cost):
        self.subject = subject
        self.date_split_symbol = date_split_symbol
        self.pattern_restaurant = pattern_restaurant
        self.pattern_date = pattern_date
        self.pattern_cost = pattern_cost
        # run
        self.since_date = input("Since which date until now? (YYYY/MM/DD): ")
        self.get_creds()
        self.build_and_retrive_info()
    
    def get_creds(self):
        """設置認證，從文件中讀取或要求用戶進行認證，並將結果保存。"""
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
        """
        該函式透過Gmail API建立連線，並透過指定的搜尋條件取得符合條件的信件，
        再進一步進行解析取得相關資訊。最後將解析出的資訊印出。
        """
        try:
            # Call the Gmail API
            service = build('gmail', 'v1', credentials=self.creds)
            query = f"subject:{self.subject} after:{self.since_date} "
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            if not messages:
                print('No messages found.')
                return
            for message in reversed(messages):
                self.msg = service.users().messages().get(
                    userId='me', id=message['id'], format='raw').execute()
                self.parse_and_decode()
        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f'An error occurred: {error}')

    def parse_and_decode(self):
        """解析郵件並將其解碼為純文本，然後使用正則表達式匹配並提取餐廳名稱、日期和金額。"""
        # Parse the raw message.
        mime_msg = email.message_from_bytes(base64.urlsafe_b64decode(self.msg['raw']))
        # Find full message body
        message_main_type = mime_msg.get_content_maintype()
        if message_main_type == 'multipart':
            for i, part in enumerate(mime_msg.get_payload()):                
                if part.get_content_maintype() == 'text':
                    self.convert_qp_regex_and_print(part.get_payload())
        elif message_main_type == 'text':
            self.convert_qp_regex_and_print(mime_msg.get_payload())

    def convert_qp_regex_and_print(self, string_to_convert):
        """將Quoted-Printable格式的字串解碼，去除標籤並以正則表達式擷取印出。"""
        bytes_to_convert = quopri.decodestring(string_to_convert.encode('utf-8'))
        decoded_string = bytes_to_convert.decode('utf-8')
        decoded_string = re.sub('<[^>]+>', '', decoded_string)
        self.regex_and_print(decoded_string)

    def regex_and_print(self, decoded_string):
        """以正則表達式從解碼後的字串中擷取餐廳名稱、日期和金額，並以特定格式輸出。"""
        # retaurant       
        match_restaurant = re.search(self.pattern_restaurant, decoded_string)
        restaurant = match_restaurant.group(1) if match_restaurant else ''
        # date
        match_date = re.search(self.pattern_date, decoded_string)
        date = match_date.group(0) if match_date else ''
        year, month, day = date.split(self.date_split_symbol)
        formatted_date = f"{year}/{month.zfill(2)}/{day.zfill(2)}"
        # cost
        match_cost = re.search(self.pattern_cost, decoded_string)
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
            pattern_cost = "訂單總額\s+\$\s+(\d+)\.00",
            date_split_symbol = "-"
        )
    

if __name__ == '__main__':
    UbereatsMailParser()
    # FoodpandaMailParser()
