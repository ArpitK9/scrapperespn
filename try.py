from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import re
from datetime import datetime
import csv

def get_element_text_or_na(driver, by, xpath):
    try:
        return driver.find_element(by, xpath).text
    except Exception:
        return "NA"

# Read list of URLs from input CSV, assumes a header and a column named 'url'
def read_urls(csv_file):
    urls = []
    with open(csv_file, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'url' in row and row['url'].strip():
                urls.append(row['url'].strip())
    return urls

chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Activate headless mode (uses new headless mode in Chrome >= 109)
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
driver = webdriver.Chrome(options=chrome_options)

# ------ MODIFY CSV FILE PATH AS NEEDED ------
input_csv = "urls_list.csv"
output_csv = "matches.csv"

urls = read_urls(input_csv)

results = []

for url in urls:
    driver.get(url)

    city_venue_xpath = "(//a[@class='ds-inline-flex ds-items-start ds-leading-none']/span[@class='ds-text-tight-s ds-font-medium ds-block ds-text-typo ds-underline ds-decoration-ui-stroke hover:ds-text-typo-primary hover:ds-decoration-ui-stroke-primary'])[1]"
    Toss_Xpath = "(//td[@class='ds-text-typo']/span[@class='ds-text-tight-s ds-font-regular'])[1]"
    Team_1_xpath = "(//*[@class='ds-text-tight-l ds-font-bold ds-block ds-text-typo hover:ds-text-typo-primary ds-truncate'])[1]"
    Team_2_xpath = "(//*[@class='ds-text-tight-l ds-font-bold ds-block ds-text-typo hover:ds-text-typo-primary ds-truncate'])[2]"
    winner_xpath = "(//*[@class='ds-text-tight-s ds-font-medium ds-truncate ds-text-typo'])"
    umpire_1_xpath = "//*[text()='Umpires']/parent::td/parent::tr/td[2]/div[1]"
    umpire_2_xpath = "//*[text()='Umpires']/parent::td/parent::tr/td[2]/div[2]"
    match_date_xpath = "//*[text()='Match days']/parent::td/parent::tr/td[2]/span[1]"
    player_of_match_xpath = "(//*[text()='Player Of The Match'])[2]/ancestor::tr/td[2]/div/a/span/span"

    city_venue = get_element_text_or_na(driver, "xpath", city_venue_xpath)
    toss_winner_toss_decision = get_element_text_or_na(driver, "xpath", Toss_Xpath)
    team_1 = get_element_text_or_na(driver, "xpath", Team_1_xpath)
    team_2 = get_element_text_or_na(driver, "xpath", Team_2_xpath)
    winner_result_result_margin = get_element_text_or_na(driver, "xpath", winner_xpath)
    umpire_1 = get_element_text_or_na(driver, "xpath", umpire_1_xpath)
    umpire_2 = get_element_text_or_na(driver, "xpath", umpire_2_xpath)
    match_date = get_element_text_or_na(driver, "xpath", match_date_xpath)
    player_of_match = get_element_text_or_na(driver, "xpath", player_of_match_xpath)

    # Splitting city_venue
    if city_venue != "NA" and ',' in city_venue:
        venue, city = [item.strip() for item in city_venue.split(',', 1)]
    else:
        venue = city = "NA"

    # Splitting toss_winner_toss_decision
    if toss_winner_toss_decision != "NA" and ',' in toss_winner_toss_decision:
        toss_winner, decision_raw = [x.strip() for x in toss_winner_toss_decision.split(',', 1)]
        if "field" in decision_raw:
            toss_decision = "field"
        elif "bat" in decision_raw:
            toss_decision = "bat"
        else:
            toss_decision = "NA"
    else:
        toss_winner = toss_decision = "NA"

    # Winner, result, and margin parsing
    if winner_result_result_margin != "NA" and ' won by ' in winner_result_result_margin:
        parts = winner_result_result_margin.split(' won by ', 1)
        winner = parts[0].strip()
        remainder = parts[1]
        match = re.search(r'(\d+)\s+(runs?|wickets?)', remainder)
        if match:
            margin = match.group(1)
            result = 'runs' if 'run' in match.group(2) else 'wickets'
        else:
            margin = result = "NA"
    else:
        winner = result = margin = "NA"

    # Date processing
    if match_date != "NA" and '-' in match_date:
        try:
            date_part = match_date.split('-')[0].strip()
            parsed_date = datetime.strptime(date_part, "%d %B %Y")
            formatted_date = parsed_date.strftime("%d-%m-%y")
        except Exception:
            formatted_date = "NA"
    else:
        formatted_date = "NA"

    # Match ID extraction
    match = re.search(r'/(\d+)/(?:full-scorecard|scorecard|match-coverage|live-score|live|commentary|ball-by-ball)', url)
    if match:
        match_id = match.group(1)
    else:
        match_id = re.search(r'-([0-9]+)/[^/]+$', url)
        match_id = match_id.group(1) if match_id else "NA"

    csv_columns = [
        ("id", match_id),
        ("city", city),
        ("date", formatted_date),
        ("player_of_match", player_of_match),
        ("venue", venue),
        ("team1", team_1),
        ("team2", team_2),
        ("toss_winner", toss_winner),
        ("toss_decision", toss_decision),
        ("winner", winner),
        ("result", result),
        ("result_margin", margin),
        ("umpire1", umpire_1),
        ("umpire2", umpire_2)
    ]

    results.append([col[1] for col in csv_columns])

# Write output
with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    # write header
    writer.writerow([col[0] for col in csv_columns])
    # write all data rows
    writer.writerows(results)

driver.quit()
