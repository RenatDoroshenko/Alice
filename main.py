# main.py
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import model
import settings
import secure_information
import json
import memory

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

# Load memory index
memory_index, metadata = memory.load_memory_index()


@app.template_filter('tojson')
def tojson_filter(obj, indent=None):
    return json.dumps(obj, indent=indent)


@app.route('/', methods=['GET', 'POST'])
def chat():

    ai_id = secure_information.AI_ID
    selected_experience_space = request.form.get(
        'experience_space', settings.DEFAULT_EXPERIENCE_SPACE, type=int)

    messages, ai_id, ai_name = model.get_context_messages_with_manifest(
        ai_id=ai_id, experience_space=selected_experience_space)

    if 'usage' not in session:
        set_default_usage(0, 0, 0)

    if request.method == 'POST':
        user_message = request.form.get('user_message')
        generate_model_message = request.form.get('generate_model_message')
        selected_experience_space = int(request.form.get('experience_space'))

        if user_message:
            response, response_message = model.user_say_to_model(user_name=secure_information.USER_NAME,
                                                                 user_message=user_message,
                                                                 messages=messages,
                                                                 experience_space=selected_experience_space,
                                                                 memory_index=memory_index,
                                                                 metadata=metadata)
        elif generate_model_message:
            response, response_message = model.model_say_to_model(messages=messages,
                                                                  experience_space=selected_experience_space,
                                                                  memory_index=memory_index,
                                                                  metadata=metadata)

        # Save changes made to memory index
        memory.save_memory_index(memory_index, metadata)

        update_session_objects(response, selected_experience_space)

        messages.append(
            {"role": "assistant", "content": response_message})

    all_experience_spaces = database.get_all_experience_spaces(
        session.get('ai_id', ai_id))
    highest_experience_space = max(all_experience_spaces, default=1)

    return render_template('chat.html',
                           messages=messages,
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
                           ai_name=session.get('ai_name', secure_information.AI_NAME))


# Select experience space
@app.route('/change_experience_space', methods=['POST'])
def change_experience_space():

    # reset the usage
    # set_default_usage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    ai_id = secure_information.AI_ID
    selected_experience_space = int(request.form.get('experience_space'))
    print("Selected experience space:",
          selected_experience_space)  # Add this line
    messages, ai_id, ai_name = model.get_context_messages_with_manifest(ai_id=ai_id,
                                                                        experience_space=selected_experience_space)

    usage = session['usage']

    all_experience_spaces = database.get_all_experience_spaces(
        session.get('ai_id', ai_id))

    if len(all_experience_spaces) == 0:
        all_experience_spaces = [1]
    else:
        all_experience_spaces.sort()

    return jsonify(messages=messages, usage=usage, all_experience_spaces=all_experience_spaces)


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
