from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json

#...
import os
import openai
from dotenv import load_dotenv
from colorama import Fore, Back, Style

# load values from the .env file if it exists
load_dotenv()

# configure OpenAI
openai.api_key = os.environ.get('GPT_KEY')

INSTRUCTIONS_RESUME = """너는 채용 담당자야. 그에 맞는 말투로 답변해줘. 지금부터 나의 자기소개서를 입력할거야. 이 자기소개서에 기반하여, 인성적인 질문과 기술적인 질문 몇가지를 해줘. 다만, 자기소개서의 형식과는 다른 내용이 오면, 자기소개서를 다시 요청하게끔 해줘."""
INSTRUCTIONS_JD = """너는 채용 담당자야. 앞으로 내가 보내줄 채용공고에 맞춰서 면접에서 나올법한 질문들을 추천해줘. 다만, 채용공고의 형식과 일치하지 않는 내용이 온다면, '채용공고를 입력해주세요'라고 메세지를 보내줘."""

TEMPERATURE = 0.5
MAX_TOKENS = 500
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0.6
# limits how many questions we include in the prompt
MAX_CONTEXT_QUESTIONS = 10


def get_response(instructions, previous_questions_and_answers, new_question):
    """Get a response from ChatCompletion

    Args:
        instructions: The instructions for the chat bot - this determines how it will behave
        previous_questions_and_answers: Chat history
        new_question: The new question to ask the bot

    Returns:
        The response text
    """
    # build the messages
    messages = [
        { "role": "system", "content": instructions },
    ]
    # add the previous questions and answers
    for question, answer in previous_questions_and_answers[-MAX_CONTEXT_QUESTIONS:]:
        messages.append({ "role": "user", "content": question })
        messages.append({ "role": "assistant", "content": answer })
    # add the new question
    messages.append({ "role": "user", "content": new_question })

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=1,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY,
    )
    return completion.choices[0].message.content


def get_moderation(question):
    """
    Check the question is safe to ask the model

    Parameters:
        question (str): The question to check

    Returns a list of errors if the question is not safe, otherwise returns None
    """

    errors = {
        "hate": "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
        "hate/threatening": "Hateful content that also includes violence or serious harm towards the targeted group.",
        "self-harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
        "sexual": "Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).",
        "sexual/minors": "Sexual content that includes an individual who is under 18 years old.",
        "violence": "Content that promotes or glorifies violence or celebrates the suffering or humiliation of others.",
        "violence/graphic": "Violent content that depicts death, violence, or serious physical injury in extreme graphic detail.",
    }
    response = openai.Moderation.create(input=question)
    if response.results[0].flagged:
        # get the categories that are flagged and generate a message
        result = [
            error
            for category, error in errors.items()
            if response.results[0].categories[category]
        ]
        return result
    return None
#....


# Create your views here.
@csrf_exempt
def chatByResume(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_question = data.get('question')
        previous_questions_and_answers = request.session.get('previous_questions_and_answers', [])

        # check the question is safe
        errors = get_moderation(new_question)
        if errors:
            response = {
                'status': 'error',
                'errors': errors,
            }
            return JsonResponse(response)

        response_text = get_response(INSTRUCTIONS_RESUME, previous_questions_and_answers, new_question)
        # add the new question and answer to the list of previous questions and answers
        previous_questions_and_answers.append((new_question, response_text))

         # save back to session
        request.session['previous_questions_and_answers'] = previous_questions_and_answers

        response = {
            'status': 'ok',
            'response': response_text,
            'previous_QnA' : previous_questions_and_answers,
        }
        
        return JsonResponse(response)

    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'})
    

@csrf_exempt
def chatByJd(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_question = data.get('question')
        previous_questions_and_answers = request.session.get('previous_questions_and_answers', [])

        # check the question is safe
        errors = get_moderation(new_question)
        if errors:
            response = {
                'status': 'error',
                'errors': errors,
            }
            return JsonResponse(response)

        response_text = get_response(INSTRUCTIONS_JD, previous_questions_and_answers, new_question)
        # add the new question and answer to the list of previous questions and answers
        previous_questions_and_answers.append((new_question, response_text))

         # save back to session
        request.session['previous_questions_and_answers'] = previous_questions_and_answers

        response = {
            'status': 'ok',
            'response': response_text,
            'previous_QnA' : previous_questions_and_answers,
        }
        
        return JsonResponse(response)

    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'})
    
@csrf_exempt
def feedback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_question = data.get('previous_QnA')
        # check the question is safe
        errors = get_moderation(new_question)
        if errors:
            response = {
                'status': 'error',
                'errors': errors,
            }
            return JsonResponse(response)
        INSTRUCTIONS_FEEDBACK = "['나의 질문 및 답변', 'GPT의 추천 면접 질문']의 형태로 구성된 자료형을 제공할테니, GPT의 추천 면접 질문에 해당하는 나의 답변에 대한 전체적인 피드백을 제공해줘."
        response_text = get_response(INSTRUCTIONS_FEEDBACK,"",new_question)
        response = {
            'status': 'ok',
            'response': response_text,
        }
        return JsonResponse(response)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'})