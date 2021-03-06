import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable

PROGRAMMING_LANGUAGES = [
    'JavaScript',
    'Java',
    'Python',
    'Ruby',
    'PHP',
    'C++',
    'C#',
    '1С',
    'Kotlin',
    'Swift',
    'Go'
]
SJ_MOSCOW_CODE = 4
SJ_IT_CODE = 48


def predict_rub_salary_hh(vacancy):
    if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
        return predict_salary(vacancy['salary']['from'],
                              vacancy['salary']['to'])


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] and vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'],
                              vacancy['payment_to'])


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return salary_from + salary_to / 2
    elif salary_to:
        return salary_to * 0.8
    elif salary_from:
        return salary_from * 1.2


def get_table(all_languages_stat, title=''):
    table_data = [
        [
            'Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата'
        ]
    ]
    for lang_name, stats in all_languages_stat.items():
        table_data.append(
            [
                lang_name,
                stats['vacancies_found'],
                stats['vacancies_processed'],
                stats['average_salary']
            ]
        )
    table = AsciiTable(table_data, title)
    return table.table


def get_headhunter_stats(languages):
    all_languages_stat = {}
    for language in languages:
        vacancies_processed, average_salary, vacancies_found = get_hh_lang_stat(
            language)
        all_languages_stat[language] = {
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary,
            'vacancies_found': vacancies_found
        }
    return all_languages_stat


def get_superjob_stats(languages, superjob_token):
    all_languages_stat = {}
    for language in languages:
        vacancies_processed, average_salary, vacancies_found = get_sj_lang_stat(
            language, superjob_token)
        all_languages_stat[language] = {
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary,
            'vacancies_found': vacancies_found
        }
    return all_languages_stat


def get_hh_lang_stat(language):
    payload = {
        'text': 'программист {}'.format(language),
        'per_page': 100,
    }

    vacancies_processed = 0
    page = 0
    pages_number = 1
    salary_total = 0
    average_salary = 0

    while page < pages_number:
        payload['page'] = page
        response = requests.get('https://api.hh.ru/vacancies', params=payload)
        response.raise_for_status()
        response = response.json()
        pages_number = response['pages']

        for vacancy in response['items']:
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                salary_total += salary
                vacancies_processed += 1
        page += 1

    if vacancies_processed:
        average_salary = int(salary_total / vacancies_processed)

    vacancies_found = response['found']
    return vacancies_processed, average_salary, vacancies_found


def get_sj_lang_stat(language, superjob_token):
    headers = {'X-Api-App-Id': superjob_token}

    payload = {
        'town': SJ_MOSCOW_CODE,
        'catalogues': SJ_IT_CODE,
        'count': 100,
        'keyword': language
    }

    vacancies_processed = 0
    average_salary = 0

    page = 0
    salary_total = 0
    more = True
    while more:
        payload['page'] = page
        page += 1
        response = requests.get('https://api.superjob.ru/2.0/vacancies/',
                                headers=headers,
                                params=payload)
        response.raise_for_status()
        response = response.json()
        more = response['more']

        for vacancy in response['objects']:
            salary = predict_rub_salary_sj(vacancy)
            if salary:
                salary_total += salary
                vacancies_processed += 1

    if vacancies_processed:
        average_salary = int(salary_total / vacancies_processed)

    vacancies_found = response['total']
    return vacancies_processed, average_salary, vacancies_found


if __name__ == '__main__':
    load_dotenv()
    superjob_token = os.getenv('SUPERJOB_TOKEN')
    print(get_table(get_headhunter_stats(PROGRAMMING_LANGUAGES),
                    'Статистика зарплат HeadHunter'))
    print(get_table(get_superjob_stats(PROGRAMMING_LANGUAGES, superjob_token),
                    'Статистика зарплат Superjob'))
