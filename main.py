from webapi import WebApi

api = WebApi("config.json")

steam = api.classes["steam"](api_key="6928F360E7EE0A667B41C09B2DE76930")

steam.refresh_schema()

print(steam.schema())