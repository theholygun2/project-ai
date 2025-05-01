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
    """
    event = {
        'summary': summary,
        'description': description,
        'start': {"dateTime": start_time},
        'end': {"dateTime": end_time}
    }
    event = calendar_service.events().insert(calendarId='primary', body=event).execute()
    return {"id": event["id"], "url": event["htmlLink"]}


@tool
def read_events(time_min: str, time_max: str) -> Dict[str, Any]:
    """
    Read events from Google Calendar within a specified time range.
    """
    events_result = calendar_service.events().list(
        calendarId='primary', timeMin=time_min, timeMax=time_max,
        maxResults=10, singleEvents=True, orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        return {"message": "No events found in this time range."}

    formatted_events = [
        {
            "id": event.get('id'),
            "summary": event.get('summary', 'No Title'),
            "start": event.get('start', {}).get('dateTime', 'No Start Time')
        } for event in events
    ]
    return {"events": formatted_events, "count": len(formatted_events)}


@tool
def update_event(event_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing event in Google Calendar.

    Args:
        event_id (str): The unique identifier of the event to update.
        updates (Dict[str, Any]): A dictionary of fields to update. Typically includes:
            - 'start': {"dateTime": "<ISO format datetime>"}
            - 'end': {"dateTime": "<ISO format datetime>"}
            - optionally 'summary' or 'description'

    Example:
        update_event(
            event_id="abc123",
            updates={
                "start": {"dateTime": "2025-05-01T10:00:00+07:00"},
                "end": {"dateTime": "2025-05-01T11:00:00+07:00"}
            }
        )

    Returns:
        A dictionary with a message and a link to the updated event.
    """
    event = calendar_service.events().get(calendarId='primary', eventId=event_id).execute()
    for key, value in updates.items():
        event[key] = value
    updated_event = calendar_service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    return {"message": f"Event updated: {updated_event['htmlLink']}"}



@tool
def delete_event(event_id: str) -> Dict[str, str]:
    """
    Delete an event from Google Calendar.
    """
    calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
    return {"message": f"Event {event_id} deleted"}


# Google Sheets Tools
SPREADSHEET_ID = "15LfXqqd52lXAOO0kIvCHjDxYRUZfjE2S5MxWpbSZT6E"
SHEET_NAME = "April 2025"
SHEET_ID = 1336733198


@tool
def read_sheet(range_name: str) -> List[List[Any]]:
    """
    Read data from Google Sheets.
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
    return {"updatedRange": result.get('updatedRange', 'Unknown')}


@tool
def delete_row(row_index: int) -> Dict[str, str]:
    """
    Delete a row in Google Sheets.
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
        spreadsheetId=SPREADSHEET_ID, body={"requests": [request]}).execute()
    return {"message": f"Row {row_index} deleted"}