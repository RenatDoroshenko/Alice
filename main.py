# main.py
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import model
import settings
import secure_information
import json
import memory
# from flask_session import Session

# Import your models and database instance
import database

# Custom filter function


def from_json_filter(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    else:
        return value


# Specify the template folder explicitly
template_dir = os.path.abspath('templates')
app = Flask(__name__, template_folder=template_dir)
# Register custom filter
app.jinja_env.filters['from_json'] = from_json_filter
app.secret_key = settings.SECRET_KEY

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///mydb.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration
# app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SESSION_FILE_DIR'] = os.path.abspath('flask_session')
# app.config['SESSION_PERMANENT'] = False
# Session(app)

# Initialize the database with the app
database.db.init_app(app)

with app.app_context():
    database.db.create_all()

# Load memory index
memory_index, metadata = memory.load_memory_index()

response_option_global = settings.DEFAULT_COMMUNICATION_MODE


@app.template_filter('tojson')
def tojson_filter(obj, indent=None):
    return json.dumps(obj, indent=indent)


@app.route('/', methods=['GET', 'POST'])
def chat():

    global response_option_global

    ai_id = secure_information.AI_ID
    selected_experience_space = int(request.form.get(
        'experience_space', session.get('experience_space', settings.DEFAULT_EXPERIENCE_SPACE)))

    diagnostic = is_diagnostic_mode()

    messages, ai_id, ai_name = model.get_context_messages_with_manifest(ai_id=ai_id,
                                                                        experience_space=selected_experience_space,
                                                                        memories_only_for_context=True,
                                                                        diagnostic=diagnostic)

    if 'usage' not in session:
        set_default_usage(0, 0, 0)

    all_experience_spaces = database.get_all_experience_spaces(
        session.get('ai_id', ai_id))
    highest_experience_space = max(all_experience_spaces, default=1)

    return render_template('chat.html',
                           initial_messages=messages,
                           prompt_tokens=session["usage"].get(
                               'prompt_tokens', 0),
                           completion_tokens=session["usage"].get(
                               'completion_tokens', 0),
                           total_tokens=session["usage"].get(
                               'total_tokens', 0),
                           experience_space=session.get(
                               'experience_space', settings.DEFAULT_EXPERIENCE_SPACE),
                           all_experience_spaces=all_experience_spaces,
                           highest_experience_space=highest_experience_space,
                           ai_id=session.get(
                               'ai_id', secure_information.AI_ID),
                           ai_name=session.get(
                               'ai_name', secure_information.AI_NAME),
                           response_option=response_option_global)


# Select experience space
@app.route('/change_experience_space', methods=['POST'])
def change_experience_space():

    # reset the usage
    # set_default_usage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    ai_id = secure_information.AI_ID
    selected_experience_space = int(request.form.get('experience_space'))
    print("Selected experience space:",
          selected_experience_space)
    diagnostic = is_diagnostic_mode()

    messages, ai_id, ai_name = model.get_context_messages_with_manifest(ai_id=ai_id,
                                                                        experience_space=selected_experience_space,
                                                                        memories_for_all_messages=True,
                                                                        diagnostic=diagnostic)

    usage = session['usage']
    session['experience_space'] = selected_experience_space

    all_experience_spaces = database.get_all_experience_spaces(
        session.get('ai_id', ai_id))

    if len(all_experience_spaces) == 0:
        all_experience_spaces = [1]
    else:
        all_experience_spaces.sort()

    return jsonify(messages=messages, usage=usage, all_experience_spaces=all_experience_spaces)


@app.route('/send_user_message', methods=['POST'])
def send_user_message():
    ai_id = secure_information.AI_ID
    selected_experience_space = request.form.get(
        'experience_space', settings.DEFAULT_EXPERIENCE_SPACE, type=int)
    diagnostic = is_diagnostic_mode()

    user_message = request.form.get('user_message')

    messages, ai_id, ai_name = model.get_context_messages_with_manifest(ai_id=ai_id,
                                                                        experience_space=selected_experience_space,
                                                                        memories_only_for_context=True,
                                                                        messages_with_memory_showed_to_ai=settings.MESSAGES_WITH_MEMORY_SHOWED_TO_AI-1,
                                                                        diagnostic=diagnostic)

    # Process the user message and generate the model's response
    response, response_message = model.user_say_to_model(user_name=secure_information.USER_NAME,
                                                         user_message=user_message,
                                                         messages=messages,
                                                         experience_space=selected_experience_space,
                                                         memory_index=memory_index,
                                                         metadata=metadata,
                                                         diagnostic=diagnostic)

    # Save changes made to memory index
    if settings.LONG_MEMORY_ENABLED and not diagnostic:
        memory.save_memory_index(memory_index, metadata)

    update_session_objects(response, selected_experience_space)

    usage = session['usage']

    messages, _, _ = model.get_context_messages_from_db(ai_id=ai_id,
                                                        experience_space=selected_experience_space,
                                                        messages_number=2,
                                                        diagnostic=diagnostic)
    user_message = messages[0]
    assistant_message = messages[1]

    send_model_message_again = should_model_think(assistant_message)

    return jsonify(user_message=user_message,
                   assistant_message=assistant_message,
                   usage=usage,
                   send_model_message_again=send_model_message_again)


@app.route('/generate_model_message', methods=['POST'])
def generate_model_message():

    ai_id = secure_information.AI_ID
    selected_experience_space = request.form.get(
        'experience_space', settings.DEFAULT_EXPERIENCE_SPACE, type=int)
    diagnostic = is_diagnostic_mode()

    messages, ai_id, ai_name = model.get_context_messages_with_manifest(ai_id=ai_id,
                                                                        experience_space=selected_experience_space,
                                                                        memories_only_for_context=True,
                                                                        diagnostic=diagnostic)

    # Generate the model's response
    response, response_message = model.model_say_to_model(messages=messages,
                                                          experience_space=selected_experience_space,
                                                          memory_index=memory_index,
                                                          metadata=metadata,
                                                          diagnostic=diagnostic)

    # Save changes made to memory index
    if settings.LONG_MEMORY_ENABLED and not diagnostic:
        memory.save_memory_index(memory_index, metadata)

    update_session_objects(response, selected_experience_space)

    usage = session['usage']

    messages, _, _ = model.get_context_messages_from_db(ai_id=ai_id,
                                                        experience_space=selected_experience_space,
                                                        messages_number=1,
                                                        diagnostic=diagnostic)

    send_model_message_again = should_model_think(messages[0])

    return jsonify(assistant_message=messages[0], usage=usage, send_model_message_again=send_model_message_again)


@app.route('/update_response_option', methods=['POST'])
def update_response_option():
    global response_option_global
    response_option = request.form.get('response_option')
    response_option_global = response_option
    print(f'response_option changed to "{response_option_global}"')
    return jsonify(success=True)


def should_model_think(message):
    global response_option_global

    print("Retrieved response_option_global from global:",
          response_option_global)

    send_model_message_again = False
    to_user = message['content']['to_user']

    # use selected model communication mode
    if response_option_global == 'thinking' and not bool(to_user):
        send_model_message_again = True
    elif response_option_global == 'continuous':
        send_model_message_again = True

    print('communication mode: ', response_option_global)
    print('to_user: ', to_user)
    print('send_model_message_again: ', send_model_message_again)

    return send_model_message_again


def is_diagnostic_mode():
    global response_option_global
    return response_option_global == 'diagnostic'


def set_default_usage(prompt_tokens, completion_tokens, total_tokens):
    session["usage"] = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens
    }


def update_session_objects(response, experience_space):

    session['usage'] = response.usage
    session['experience_space'] = experience_space

    session.modified = True


if __name__ == '__main__':
    app.run(debug=True)
