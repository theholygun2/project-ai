from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os.path
from langchain_core.tools import tool

creds = None

SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/spreadsheets']
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

        

# Google Calendar API setup

calendar_service = build('calendar', "v3", credentials=creds)

# Google Sheets API setup
sheets_service = build('sheets', 'v4', credentials=creds)




# Google Calendar Tools
@tool
def create_event(summary: str, start_time: str, end_time: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new event in Google Calendar
    Args:
        summary: The title of the event
        start_time: The start time of the event in the format YYYY-MM-DDTHH:MM:SS-[timezone].
        end_time: The end time of the event in the format YYYY-MM-DDTHH:MM:SS-[timezone].
        description: The description of the event.
    """
    event = {
        'summary': summary,
        'description': description,
        'start': start_time,
        'end': end_time
    }
    event = calendar_service.events().insert(calendarId='primary', body=event).execute()
    return {"id": event["id"], "url": event["htmlLink"]}



@tool
def read_events(time_min: str, time_max: str) -> List[Dict[str, any]]:
    """
    Read events from Google Calendar within a specified time range.
    Use this function to retrieve event details including their IDs for potential updates or deletions.
    Args:
        time_min: The start time of the time range in the format YYYY-MM-DDTHH:MM:SS-[timezone].
        time_max: The end time of the time range in the format YYYY-MM-DDTHH:MM:SS-[timezone].
    """
    events_result = calendar_service.events().list(
        calendarId='primary', timeMin=time_min, timeMax=time_max,
        maxResults=10, singleEvents=True, orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return [{"id": event['id'], "summary": event['summary'], "start": event['start']['dateTime']} for event in events]



@tool
def update_event(event_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    # First retrieve the event from the API.

    """
    Update an existing event in Google Calendar.
    args:
    event_id: The ID of the event to update.
    updates: A dictionary of fields to update. For 'start' and 'end' fields, use the format:
        { "start:" { "dateTime": "YYYY-MM-DDTHH:MM:SS-[timezone]" }, "end": { "datetime": "YYYY-MM-DDTHH:MM:SS-[timezone]" } }
        Other fields like 'summary' (title) can be  updated directly.
    """

    event = calendar_service.events().get(calendarId='primary', eventId='eventId').execute()
    for key, value in updates.items():
        event[key] = value
    updated_event = calendar_service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    return {"message": f"Event updated: {updated_event['htmlLink']}"}



@tool
def delete_event(event_id: str) -> Dict[str, str]:

    """
    Delete an event from Google Calendar.
    Args:
        event_id: The ID of the event to delete.
    """
    
    calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
    return {"message": f"Event {event_id} deleted"}





# Google Sheets Tools

SPREADSHEET_ID = "1nRsVpuv7l3xrwja28xjniZF_4wvm9vBn3-MNEffcnic"
SHEET_NAME = "Budget"
SHEET_ID = 0



@tool
def read_sheet(range_name: str) -> List[List[Any]]:
    """
    Read data from Google Sheets.
    Args:
        range_name: The range of cells to read in the format "A1:B2".
    """
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!{range_name}").execute()
    return result.get('values', [])



@tool
def update_sheet(range_name: str, values: List[List[Any]]) -> Dict[str, Any]:
    """
    Update cells / write cells in Google Sheets.

    """
    body = {'values': values}
    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!{range_name}",
        valueInputOption='USER_ENTERED', body=body).execute()
    return result.get('values', [])



@tool
def delete_row(row_index: int) -> Dict[str, str]:
    """
    Delete cells cells in Google Sheets.
    
    """
    request = {
        "deleteDimension": {
            "range": {
                "sheetId": SHEET_ID,
                "dimension": "ROWS",
                "startIndex": row_index - 1,
                "endIndex": row_index
            }
        }
    }

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID, body={"request": [request]}).execute()
    return ("message", f"Row {row_index} deleted")