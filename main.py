#!/usr/bin/env python3

import os
from datetime import datetime

import urllib3
from gql import Client, gql, AIOHTTPTransport
from numpy.core import long
from rich.console import Console

urllib3.disable_warnings()

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTING_FILE = ROOT_DIR + "/setting.txt"

with open(ROOT_DIR + "/schema.graphql") as f:
    SCHEMA_STR = f.read()

console = Console()

query = gql('''
query getCurrentSeason($page: Int, $season: MediaSeason, $seasonYear: Int, $onList: Boolean) {
  Page(page: $page, perPage: 50) {
    media(season: $season, seasonYear: $seasonYear, onList: $onList) {
      id
      title {
        userPreferred
      }
      episodes
      nextAiringEpisode {
        airingAt
        episode
      }
    }
  }
}
''')


def epochtodate(epoch) -> str:
    return datetime.fromtimestamp(long(epoch)).strftime('%a (%d/%m) at %I:%M %p')


def readtokenfromfile():

    access_token = ""

    try:
        with open(SETTING_FILE, 'r') as file:
            try:
                access_token = file.readline()
            except:
                console.print("Couldn't read from file!", "Well this is awkward", ":flushed:")
    except:
        console.print("Couldn't open file!", "Don't worry everything is fine", ":exploding_head:")

    return access_token


def writetokentofile(access_token):
    with open(SETTING_FILE, 'a') as file:
        file.write(access_token)


def askfortoken() -> str:
    access_token = readtokenfromfile()
    if access_token:
        return access_token

    id = 3721
    url = "https://anilist.co/api/v2/oauth/authorize?client_id=" + str(id) + "&response_type=token"

    console.print("Welcome to [bold blue]NextUp[/bold blue]!")
    console.print("To get started you need to authorize the program")
    console.print("You can do so by heading over to " + url)
    console.print("After you have authorized the program copy & paste the token")
    access_token = console.input("Paste token right here: ")

    if len(access_token) > 100:
        writetokentofile(access_token)
    else:
        print("That is not a token :^/")
        return askfortoken()

    return access_token


def createtransport(access_token: str) -> AIOHTTPTransport:
    return AIOHTTPTransport(
        url='https://graphql.anilist.co',
        headers={
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    )


def setupclient(transport: AIOHTTPTransport) -> Client:
    return Client(
        transport=transport,
        schema=SCHEMA_STR
    )


def season(month: int):
    month = month + 1

    if month in [12, 1, 2]:
        return "WINTER"

    if month in [3, 4, 5]:
        return "SPRING"

    if month in [6, 7, 8]:
        return "SUMMER"

    if month in [9, 10, 11]:
        return "FALL"


def getcurrentseason(client: Client) -> dict:
    today = datetime.today()
    params = {
        "page": 1,
        "season": season(today.month),
        "seasonYear": today.year,
        "onList": True
    }

    return client.execute(query, variable_values=params)


def printresult(current_season: dict):
    media = list(
        map(
            lambda item: {
                'title': item['title']['userPreferred'],
                'airingAt': item['nextAiringEpisode']['airingAt'],
                'episode': item['nextAiringEpisode']['episode'] if item['nextAiringEpisode']['episode'] else "?",
                'episodes': item['episodes'] if item['episodes'] else "?",
            }, current_season['Page']['media']
        )
    )

    console.print("Here is your [bold blue]NextUp[/bold blue] schedule!")

    for item in sorted(media, key=lambda item: item['airingAt']):
        console.print("[bold blue]{}[/bold blue] episode {} of {} will air on {} ".format(item['title'],
                                                                                item['episode'],
                                                                                item['episodes'],
                                                                                epochtodate(item['airingAt'])))


def main():
    access_token = askfortoken()
    transport = createtransport(access_token)
    client = setupclient(transport)
    current_season = getcurrentseason(client)
    printresult(current_season)


if __name__ == "__main__":
    main()
