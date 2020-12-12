from __future__ import print_function
import pickle
import os.path
import tweepy
import twitter_config
from os import path
from time import sleep
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID of Northeastern's testing sheet and range of relevant data
SAMPLE_SPREADSHEET_ID = '1C8PDCqHB9DbUYbvrEMN2ZKyeDGAMAxdcNkmO2QSZJsE'
SAMPLE_RANGE_NAME = 'A:P'


def main():

    # Setup Google Sheet API
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    if path.isfile("current_length.txt"):
        with open("current_length.txt") as data:
            lines = data.readlines()
            current_length = int(lines[len(lines) - 1])
    else:
        current_length = 0

    # Setup Twitter API
    auth = tweepy.OAuthHandler(twitter_config.consumer_key, twitter_config.consumer_secret)
    auth.set_access_token(twitter_config.access_token, twitter_config.token_secret)
    twit_api = tweepy.API(auth)

    while True:
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])
        current_length_new = len(values)

        # Check if there's a new row of data
        if current_length_new != current_length:
            current_length = current_length_new
            num_positives = values[len(values) - 1][2]
            positive_rate = int(num_positives) / int(values[len(values) - 1][1]) * 100
            seven_day_positives = values[len(values) - 1][15]
            seven_day_positives_yesterday = values[len(values) - 2][15]
            seven_day_positives_difference = int(seven_day_positives) - int(seven_day_positives_yesterday)
            if seven_day_positives_difference > 0:
                seven_day_change = "(up " + str(abs(seven_day_positives_difference)) + " from yesterday)"
            elif seven_day_positives_difference < 0:
                seven_day_change = "(down " + str(abs(seven_day_positives_difference)) + " from yesterday)"
            else:
                seven_day_change = "(same as yesterday)"
            with open('current_length.txt', 'w+') as f:
                f.write(str(len(values)))
            date = values[len(values) - 1][0]
            status_update = "Northeastern University COVID Update for " + date + "\n" + \
                            "Positive Tests: " + num_positives + "\n" + \
                            "Seven-Day Positive Tests: " + str(seven_day_positives) + " " + seven_day_change + "\n" + \
                            "Positive Rate: " + str(round(positive_rate, 2)) + "%"
            twit_api.update_status(status_update)
            print(status_update)
            print("-----------")
        else:
            print("Nothing new!")
        sleep(5)


if __name__ == '__main__':
    main()
