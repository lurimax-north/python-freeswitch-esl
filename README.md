### Subscribing to events
There are two ways to subscribe to to freeswitch events. You can provide either a single callback, 
or a list of callbacks

#### During initilisation of the connection
```
from python_freeswitch_esl connection import ESLClient
def my_event_handler(event)
    print(f"Event {event} happened!")

# Providing a single callback
conn = ESLClient("127.0.0.1, 8021, event_callbacks={Event.NOTIFY: my_event_handler})

# providing multiple callbacks
def my_other_event_handler(event):
    print("I also receive events")

conn = ESLClient("127.0.0.1", 8021, event_callbacks={Event.MODULE_LOAD: [my_event_handler, my_other_event_handler]})
```

#### Using the `add_event_callback` method
```
def my_event_handler(event):
    print(f"Received event: {event}")

conn = ESLCLient("127.0.0.1", 8021)
conn.add_event_callback(EVENT.NOTIFY, my_event_handler)
async for _ in conn.loop():
    continue
```

#### Manually iterating through the events()
```
def my_event_handler(event):
    print(f"Received event: {event}")

conn = ESLCLient("127.0.0.1", 8021)
async for event in conn.loop():
    if event.event == Event.CHANNEL_BRIDGE:
        my_event_handler(event)
```

### Sending commands

You can send any command using `send_message()`
```
conn = ESLClient("127.0.0.1", 8021)
conn.send_message("log 9")
```

For simple commands you can use the `api()` shortcut

```
conn = ESLClient("127.0.0.1", 8021)
con.api("status")
```