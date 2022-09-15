import requests
from bs4 import BeautifulSoup
import argparse
import os
import yaml

ANKI_LOGIN_URL = "https://ankiweb.net/account/login"
ANKI_MAIN_URL = "https://ankiweb.net/decks/"
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DEFAULT_CREDENTIALS_FILE = os.path.join(DIR_PATH, "credentials.yaml")
DEFAULT_CONNECTIONS_FILE = os.path.join(DIR_PATH, "connections.yaml")
TIMEOUT = 60


def load_yaml(fh):
    data = yaml.safe_load(fh)
    if data is None or len(data) == 0:
        raise ValueError(f"{fh.name} is empty - please fill in tokens / credentials")
    return data


def get_token(page):
    soup = BeautifulSoup(page.text, "html.parser")
    token_box = soup.find("input", attrs={"name": "csrf_token"})
    token = token_box.get("value")
    return token


def get_payload(credentials_file):
    values = {
        "submitted": "1",
        "csrf_token": "",
    }
    creds = load_yaml(credentials_file)
    values.update(creds)
    return values


def teams_notify(webhook, results):
    facts = [{"name": deck, "value": str(os)} for deck, os in results.items()]
    payload = {
        "summary": "You have unreviewed Anki cards!",
        "text": "Anki reminder - you have unreviewed cards!",
        "sections": [
            {
                "activitySubtitle": "Breakdown by deck",
                "facts": facts,
            }
        ],
    }

    headers = {"Content-Type": "application/json"}
    r = requests.post(
        webhook,
        json=payload,
        headers=headers,
        timeout=TIMEOUT,
    )

    if not (r.status_code == requests.codes.ok and r.text == "1"):
        raise ValueError(r.text)


def get_num_outstanding_reviews(credentials):

    with requests.Session() as s:
        values = get_payload(credentials)
        # Set Token and post login credentials
        page = s.get(ANKI_LOGIN_URL)
        values["csrf_token"] = get_token(page)
        s.post(
            ANKI_LOGIN_URL,
            data=values,
        )
        decks_page = s.get(ANKI_MAIN_URL)
        if (decks_page.status_code != 200) or ("decks" not in decks_page.url):
            raise ValueError(f"Failed to login to ankiweb: status code: {decks_page.status_code}")

    # Parse the page for oustanding cards, create results dictionary
    # with {deck_name: outstanding_cards} format
    soup = BeautifulSoup(decks_page.content, "html.parser")
    n_reviews = [int(i.text.strip()) for i in soup.find_all("div", {"class": "deckDueNumber"})]
    deck_names = [i.get("data-full") for i in soup.find_all("button", {"class": "pl-0"})]
    results = {dn: (n_reviews[2 * i] + n_reviews[2 * i + 1]) for i, dn in enumerate(deck_names)}
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="script to parse anki web for outstanding reviews and send teams notification if there are any"
    )
    parser.add_argument(
        "--credentials",
        "-c",
        default=DEFAULT_CREDENTIALS_FILE,
        type=argparse.FileType("r"),
        help="path to credentials.yaml",
    )
    parser.add_argument(
        "--connections",
        "-w",
        default=DEFAULT_CONNECTIONS_FILE,
        type=argparse.FileType("r"),
        help="path to connections.yaml",
    )
    parser.add_argument(
        "--deck",
        "-d",
        default=None,
        type=str,
        help="If specified only notify if deck with that name has pending reviews",
    )
    args = parser.parse_args()
    results = get_num_outstanding_reviews(args.credentials)
    notify = (args.deck is not None and results[args.deck] > 0) or (args.deck is None and sum(results.values()) > 0)
    hooks = load_yaml(args.connections)
    if notify:
        teams_notify(hooks["teams"], results)
