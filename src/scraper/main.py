import requests


def start():
    print("Hello world!")
    r = requests.get("https://www.jobly.fi/tyopaikka/director-licensing-iot-2222448")
    print(r.content)
