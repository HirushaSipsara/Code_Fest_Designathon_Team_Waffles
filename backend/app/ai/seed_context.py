"""Few-shot context for a real provider; never an executable parser."""
SUPPORTED_ACTIONS = {"ac": ["set_temperature"], "light": ["set_level", "turn_on", "turn_off"], "curtain": ["set_level"], "tv": ["turn_on", "turn_off"], "lock": ["lock"]}
SUPPORTED_TRIGGER = "resident_arrives"
SUPPORTED_CONDITION = "time_after"
FEW_SHOT_EXAMPLES = [
    {"request": "When I arrive after 7 PM, set the living room AC to 24 degrees.", "condition": "19:00", "actions": [{"device_id": "ac", "action": "set_temperature", "value": 24}]},
    {"request": "When I arrive after 8 PM, turn on the bedside lamp.", "condition": "20:00", "actions": [{"device_id": "blight", "action": "turn_on"}]},
    {"request": "When I come home after 6 PM, dim the ceiling light to 40%.", "condition": "18:00", "actions": [{"device_id": "light", "action": "set_level", "value": 40}]},
    {"request": "When I arrive after 9 PM, close the bedroom curtains.", "condition": "21:00", "actions": [{"device_id": "bcurtain", "action": "set_level", "value": 0}]},
    {"request": "When I get home after 5 PM, turn on the TV.", "condition": "17:00", "actions": [{"device_id": "tv", "action": "turn_on"}]},
    {"request": "When I arrive after 7 PM, lock the front door.", "condition": "19:00", "actions": [{"device_id": "lock", "action": "lock"}]},
    {"request": "When I get home after 8 PM, set bedroom AC to 23 degrees.", "condition": "20:00", "actions": [{"device_id": "bac", "action": "set_temperature", "value": 23}]},
    {"request": "When I come back after 6 PM, set living room curtains halfway.", "condition": "18:00", "actions": [{"device_id": "curtain", "action": "set_level", "value": 50}]},
]
BEHAVIOUR_HISTORY = [("Mon", "AC manually turned on", "18:24"), ("Tue", "no matching event", None), ("Wed", "AC manually turned on", "18:33"), ("Thu", "AC manually turned on", "18:28"), ("Fri", "AC manually turned on", "18:36")]
