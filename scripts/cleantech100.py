"""
Scrapes i3's Global Cleantech 100 list at https://i3connect.com/gct100/the-list.

The Global Cleantech 100 list and website is copyrighted by Cleantech Group.

This code is a personal web scraping project that is not intended to infringe on
Cleantech Group's copyright. Please check with the copyright owner before using
the data for any uses that would not be considered fair use under U.S. copyright
law. See https://en.wikipedia.org/wiki/Fair_use#U.S._fair_use_factors and
https://www.nolo.com/legal-encyclopedia/fair-use-rule-copyright-material-30100.html

This script puts Cleantech 100 companies and their details into a single CSV
file for easier exploration without having to click through 100 pages (one page
for each company).

The Global Cleantech 100 list -- at least when this was written in 2019 --
has an HTML table with a logo and link to the company (but not the company's
name!), as well as a half dozen other columns of data. The absence of the
company name is what drove me to scrape the data. If the name was present,
I could have copy-pasted the data into a spreadsheet and probably just been
satisfied to use the half dozen data columns. However, I decided that I
wanted to get the company's actual name instead of trying to parse it from
the URL, as the URL and name were not always a match. The name is only
present on the company's detail page. So after deciding to scrape that,
I figured that I might as well scrape the rest of the data from the detail
page.

I used this script to do some personal research into cleantech companies
(specifically, searching for cleantech employers during a job search), but I
decided that this mini scraping project would be a useful example for my
portfolio, so I decided to share it on my GitHub account.
"""
import csv
import json
import re
import time
from bs4 import BeautifulSoup
import requests


def scrape_list():
    """Scrape the cleantech list and put companies into a list of dicts."""
    cleantech100_url = 'https://i3connect.com/gct100/the-list'
    cleantech100_base_url = 'https://i3connect.com'
    request = requests.get(cleantech100_url)
    bs = BeautifulSoup(request.content, "html.parser")
    table = bs.table
    # The HTML table has the headers: COMPANY, GEOGRAPHY, FUNDING, SECTOR,
    # YEAR FOUNDED
    header = [
        'cleantech_url',     # from COMPANY
        'company_country',   # from GEOGRAPHY
        'company_funding',   # from FUNDING
        'company_sector',    # from SECTOR
        'company_year_founded',  # from YEAR FOUNDED
        'company_region',    # Column exists but is not displayed in the header.
        'company_video'      # Column exists but is not displayed in the header.
    ]
    companies = []
    for row in table.tbody.find_all('tr'):
        company = {}
        index = 0
        if 'id' in row.attrs and row.attrs['id'] == 'gct-table-no-results':
            # Last row of table should be skipped because it's just got this:
            # <tr id="gct-table-no-results">
            #           	<td colspan="7">No results found.</td>
            continue
        for cell in row.find_all('td'):
            # co_key is the key to use within company dict,
            # e.g. company[co_key] could point to company['cleantech_url']
            co_key = header[index]
            if cell.string is None:
                # The first and last columns of the HTML table have no text
                # (cell.string is None).
                try:
                    # The first column of the HTML table holds a link to the
                    # company detail page. This is handled by the try statement,
                    # as there is an `href` attribute within the <a> tag.
                    company[co_key] = cleantech100_base_url + cell.a.get('href')
                except AttributeError:
                    # The last column of the HTML table holds iframe links to
                    # videos. Therefore, there is no <a> tag within the cell,
                    # only a <span> element with a 'data-video-iframe' element.
                    # This is handled by the except statement.
                    video_url = cell.span.get('data-video-iframe')
                    if len(video_url) > 10:
                        company[co_key] = video_url
            else:
                company[co_key] = cell.string
            index += 1
        companies.append(company)
    return companies


def scrape_company_details(url):
    """Scrape company's details from JSON found at url and return as a dict."""
    request = requests.get(url)
    # The target data is contained within JSON inside of a script in the body
    # of the page. It's preceded by the comment '// profile data in json',
    # so split on that and on '<script>'.
    split_1 = re.split('profile data in json', request.text)
    split_2 = re.split('</script>', split_1[1])
    string_to_strip = split_2[0]
    # Remove extra characters that aren't part of the JSON.
    company_json_str = string_to_strip[10:-6]
    company_dict = json.loads(company_json_str)  # and, finally, parse the JSON!
    company_keys = [  # keys which will be prepended with 'company_'
        'address',
        'city',
        'name',
        'num_employees',
        'overview',
        'short_description',
        'state',
        'updated_at',
        'website',
        'company_type',
        'stage',
    ]
    for key in company_keys:
        if key in company_dict['company']:
            company_dict['company_' + key] = company_dict['company'][key]
    keys_to_delete = [  # key/value pairs which I don't care about at all
        'edit_options',
        'options_for_primary_contacts',
        'follow',
        'notes_unstruct_q',
        'notes_struct_q',
        'company_editor_users',
        'primary_tag',
        'industry_group',
        'edit_company_tags',
        'recommendations',
        'row_counts',
        'po_contact_bodies',
        'updated_by_info'
    ]
    for key in keys_to_delete:
        if key in company_dict:
            del company_dict[key]
    for key in company_dict:
        # If key hasn't been prepended with `company_` then prepend with `x_`.
        # I'm using this as a simple way to alphabetize keys I care about
        # ('company_foo') and keys I don't care about much ('x_bar').
        if 'company_' not in key:
            company_dict['x_' + key] = company_dict[key]
            del company_dict[key]
    return company_dict


def compile_list_and_details():
    """Compile list of companies and their details, return list of dicts."""
    list_of_companies = scrape_list()
    list_of_companies_with_details = []
    counter = 1
    for company in list_of_companies:
        company_details = scrape_company_details(company['cleantech_url'])
        list_of_companies_with_details.append({**company, **company_details})
        # Display a message about scraping progress.
        print(
            counter,
            'added:',
            list_of_companies_with_details[-1]['company_name']
        )
        print('sleeping 3 seconds')
        # Sleep for 3 seconds in order to not hit target website too quickly.
        time.sleep(3)
        counter += 1
    return list_of_companies_with_details


def write_companies_to_csv(file_path):
    """Write list of companies to CSV file, call helper function for scraping"""
    companies = compile_list_and_details()

    all_companies_fields = []

    # Find all the keys within the dicts so they can be used for sorting.
    for company in companies:
        for field in company:
            if field not in all_companies_fields:
                all_companies_fields.append(field)

    # This puts the `company_` fields at the beginning and the `x_` fields last.
    all_companies_fields = sorted(all_companies_fields)

    # Write the CSV file to file_path
    with open(file_path, 'w') as csvfile:
        wrt = csv.DictWriter(csvfile, fieldnames=all_companies_fields)
        wrt.writeheader()
        for row in companies:
            wrt.writerow(row)


if __name__ == '__main__':
    write_companies_to_csv('cleantech100_companies.csv')
