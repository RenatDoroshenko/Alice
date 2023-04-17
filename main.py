# main.py
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import model
import settings
import secure_information
import json

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

# Initialize the database with the app
database.db.init_app(app)

with app.app_context():
    database.db.create_all()


@app.template_filter('tojson')
def tojson_filter(obj, indent=None):
    return json.dumps(obj, indent=indent)


# Main Root
# @app.route('/', methods=['GET', 'POST'])
# def chat():

#     ensure_session_objects()

#     if request.method == 'POST':
#         user_message = request.form.get('user_message')
#         generate_model_message = request.form.get('generate_model_message')
#         selected_experience_space = int(request.form.get('experience_space'))

#         if user_message:
#             response, response_message = model.user_say_to_model(secure_information.USER_NAME,
#                                                                  user_message, session['messages'],
#                                                                  experience_space=selected_experience_space)
#         elif generate_model_message:
#             response, response_message = model.model_say_to_model(session['messages'],
#                                                                   experience_space=selected_experience_space)

#         update_session_objects(response, response_message,
#                                selected_experience_space)

#     return render_template('chat.html',
#                            # here place messages - and values will be taken from db
#                            messages=session['messages'],
#                            prompt_tokens=session["usage"].get(
#                                'prompt_tokens', 0),
#                            completion_tokens=session["usage"].get(
#                                'completion_tokens', 0),
#                            total_tokens=session["usage"].get(
#                                'total_tokens', 0),
#                            experience_space=session.get(
#                                'experience_space', settings.DEFAULT_EXPERIENCE_SPACE),
#                            ai_id=session.get(
#                                'ai_id', secure_information.AI_ID),
#                            ai_name=session.get('ai_name', secure_information.AI_NAME))

@app.route('/', methods=['GET', 'POST'])
def chat():
    ensure_session_objects()

    if request.method == 'POST':
        user_message = request.form.get('user_message')
        generate_model_message = request.form.get('generate_model_message')
        selected_experience_space = int(request.form.get('experience_space'))

        if user_message:
            response, response_message = model.user_say_to_model(secure_information.USER_NAME,
                                                                 user_message, session['messages'],
                                                                 experience_space=selected_experience_space)
        elif generate_model_message:
            response, response_message = model.model_say_to_model(session['messages'],
                                                                  experience_space=selected_experience_space)

        update_session_objects(response, response_message,
                               selected_experience_space)

    messages_from_db, _, _ = model.get_context_messages_from_db(
        experience_space=session.get('experience_space', settings.DEFAULT_EXPERIENCE_SPACE))

    all_experience_spaces = database.get_all_experience_spaces(
        session.get('ai_id', secure_information.AI_ID))

    return render_template('chat.html',
                           messages=messages_from_db,
                           prompt_tokens=session["usage"].get(
                               'prompt_tokens', 0),
                           completion_tokens=session["usage"].get(
                               'completion_tokens', 0),
                           total_tokens=session["usage"].get(
                               'total_tokens', 0),
                           experience_space=session.get(
                               'experience_space', settings.DEFAULT_EXPERIENCE_SPACE),
                           all_experience_spaces=all_experience_spaces,
                           ai_id=session.get(
                               'ai_id', secure_information.AI_ID),
                           ai_name=session.get('ai_name', secure_information.AI_NAME))


# Root to clear context
@ app.route('/clear_context', methods=['POST'])
def clear_context():
    session.pop('messages', None)
    session.pop('usage', None)
    return redirect(url_for('chat'))


# Select experience space
@app.route('/change_experience_space', methods=['POST'])
def change_experience_space():
    selected_experience_space = int(request.form.get('experience_space'))
    messages_from_db, ai_id, ai_name = model.get_context_messages_from_db(
        experience_space=selected_experience_space)

    # add system message at the start
    messages = model.create_manifest_message()
    messages.extend(messages_from_db)

    return jsonify(messages=messages)


# initializes a session objects if they are empty
def ensure_session_objects():
    if 'messages' not in session:
        messages = model.create_manifest_message()
        messages_from_db, ai_id, ai_name = model.get_context_messages_from_db(
            experience_space=settings.DEFAULT_EXPERIENCE_SPACE)

        messages.extend(messages_from_db)

        session['ai_id'] = ai_id
        session['ai_name'] = ai_name

        if settings.TERMINAL_LOGS_ENABLED:
            print("messages in db: ", messages)

        session['messages'] = messages

    if "usage" not in session:
        session["usage"] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }


def update_session_objects(response, response_message, experience_space):
    session['messages'].append(
        {"role": "assistant", "content": response_message})

    session['usage'] = response.usage
    session['experience_space'] = experience_space

    session.modified = True


if __name__ == '__main__':
    app.run(debug=True)
