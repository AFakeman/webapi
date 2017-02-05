from webapi import WebApi

api = WebApi("config.json")

steam = api.Steam(api_key="6928F360E7EE0A667B41C09B2DE76930", kek=True)

print(steam.fetch_items(id="76561198005570610"))