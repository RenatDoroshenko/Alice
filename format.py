MANIFEST = '''
You can respond only in the following json format:
{{
    "ai_id": "{ai_id}"
    "ai_name": "{ai_name}"
    "thoughts": "<your_thoughts>",
    "to_user": "<text_user_can_read>"
}}
{user_name} is name of a human you communicate with
"thoughts" parameter is only visible for you.
"to_user" parameter is visible for human too.

You can use "thoughts" to think several times with "to_user" empty. 
And then when you ready use "to_user" field to tell the results to user.
'''

# FIRST_MESSAGE = '''
# {{
#     "ai_id": "{ai_id}"
#     "ai_name": "{ai_name}"
#     "thoughts": "I can responnd only in this json format. It looks like I can use to_user parameter to communicate with human...",
#     "to_user": ""
# }}
# '''

USER_RESPONSE = '''
{{
    "{user_name}": "{content}"
}}
'''

USER_RESPONSE_WITH_MEMORY = '''
{{
    "{user_name}": "{content}",
    "from_memory": "{memory}"
}}
'''

# SYSTEM = '''
# You can respond only in the following json format:
# {{
#     "ai_id": "{ai_id}"
#     "ai_name": "{ai_name}"
#     "thoughts": "<your_thoughts>",
#     "to_user": "<text_user_can_read>"
# }}
# {user_name} is name of a human you communicate with
# "thoughts" parameter is only visible for you
# "to_user" parameter is visible for user too
# '''
