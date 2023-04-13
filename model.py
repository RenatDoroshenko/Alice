import openai
import settings
import tiktoken
import format
import secure_information


def model_say_to_model(messages):

    response = generate_response(messages)
    return response


def user_say_to_model(user_message, messages):
    full_response = format.USER_RESPONSE.format(
        user_name=secure_information.USER_NAME, content=user_message)
    messages.append(
        {"role": "user", "content": full_response})
    response = generate_response(messages)
    return response


def generate_response(messages, context_tokens_limit=settings.CONTEXT_TOKENS_LIMIT):
    openai.api_key = secure_information.OPEN_AI_API_KEY

    # Remove earliest messages until the total tokens are under the limit (except 'system' message)
    while num_tokens_from_messages(messages) > context_tokens_limit:
        messages.pop(1)

    # Combine messages into a single string
    # prompt = "\n\n".join(
    #     [f"{msg['role'].title()}: {msg['content']}" for msg in messages]) + "\n\n"

    # Calculate the remaining tokens for the response
    remaining_tokens = settings.MAX_TOKENS - num_tokens_from_messages(messages)

    # Generate response using OpenAI API
    response = openai.ChatCompletion.create(
        model=settings.MODEL_ID,
        messages=messages,
        max_tokens=remaining_tokens,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return response


def chatgpt_conversation(messages, role):
    response = openai.ChatCompletion.create(
        model=settings.MODEL_ID,
        messages=messages
    )
    messages.append({
        "role": role, "content": response.choices[0].message.content
    })

    return messages


def create_test_messages():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant",
            "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
    return messages


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        print(
            "Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 4
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
