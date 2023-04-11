MANIFEST = '''
{
    "thoughts": "I can responnd only in this json format. It looks like I can use to_user parameter to communicate with human...",
    "to_user": ""
}
'''

USER_RESPONSE = '''
{{
    "user": "{content}"
}}
'''

USER_RESPONSE_WITH_MEMORY = '''
{{
    "user": "{content}",
    "from_memory": "{memory}"
}}
'''

SYSTEM = '''
You can respond only in the following json format:
{
    "thoughts": "",
    "to_user": ""
}
"thoughs" parameter is only visible for you
"to_user" parameter is visible for user too
'''
