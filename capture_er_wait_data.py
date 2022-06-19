import time
import datetime
import os
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

stats_file_name = "hospital_stats.csv"
CRLF = "\r\n"
polling_interval = 3600  # seconds
date_time_format = "%a %b %d %Y - %H:%M:%S"

if __name__ == "__main__":

    # Chrome driver options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--log-level=3")

    # Hard code for now
    chromedriver_path = r'C:\Programming\YYCErWaitTimes\chromedriver_win32\chromedriver.exe'
    url = "https://www.albertahealthservices.ca/waittimes/waittimes.aspx"

    # Run forever
    while True:

        driver = webdriver.Chrome(chrome_options=options, executable_path=chromedriver_path)

        # Get page and wait for JS to load
        driver.get(url)
        time.sleep(3)

        # Grab the HTML
        page = driver.page_source

        driver.quit()

        # Put it in the parser
        doc = BeautifulSoup(page, "html.parser")

        # Grab Calgary area only
        # TODO: Expand to Edmonton
        div_calgary = doc.find("div", class_="cityContent-calgary")
        calgary_hospitals_div = div_calgary.find_all(class_="hospitalName")
        wait_times_div = div_calgary.find_all(class_="wt-times")

        hospitals = []
        wait_times = []

        # Capture hospital names
        for hospital in calgary_hospitals_div:
            hospitals.append(hospital.find("a").contents[0])

        # Capture wait times for each hospital
        for wait_time in wait_times_div:

            wait_time_strong_tags = wait_time.find_all("strong")
            if len(wait_time_strong_tags) == 2:
                hours_wait = int(wait_time_strong_tags[0].string)
                minutes_wait = int(wait_time_strong_tags[1].string)
                wait_times.append(hours_wait*60 + minutes_wait)
            else:
                wait_times.append(None)

        # Combine data with current time
        hospitals_and_wait_times = dict(zip(hospitals, wait_times))
        now = datetime.datetime.now().strftime(date_time_format)
        current_time = {"time_stamp": now}
        result = {**current_time, **hospitals_and_wait_times}

        # Output to csv file, this is the header of the file
        fields = list(result.keys())

        # Create new file if one not exists
        if not os.path.isfile(stats_file_name):
            with open(stats_file_name, 'w') as fout:
                writer = csv.DictWriter(fout, fieldnames=fields)
                writer.writeheader()
                writer.writerows([result])

        # Otherwise append data
        else:
            with open(stats_file_name, 'a') as fout:
                writer = csv.DictWriter(fout, fieldnames=fields)
                writer.writerows([result])

        # Wait to poll again
        print(f"Polled website at: {now}.  Waiting {polling_interval} seconds.")
        time.sleep(polling_interval)
