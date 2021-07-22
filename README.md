# ScrumBot

## Summary
Scrumbot for Slack to post the daily status, and then follows up with people over the course of the day to whoever has not given their status update.

The assumption is that Slack updates will be in the form of
1. What you did yesterday
2. What you're doing today
3. Any blockers

After posting the initial thread starting with `Scrum for <Today's date in mm/dd/yyy>`, it will sleep for an hour and follow up with whoever has not posted their daily status update after that time frame, it will repeat this 3 times.

If all users have given their status update, it will post a `SUCCESS` message.

## Usage

This can be run either manually or via container

### Manual Run

First set the `SLACK_BOT_TOKEN`  and `CHANNEL_ID` either in the env, or pass it in as a parameter.
```
export SLACK_BOT_TOKEN=<token>
export CHANNEL_ID=<CHANNEL ID>
```

Script usage is
```
python3 scrumbot.py [ -t/--token <token> ] [ -c/--channel <channel id> ]
```

So you could not set the env vars at all and pass them in through command line
```
python3 scrumbot.py -t <token> -c <channel id>
```

### Docker run

First build the image with the corresponding Dockerfile by first doing a `cd` into the repository location.
```
docker build -t scrum-bot .
```

Then execute the container as below
```
docker run --rm -e SLACK_BOT_TOKEN=<token> -e CHANNEL_ID=<channel id> -it scrum-bot 
```