# database.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    summary_id = db.Column(
        db.Integer, db.ForeignKey("summary.id"), nullable=True)
    message_type = db.Column(
        db.Enum("system", "assistant", "user"), nullable=False)
    author = db.Column(db.Enum("AI", "user", "environment"), nullable=False)
    ai_id = db.Column(db.String(100), nullable=True)
    ai_name = db.Column(db.String(100), nullable=True)
    thoughts = db.Column(db.Text, nullable=True)
    to_user = db.Column(db.Text, nullable=True)
    user_name = db.Column(db.String(100), nullable=True)
    user_message = db.Column(db.Text, nullable=True)
    commands = db.Column(db.Text, nullable=True)
    commands_result = db.Column(db.Text, nullable=True)
    memories = db.Column(db.Text, nullable=True)
    experience_space = db.Column(db.Integer, nullable=True)
    diagnostic = db.Column(db.Boolean, nullable=False, default=False)
    date_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'message_type': self.message_type,
            'author': self.author,
            'ai_id': self.ai_id,
            'ai_name': self.ai_name,
            'thoughts': self.thoughts,
            'to_user': self.to_user,
            'user_name': self.user_name,
            'user_message': self.user_message,
            'commands': self.commands,
            'commands_result': self.commands_result,
            'memories': self.memories,
            'experience_space': self.experience_space,
            'date_time': self.date_time.isoformat()
        }


class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.Text, nullable=False)
    date_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    experiences = db.relationship("Experience", backref="summary", lazy=True)


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    steps = db.relationship('Step', backref='plan', lazy=True)


class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    substeps = db.relationship('SubStep', backref='step', lazy=True)


class SubStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    step_id = db.Column(db.Integer, db.ForeignKey('step.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)


def get_messages_by_ids(ids):
    """
    Retrieve a list of Experience entries based on the provided list of ids.
    Also retrieves the previous and next entries with the same experience_space.

    :param ids: List of ids of the entries to retrieve
    :return: List of Experience entries
    """
    all_experiences = []

    for id in ids:
        experience = Experience.query.filter(Experience.id == id).first()
        if experience:
            all_experiences.append(experience)
            prev_experience = Experience.query.filter(
                Experience.id < id,
                Experience.experience_space == experience.experience_space
            ).order_by(Experience.id.desc()).first()
            if prev_experience:
                all_experiences.append(prev_experience)
            next_experience = Experience.query.filter(
                Experience.id > id,
                Experience.experience_space == experience.experience_space
            ).order_by(Experience.id.asc()).first()
            if next_experience:
                all_experiences.append(next_experience)

    # Remove duplicates
    added_ids = set()
    experiences = []
    for exp in all_experiences:
        if exp.id not in added_ids:
            experiences.append(exp)
            added_ids.add(exp.id)

    # Sort experiences by id
    experiences = sorted(experiences, key=lambda x: x.id)

    return experiences


def get_latest_messages(ai_id, experience_space, messages_number, diagnostic=False):
    if diagnostic:
        latest_messages = (
            Experience.query.filter_by(
                ai_id=ai_id, experience_space=experience_space)
            .order_by(Experience.date_time.desc())
            .limit(messages_number)
            .all()
        )
    else:
        latest_messages = (
            Experience.query.filter_by(
                ai_id=ai_id, experience_space=experience_space, diagnostic=False)
            .order_by(Experience.date_time.desc())
            .limit(messages_number)
            .all()
        )
    return latest_messages[::-1]


def save_user_message(user_name, user_message, ai_id, ai_name, experience_space, memories, diagnostic=False):
    memories_string = json.dumps([memory.to_dict() for memory in memories])

    print('user memories to save: ')
    print(memories)

    user_entry = Experience(
        message_type="user",
        author="user",
        ai_id=ai_id,
        ai_name=ai_name,
        user_name=user_name,
        user_message=user_message,
        memories=memories_string,
        experience_space=experience_space,
        diagnostic=diagnostic
    )
    db.session.add(user_entry)
    db.session.commit()

    return user_entry.id, user_entry.date_time


def save_ai_message(ai_id, ai_name, thoughts, to_user, commands, commands_result, memories, experience_space, diagnostic=False):
    # commands_string = json.dumps(commands)
    commands_string = commands
    commands_result_string = json.dumps(commands_result)
    memories_string = json.dumps([memory.to_dict() for memory in memories])

    print('ai memories to save: ')
    print(memories)

    ai_entry = Experience(
        message_type="assistant",
        author="AI",
        ai_id=ai_id,
        ai_name=ai_name,
        thoughts=thoughts,
        to_user=to_user,
        commands=commands_string,
        commands_result=commands_result_string,
        memories=memories_string,
        experience_space=experience_space,
        diagnostic=diagnostic
    )
    db.session.add(ai_entry)
    db.session.commit()

    return ai_entry.id, ai_entry.date_time


def save_environment_message(ai_id, ai_name, commands, experience_space):
    environment_entry = Experience(
        message_type="system",
        author="environment",
        ai_id=ai_id,
        ai_name=ai_name,
        commands=commands,
        experience_space=experience_space
    )
    db.session.add(environment_entry)
    db.session.commit()

    return environment_entry.id


def get_all_experience_spaces(ai_id):
    all_experience_spaces = (
        db.session.query(Experience.experience_space)
        .filter(Experience.ai_id == ai_id)
        .distinct()
        .all()
    )
    all_experience_spaces = [experience_space[0]
                             for experience_space in all_experience_spaces if experience_space[0] is not None]
    return sorted(all_experience_spaces)

# Plans


def create_new_plan():
    new_plan = Plan()
    db.session.add(new_plan)
    db.session.commit()
    return new_plan


def add_step_to_plan(plan_id, content):
    new_step = Step(content=content, plan_id=plan_id)
    db.session.add(new_step)
    db.session.commit()
    return new_step


def add_substep_to_step(step_id, content):
    new_substep = SubStep(content=content, step_id=step_id)
    db.session.add(new_substep)
    db.session.commit()
    return new_substep


def modify_step(step_id, new_content):
    step_to_modify = Step.query.filter_by(id=step_id).first()
    if step_to_modify:
        step_to_modify.content = new_content
        db.session.commit()
    return step_to_modify

# Main functions


def create_plan_with_steps_and_substeps(plan_name, plan_steps_substeps):
    # Create a new plan
    new_plan = Plan()
    new_plan.name = plan_name
    db.session.add(new_plan)
    db.session.commit()

    for step in plan_steps_substeps:
        if isinstance(step, list):  # Check if this step has substeps
            step_content = step[0]  # The first item is the step content
            substeps = step[1:]  # The rest are the substeps

            # Create the step with its content
            new_step = Step(content=step_content, plan_id=new_plan.id)
            db.session.add(new_step)
            db.session.commit()

            # Create the substeps
            for substep_content in substeps:
                new_substep = SubStep(
                    content=substep_content, step_id=new_step.id)
                db.session.add(new_substep)
            db.session.commit()
        else:  # This step does not have substeps
            # Create the step with its content
            new_step = Step(content=step, plan_id=new_plan.id)
            db.session.add(new_step)
            db.session.commit()

    return f"Plan with id '{new_plan.id}' and its steps and substeps were created successfully."


def get_plan(plan_id):
    plan = Plan.query.get(plan_id)
    if plan is None:
        return "Plan not found"
    steps = Step.query.filter_by(plan_id=plan_id).all()

    output = f"Plan name: {plan.name}\n"
    for i, step in enumerate(steps, 1):
        output += f"{i}. {step.content}\n"
        substeps = SubStep.query.filter_by(step_id=step.id).all()
        for j, substep in enumerate(substeps, 1):
            output += f"    {i}.{j} {substep.content}\n"

    return output


def get_all_plans():
    plans = Plan.query.all()

    if not plans:
        return "No plans currently exist."

    result = []
    for plan in plans:
        plan_string = plan_to_string(plan)
        result.append(plan_string)

    return result


def plan_to_string(plan):
    steps = Step.query.filter_by(plan_id=plan.id).all()

    steps_list = []
    for i, step in enumerate(steps, start=1):
        step_string = step_to_string(i, step)
        steps_list.append(step_string)

    return f"{plan.name} - Plan id: {plan.id}:\n" + "\n".join(steps_list)


def step_to_string(step_index, step):
    substeps = SubStep.query.filter_by(step_id=step.id).all()

    substeps_list = []
    for i, substep in enumerate(substeps, start=1):
        substeps_list.append(f"{step_index}.{i} {substep.content}")

    return f"{step_index}. {step.content}\n" + "\n".join(["    " + s for s in substeps_list])


def remove_plan(plan_id):
    # Remove all substeps associated with the steps of the plan
    SubStep.query.filter(SubStep.step_id.in_(Step.query.with_entities(
        Step.id).filter_by(plan_id=plan_id))).delete(synchronize_session=False)

    # Remove all steps associated with the plan
    Step.query.filter_by(plan_id=plan_id).delete(synchronize_session=False)

    # Remove the plan itself
    Plan.query.filter_by(id=plan_id).delete(synchronize_session=False)

    db.session.commit()
    return f"Plan {plan_id} and all its steps and substeps have been removed successfully"


def modify_step(plan_id, step_position, new_name):
    steps = Step.query.filter_by(plan_id=plan_id).all()
    if step_position <= len(steps):
        step = steps[step_position - 1]
        step.content = new_name
        db.session.commit()
        return f"Step {step_position} modified successfully"
    else:
        return "Invalid step position"


def modify_substep(plan_id, step_position, substep_position, new_name):
    steps = Step.query.filter_by(plan_id=plan_id).all()
    if step_position <= len(steps):
        step = steps[step_position - 1]
        substeps = SubStep.query.filter_by(step_id=step.id).all()
        if substep_position <= len(substeps):
            substep = substeps[substep_position - 1]
            substep.content = new_name
            db.session.commit()
            return f"Substep {step_position}.{substep_position} modified successfully"
        else:
            return "Invalid substep position"
    else:
        return "Invalid step position"


def remove_step(plan_id, step_position):
    steps = Step.query.filter_by(plan_id=plan_id).all()
    if step_position <= len(steps):
        step = steps[step_position - 1]
        Step.query.filter_by(id=step.id).delete()
        db.session.commit()
        return f"Step {step_position} removed successfully"
    else:
        return "Invalid step position"


def remove_substep(plan_id, step_position, substep_position):
    steps = Step.query.filter_by(plan_id=plan_id).all()
    if step_position <= len(steps):
        step = steps[step_position - 1]
        substeps = SubStep.query.filter_by(step_id=step.id).all()
        if substep_position <= len(substeps):
            substep = substeps[substep_position - 1]
            SubStep.query.filter_by(id=substep.id).delete()
            db.session.commit()
            return f"Substep {step_position}.{substep_position} removed successfully"
        else:
            return "Invalid substep position"
    else:
        return "Invalid step position"


def append_step(plan_id, new_name):
    step = Step(content=new_name, plan_id=plan_id)
    db.session.add(step)
    db.session.commit()
    return f"Step '{new_name}' added to the plan"


def append_substep(plan_id, step_position, new_name):
    steps = Step.query.filter_by(plan_id=plan_id).all()
    if step_position <= len(steps):
        step = steps[step_position - 1]
        substep = SubStep(content=new_name, step_id=step.id)
        db.session.add(substep)
        db.session.commit()
        return f"Substep '{new_name}' added to step {step_position}"
    else:
        return "Invalid step position"
