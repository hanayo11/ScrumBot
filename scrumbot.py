# ##############################
# Scrumbot will post the daily scrum to a channel
# Required permissions on Slack are (Bot scope)
# chat:write
# users:read
#
# PUBLIC Channels require the below
# channels.history
# channels:read
#
# PRIVATE Channels require the groups scope of the above
# groups:history
# groups:read
#
# This is assuming the Scrum format follows 
# 1. What you did yesterday
# 2. What you're doing today
# 3. Any blockers
# ##############################

import os
import logging
import time
import re
import sys
from datetime import date, datetime, timedelta
from argparse import ArgumentParser
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ##############################
# Handle Input here
# ##############################
parser = ArgumentParser()
parser.add_argument('-t','--token', type=str, help="Slack bot token")
parser.add_argument('-c','--channel', type=str, help="Channel id to print to")

# Checks for required parameters and raises error if not passed in
try:
    options = parser.parse_args()
except SystemExit as err:
    if err.code == 2: 
        parser.print_help()
    sys.exit(0)

# ##############################
# Common Slack Info
# ##############################
# Set to C028PJHLT42 as my own personal channel id for testing
channel_id = os.environ.get("CHANNEL_ID") if options.channel == None else options.channel
slackbot_token = os.environ.get("SLACK_BOT_TOKEN") if options.token == None else options.token
logger = logging.getLogger(__name__)

if (channel_id == None) or (slackbot_token == None):
    logger.error("ERROR: channel id and slack bot token must be set either through env variable, or as command line argument")
    sys.exit(1)

client = WebClient(token=slackbot_token)

# ##############################
# Scrum message here
# ##############################
current_date = date.today()
scrum_msg = "Scrum for " + current_date.strftime("%B %d, %Y")

# ##############################
# Function will print msg to slack channel
# ############################.##
def print_to_channel(channel: str, msg: str) -> None:
    """This will print a message to the desired slack channel"""
    try:
        client.chat_postMessage(channel=channel_id, text=msg)
    except SlackApiError as e:
        logger.error("Error posting message: {}".format(e))
        
# ##############################
# Get all users in a channel so we know who to bug
# ##############################
def get_users(channel_id: str) -> dict:
    """Get all users in a team"""
    try:
        result = client.conversations_members(channel=channel_id)
        users_id = result["members"]

        result = client.users_list()
        team_list = result["members"]
    except SlackApiError as e:
        logger.error("Error getting users: {}".format(e))
    
    channel_members = {}
    for user in team_list:
        if (user['id'] in users_id) and (user['is_bot'] == False):
            channel_members[user['id']] = user['profile']['real_name_normalized']

    return channel_members

# ##############################
# Get the thread id of the last scrum post
# ##############################
def get_last_scrum_thread(channel_id: str, scrum_msg: str) -> str:
    """Get thread id of the last scrum post by bot"""
    latest_range = datetime.now()
    latest_range_ts = time.mktime(latest_range.timetuple())
    oldest_range = datetime.now() - timedelta(hours=1)
    oldest_range_ts = time.mktime(oldest_range.timetuple())
    try:
        result = client.conversations_history(channel=channel_id, latest=latest_range_ts, oldest=oldest_range_ts)
        conversation_history = result["messages"]
    except SlackApiError as e:
        logger.error("Error getting thread ts {}".format(e))
    
    last_scrum_post = ""
    for post in conversation_history:
        if post['text'] == scrum_msg:
            last_scrum_post = post['ts']
            break
    return last_scrum_post

# ##############################
# Reply to thread with members who still have not responded to update
# ##############################
def followup_unreplied(channel_id: str, scrum_ts: str, users: dict) -> int:
    """Replies to last scrum post with a follow up"""
    try:
        count = 0
        chaser_text = ""
        for user in users:
            if users[user] == 0:
                count += 1
                chaser_text += f" <@{user}>"

        if count > 0:
            chaser_text += "\n You still have not posted your daily scrum update, please do so now"
            client.chat_postMessage(channel=channel_id, thread_ts=scrum_ts, text=chaser_text)
        else:
            chaser_text = "SUCCESS: All users have posted their daily status update!"
            client.chat_postMessage(channel=channel_id, thread_ts=scrum_ts, text=chaser_text)
    except SlackApiError as e:
        logger.error("Error posting to thread: {}".format(e))

    return count

# ##############################
# Get whoever has not replied with their status update
# ##############################
def check_unreplied(channel_id: str, scrum_ts: str, users: dict) -> dict:
    """Get whoever has not posted their scrum update"""
    try:
        results = client.conversations_replies(channel=channel_id, ts=scrum_ts)
        thread_replies = results["messages"]
    except SlackApiError as e:
        logger.error("Error retrieving replies from thread: {}".format(e))
    
    for msg in thread_replies:
        if msg['user'] in users:
            re_scrum = "1.(.*)\n2.(.*)\n3.(.*)"
            if re.search(re_scrum, msg['text']):
                users[msg['user']] = 1
    
    return users


if __name__ == "__main__": 
    # First we post the Scum post to the channel
    print_to_channel(channel_id, scrum_msg)

    # Sleep for a bit as it takes time for the data to be entered into the backend
    time.sleep(1)

    # Now we get the list of users by slack id in a channel
    list_of_users = get_users(channel_id)

    # Get the last scum post by the bot
    scrum_ts = get_last_scrum_thread(channel_id, scrum_msg)

    # Then we have the bot follow up with whoever didn't 
    # Post their update after a certain amount of time
    users_replied = {x:0 for x in list_of_users}
    counter = 3
    remaining_unreplied = len(users_replied)
    while counter > 0 and remaining_unreplied > 0:
        time.sleep(10)
        print("Checking for unreplied")
        users_replied = check_unreplied(channel_id, scrum_ts, users_replied)
        remaining_unreplied = followup_unreplied(channel_id, scrum_ts, users_replied)
        counter -= 1
