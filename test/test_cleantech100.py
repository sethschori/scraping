import os
from pathlib import Path
import time
import unittest
from unittest import mock
from scripts.cleantech100 import (compile_list_and_details,
                                  scrape_company_details, scrape_list,
                                  write_companies_to_csv)


# Thanks to https://stackoverflow.com/a/28507806 for the code below which I
# adapted in order to mock requests.content and requests.text.
def mocked_requests_get(*args, **kwargs):
    """Helper function to mock requests.get and avoid making real requests"""
    class MockResponse:
        def __init__(self, content, status_code):
            self.content = content
            self.text = content
            self.status_code = status_code

    test_dir = Path(__file__).resolve().parent
    # the_list_file has mocked HTML from https://i3connect.com/gct100/the-list
    the_list_file = test_dir.joinpath('cleantech100_tests_data/the-list.html')
    # company_file has mocked HTML from https://i3connect.com/company/actility
    company_file = test_dir.joinpath('cleantech100_tests_data/company.html')

    with open(the_list_file, 'r') as f:
        the_list_html = f.read()

    with open(company_file, 'r') as f:
        company_html = f.read()

    # If request is for cleantech list, return the-list mock
    if args[0] == 'https://i3connect.com/gct100/the-list':
        return MockResponse(the_list_html, 200)
    # If request is for a company detail page, return Actility detail page mock
    elif 'https://i3connect.com/company/' in args[0]:
        return MockResponse(company_html, 200)

    return MockResponse(None, 404)


def mocked_time_sleep(*args, **kwargs):
    """Helper function to mock time.sleep and avoid sleeping 3 seconds"""

    return time.sleep(20)


class ScrapeListTests(unittest.TestCase):
    """Tests for scrape_list"""

    @mock.patch(
        'scripts.cleantech100.requests.get',
        side_effect=mocked_requests_get
    )
    def test_company_0_keys_and_values(self, mock_get):

        returned_companies = scrape_list()
        company_0 = returned_companies[0]
        self.assertEqual(
            'https://i3connect.com/company/actility',
            company_0['cleantech_url']
        )
        self.assertEqual('France', company_0['company_country'])
        self.assertEqual('$113.2M', company_0['company_funding'])
        self.assertEqual('smart grid', company_0['company_sector'])
        self.assertEqual('2010', company_0['company_year_founded'])
        self.assertEqual('Europe & Israel', company_0['company_region'])
        self.assertEqual(
            'https://www.youtube.com/embed/yIDDl65hOvI',
            company_0['company_video'],
        )

    @mock.patch(
        'scripts.cleantech100.requests.get',
        side_effect=mocked_requests_get
    )
    def test_company_99_keys_and_values(self, mock_get):

        returned_companies = scrape_list()
        company_99 = returned_companies[99]
        self.assertEqual(
            'https://i3connect.com/company/vulog',
            company_99['cleantech_url'],
        )
        self.assertEqual('France', company_99['company_country'])
        self.assertEqual('$30.98M', company_99['company_funding'])
        self.assertEqual('transportation', company_99['company_sector'])
        self.assertEqual('2006', company_99['company_year_founded'])
        self.assertEqual('Europe & Israel', company_99['company_region'])
        self.assertEqual(
            '\n',
            company_99['company_video']
        )

    @mock.patch(
        'scripts.cleantech100.requests.get',
        side_effect=mocked_requests_get
    )
    def test_100_companies(self, mock_get):

        returned_companies = scrape_list()
        self.assertEqual(100, len(returned_companies))


class ScrapeCompanyDetailsTests(unittest.TestCase):
    """Tests for scrape_company_details"""

    @mock.patch(
        'scripts.cleantech100.requests.get',
        side_effect=mocked_requests_get
    )
    def test_company_details(self, mock_get):

        company_details = scrape_company_details(
            'https://i3connect.com/company/actility'
        )
        self.assertEqual(
            '4 rue Ampère BP 30255',
            company_details['company_address']
        )
        self.assertEqual('Lannion', company_details['company_city'])
        exp = "{'parent_objs': [], 'parent': '', 'child': '', 'subsidiary': ''}"
        self.assertEqual(exp, str(company_details['x_structure']))

    @mock.patch(
        'scripts.cleantech100.requests.get',
        side_effect=mocked_requests_get
    )
    def test_company_details_deleted_keys(self, mock_get):

        company_details = scrape_company_details(
            'https://i3connect.com/company/actility'
        )
        self.assertNotIn('edit_options', company_details)


class CompileListAndDetailsTests(unittest.TestCase):
    """Tests for compile_list_and_details"""

    @mock.patch(
        'scripts.cleantech100.requests.get',
        side_effect=mocked_requests_get
    )
    @mock.patch(
        'scripts.cleantech100.time.sleep',
        # return_value suggested by https://stackoverflow.com/a/22839439
        # but doesn't seem to be needed
        # return_value=None,
    )
    def test_compiled_list_and_details(self, mock_get, patched_time_sleep):

        list_of_companies_with_details = compile_list_and_details()
        self.assertEqual(100, len(list_of_companies_with_details))


class WriteCompaniesToCsv(unittest.TestCase):
    """Tests for write_companies_to_csv"""

    @mock.patch(
        'scripts.cleantech100.requests.get',
        side_effect=mocked_requests_get
    )
    @mock.patch(
        'scripts.cleantech100.time.sleep'
    )
    def test_write_companies_to_csv(self, mock_get, patched_time_sleep):

        test_dir = Path(__file__).resolve().parent
        gold_csv_file = test_dir.joinpath(
            'cleantech100_tests_data/gold_companies.csv'
        )
        test_csv_file = test_dir.joinpath(
            'cleantech100_tests_data/test_companies.csv'
        )
        write_companies_to_csv(test_csv_file)
        with open(gold_csv_file, 'r') as f:
            gold_csv_file_str = f.read()
        with open(test_csv_file, 'r') as f:
            test_csv_file_str = f.read()
        self.assertEqual(test_csv_file_str, gold_csv_file_str)
        os.remove(test_csv_file)


if __name__ == '__main__':
    unittest.main()
