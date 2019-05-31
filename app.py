import requests
import configparser
from terminaltables import AsciiTable

config = configparser.ConfigParser()
config.read('config.ini')

SUPERJOB_SECRET_KEY = config['SUPERJOB']['SECRET_KEY']
HH_API_URL = 'https://api.hh.ru/vacancies'
SJ_API_URL = 'https://api.superjob.ru/2.0/vacancies/'


trend_langs = (
    'JavaScript',
    'Java',
    'Python',
    'Ruby',
    'PHP',
    'C++',
    'C#',
    'C',
    'Go',
    '1с',
)


def get_predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8


def show_table(languages, title):
    table_data = list()
    table_data.append([
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата', ]
    )
    for language, vacancy_data in languages.items():
        table_row = list()
        table_row.append(language)
        table_row.extend(list(vacancy_data.values()))
        table_data.append(table_row)
    table_instance = AsciiTable(table_data, title)
    print(table_instance.table)


def get_hh_vacancies(language):
    payloads = {
        'text': language,
        'area': 1,
        'period': 30,
    }
    vacancies = list()
    page = 0
    pages_number = 1
    while page < pages_number:
        payloads['page'] = page
        response = requests.get(HH_API_URL, params=payloads)
        response.raise_for_status()
        page_data = response.json()
        vacancies.extend(page_data['items'])
        pages_number = page_data['pages']
        page += 1
    return vacancies


def get_predict_rub_salary_hh(vacancy):
    if not vacancy['salary']:
        return None
    if not vacancy['salary']['currency'] == 'RUR':
        return None
    salary_from = vacancy['salary']['from']
    salary_to = vacancy['salary']['to']
    if not salary_from:
        salary_from = 0
    if not salary_to:
        salary_to = 0
    return get_predict_salary(salary_from, salary_to)


def get_statistic_hh():
    languages = dict()
    for language in trend_langs:
        vacancies = get_hh_vacancies(language)
        vacancies_salary = [get_predict_rub_salary_hh(vacancy) for vacancy in vacancies if get_predict_rub_salary_hh(vacancy)]
        vacancies_found = len(vacancies)
        vacancies_processed = len(vacancies_salary)
        try:
            average_salary = int(sum(vacancies_salary) / vacancies_processed)
        except ZeroDivisionError:
            average_salary = 0
        languages[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary,
        }
    return languages


def get_sj_vacancies(language=None):
    payloads = {
        'keywords[1][srws]': 1,
        'keywords[1][keys]': language,
        'town': 4,
    }
    headers = {
       'X-Api-App-Id': SUPERJOB_SECRET_KEY
    }
    vacancies = list()
    page = 0
    more = True
    while more:
        payloads['page'] = page
        response = requests.get(SJ_API_URL, headers=headers, params=payloads)
        response.raise_for_status()
        page_data = response.json()
        vacancies.extend(page_data['objects'])
        more = page_data['more']
        page += 1
    return vacancies


def get_predict_rub_salary_sj(vacancy):
    if not vacancy['currency'] == 'rub':
        return None
    salary_from = vacancy['payment_from']
    salary_to = vacancy['payment_to']
    return get_predict_salary(salary_from, salary_to)


def get_statistic_sj():
    languages = dict()

    for language in trend_langs:
        vacancies = get_sj_vacancies(language)
        vacancies_salary = [get_predict_rub_salary_sj(vacancy) for vacancy in vacancies if get_predict_rub_salary_sj(vacancy)]
        vacancies_found = len(vacancies)
        vacancies_processed = len(vacancies_salary)
        try:
            average_salary = int(sum(vacancies_salary) / vacancies_processed)
        except ZeroDivisionError:
            average_salary = 0
        languages[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary,
        }
    return languages


def show_possible_salary():
    show_table(get_statistic_sj(), 'SuperJob Moscow')
    show_table(get_statistic_hh(), 'HeadHunter Moscow')


if __name__ == '__main__':
    show_possible_salary()

