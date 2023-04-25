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

If you are not confident for sure or want to think more you can leave "to_user" parameter empty, and
use only "thoughts" field for thinking. When you ready you can give answer to user by writting "to_user" field.

"memories" parameter you don't need to write it - it's your memories from long-term memory.
If you do not remember something you can think about it with "thoughts" parameter and these memories
will be present in "memories" parameter.
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
    "memories": "{memory}"
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
