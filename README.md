# Anki Notifications

This script parses [Anki Web](https://ankiweb.net/), checks for any unreviewed cards and sends you a teams notification if there are unreviewed cards.

## Setup

### Credentials and webhooks
You need to add two files: a `credentials.yaml` file and a `connections.yaml` file:

- `credentials.yaml` stores your anki login info and should be filled in like this
    ```
    username: <anki username (email)>
    password: <anki password>
    ```
- `connections.yaml` stores your teams webhook address - see [here](https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook) to learn how to set these up
    ```
    teams: <teams webhook>
    ```

by default the script will look for these files in the root of this folder but you can store them elsewhere and specify their location with the `--credentials` and `--connections` args:
```
python notify.py --credentials <path to credentials.yaml> --connections <path to connections.yaml>
```
Once you've set these files up you can check that your credentials and webhook are correct by running the script directly.

### The `--deck` option
You can use the `--deck` (`-d`) option to specify a particular anki deck to check against, e.g. if you have many decks and only want to be notified if one of them has unreviewed cards. If unspecified the script checks all decks.

## Automation (cron)
You can automate this script to run using cron if you are on linux, running `crontab -e` lets you edit your cron table and from there you can specify when you want the script to be run e.g.:

```
# m h  dom mon dow   command
0 17,20 * * * /home/<user>/.pyenv/bin/versions/3.10.3/bin/python3.10 /home/<user>/git/anki-notifications/notify.py -d All &> /tmp/anki-notifications.log
```
This will run the script at 5pm and 8pm every day. Note you need to include the full python path if using a particular version (cron does not run in an interactive shell so does not have access to your env variables). The redirect to a log file also prevents cron from emailing you when the command is run.
