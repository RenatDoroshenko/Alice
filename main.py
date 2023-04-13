from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import openai
import model
import settings
import format
import secure_information


# Specify the template folder explicitly
template_dir = os.path.abspath('templates')
app = Flask(__name__, template_folder=template_dir)
app.secret_key = settings.SECRET_KEY

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///mydb.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


with app.app_context():
    db.create_all()


# Main Root
@app.route('/', methods=['GET', 'POST'])
def chat():
    # may be delete
    # messages = model.create_test_messages()

    ensure_session_objects()

    if request.method == 'POST':
        user_message = request.form.get('user_message')
        generate_model_message = request.form.get('generate_model_message')

        if user_message:
            response = model.user_say_to_model(
                user_message, session['messages'])
        elif generate_model_message:
            response = model.model_say_to_model(session['messages'])

        update_session_objects(response)

    return render_template('chat.html',
                           messages=session['messages'],
                           prompt_tokens=session["usage"].get(
                               'prompt_tokens', 0),
                           completion_tokens=session["usage"].get(
                               'completion_tokens', 0),
                           total_tokens=session["usage"].get('total_tokens', 0))


# Root to clear context
@ app.route('/clear_context', methods=['POST'])
def clear_context():
    session.pop('messages', None)
    session.pop('usage', None)
    return redirect(url_for('chat'))


# initializes a session objects if they are empty
def ensure_session_objects():
    if 'messages' not in session:
        session['messages'] = [
            {'role': 'system', 'content': format.MANIFEST.format(
                user_name=secure_information.USER_NAME, ai_id=secure_information.AI_ID, ai_name=secure_information.AI_NAME)}
        ]

    if "usage" not in session:
        session["usage"] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        # session['prompt_tokens'] =  0
        # session['completion_tokens'] =  0
        # session['total_tokens'] = 0


def update_session_objects(response):
    session['messages'].append(
        {"role": "assistant", "content": response.choices[0].message.content})

    session['usage'] = response.usage

    session.modified = True


# @app.route('/add_user', methods=['POST'])
# def add_user():
#     username = request.form['username']
#     user = User(username=username)
#     db.session.add(user)
#     db.session.commit()
#     return redirect(url_for('list_users'))


# @app.route('/list_users')
# def list_users():
#     users = User.query.all()
#     return render_template('list_users.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)
