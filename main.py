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


def predict_rub_salary_hh(vacancy):
    if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
        return predict_salary(vacancy['salary']['from'], vacancy['salary']['to'])


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] and vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return salary_from + salary_to / 2
    elif salary_to:
        return salary_to * 0.8
    elif salary_from:
        return salary_from * 1.2


def get_table(all_languages_stat, title=''):
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for lang_name, stats in all_languages_stat.items():
        table_data.append(
            [lang_name, stats['vacancies_found'], stats['vacancies_processed'], stats['average_salary']]
        )
    table = AsciiTable(table_data, title)
    return table.table


def get_headhinter_stats_dict(languages):
    all_languages_stat = {}
    for language in languages:
        payload = {
            'text': 'программист {}'.format(language),
            'per_page': 100,
        }
        lang_stat = {
            'vacancies_processed': 0,
            'average_salary': 0,
            'vacancies_found': 0,
        }
        page = 0
        pages_number = 1
        salary_total = 0

        while page < pages_number:
            payload['page'] = page
            response = requests.get('https://api.hh.ru/vacancies', params=payload)

            if response.ok:
                pages_number = response.json()['pages']
                lang_stat['vacancies_found'] = response.json()['found']

                for vacancy in response.json()['items']:
                    salary = predict_rub_salary_hh(vacancy)
                    if salary:
                        salary_total += salary
                        lang_stat['vacancies_processed'] += 1
                if lang_stat['vacancies_processed']:
                    lang_stat['average_salary'] = int(salary_total / lang_stat['vacancies_processed'])
                all_languages_stat[language] = lang_stat
            page += 1
    return all_languages_stat


def get_superjob_stats_dict(languages):
    headers = {'X-Api-App-Id': os.getenv('SUPERJOB_TOKEN')}

    payload = {
        'town': 4,
        'catalogues': 48,
        'count': 100,
        'page': 0
    }

    all_languages_stat = {}

    for language in languages:
        lang_stat = {
            'vacancies_processed': 0,
            'average_salary': 0,
            'vacancies_found': 0
        }
        page = 0
        salary_total = 0
        more = True
        while more:
            payload['keyword'] = language
            payload['page'] = page
            page += 1
            response = requests.get('https://api.superjob.ru/2.0/vacancies/', headers=headers, params=payload)
            more = response.json()['more']
            lang_stat['vacancies_found'] = response.json()['total']

            for vacancy in response.json()['objects']:
                salary = predict_rub_salary_sj(vacancy)
                if salary:
                    salary_total += salary
                    lang_stat['vacancies_processed'] += 1

        if lang_stat['vacancies_processed']:
            lang_stat['average_salary'] = int(salary_total / lang_stat['vacancies_processed'])
        all_languages_stat[language] = lang_stat
    return all_languages_stat


if __name__ == "__main__":
    load_dotenv()
    print(get_table(get_headhinter_stats_dict(PROGRAMMING_LANGUAGES), 'Статистика зарплат HeadHunter'))
    print(get_table(get_superjob_stats_dict(PROGRAMMING_LANGUAGES), 'Статистика зарплат Superjob'))
