from pathlib import Path
import unittest
from unittest import mock
from scripts.cleantech100 import scrape_list


# Thanks to https://stackoverflow.com/a/28507806 for the code below which I
# adapted in order to mock requests.content.
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, content, status_code):
            self.content = content
            self.status_code = status_code

    test_dir = Path(__file__).resolve().parent
    # the_list_file has mocked HTML from https://i3connect.com/gct100/the-list
    the_list_file = test_dir.joinpath('cleantech100_tests_data/the-list.html')

    with open(the_list_file, 'r') as f:
        the_list_html = f.read()

    if args[0] == 'https://i3connect.com/gct100/the-list':
        return MockResponse(the_list_html, 200)
    elif args[0] == 'http://someotherurl.com/anothertest.json':
        return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)


class ScrapeListTests(unittest.TestCase):

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
    def test_company_100_keys_and_values(self, mock_get):

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


if __name__ == '__main__':
    unittest.main()
