"""Module to capture ER wait data from various hospitals in Alberta."""

import time
import datetime
from pytz import timezone
import os
import csv
import certifi
from pymongo import MongoClient
from bs4 import BeautifulSoup
from tempfile import mkdtemp
# from headless_chrome import create_driver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

DATE_TIME_FORMAT = "%a %b %d %Y - %H:%M:%S"
MINUTES_PER_HOUR = 60

# ER Wait times URL for alberta
ROOT_URL = "https://www.albertahealthservices.ca"
URL = f"{ROOT_URL}/waittimes/waittimes.aspx"

# Appears to have changed July 5, 2023
# URL = "https://www.albertahealthservices.ca/waittimes/Page14230.aspx"

MONGO_CLIENT_URL = os.environ["MONGO_DB_URL"]
DB_NAME = 'erWaitTimesDB'

class ErWait:
    """Class to capture data of a specific city. It is intended to run as separate threads."""

    def __init__(self, city):

        if city.lower() == "calgary" or city.lower() == "edmonton":
            self.city = city
        else:
            raise ValueError('City should either be "Calgary" or "Edmonton"')

        # Chrome driver options
        # self.options = Options()
        # self.options.add_argument('--headless')
        # self.options.add_argument('--disable-gpu')
        # self.options.add_argument("--log-level=3")
        # self.options.add_argument('--no-sandbox')

        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-dev-tools')
        self.options.add_argument('--remote-debugging-port=9222')
        self.options.add_argument(f"--user-data-dir={mkdtemp()}")
        self.options.add_argument(f"--data-path={mkdtemp()}")
        self.options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        self.options.add_argument('--window-size=1280x1696')
        self.options.add_argument('--user-data-dir=/tmp/chrome-user-data')
        self.options.add_argument('--single-process')
        self.options.add_argument("--no-zygote")
        self.options.add_argument('--ignore-certificate-errors')
        self.options.binary_location = "/opt/chrome/chrome"

        self.stats_file_name = f"{self.city}_hospital_stats.csv"

    # -------------------------------------------------------------------------------------------------

    def _get_wait_page_url(self, driver, wait_secs):
        '''Post July5/2023 - Main URL has changed, search to get wait times URL via blue button.
        :param: driver (chrome) - Web driver
        :param: wait_secs (int) How many seconds to wait after the driver has launched.  3 secs seems good.
        "return: The URL for the wait times page (str)'''

        print("Getting wait URL page, please wait...")
        driver.get(URL)
        time.sleep(wait_secs)

        # Grab the HTML and stop driver
        page = driver.page_source

        try:
            # Put it in the parser
            doc = BeautifulSoup(page, "html.parser")
        except Exception as e:
            msg = f"Exception happened in {self.city} _get_wait_page_url() BeautifulSoup()."
            print(msg)
            raise

        temp = doc.find("a", class_=f"btn btn-primary btn-lg in-btn-blue")
                                     
        href = temp['href']

        WAIT_URL = ROOT_URL + href

        print(f"Got page URL: {WAIT_URL}")

        return WAIT_URL

    # -------------------------------------------------------------------------------------------------

    def _run_driver(self, wait_secs):
        """Runs the Chrome webdriver and returns the HTML of the page (doc) of URL.
        :param: wait_secs (int) How many seconds to wait after the driver has launched.  3 secs seems good.
        :return: page HTML source (str)"""

        print("Spooling up new driver...")
        driver = webdriver.Chrome(service=Service(r'/opt/chromedriver'), options=self.options)
        # driver = create_driver()
        print("Installation of driver complete")
        WAIT_URL = self._get_wait_page_url(driver, wait_secs)

        # Get page and wait for JS to load
        print(f"Obtaining data from: {WAIT_URL} for {self.city}.")
        driver.get(WAIT_URL)
        time.sleep(wait_secs)
        print(f"Data obtained for {self.city}.")

        # Grab the HTML and stop driver
        page = driver.page_source
        driver.quit()

        return page

    # -------------------------------------------------------------------------------------------------

    def _get_div_city(self, doc):
        """Returns a div of the city containing the hospital data.
        :param: doc (str) The HTML source of the page
        :return: doc.find() (str) of the city of the hospital."""

        return doc.find("div", class_=f"cityContent-{self.city.lower()}")

    # -------------------------------------------------------------------------------------------------

    def _get_wait_data(self, doc):
        """Returns the hospital name, wait time, and current time stamp.
        :param: doc (str) The HTML source of the page
        :return: (dict) containing current time and wait data."""

        hospitals = []
        wait_times = []
        div_city = self._get_div_city(doc)
        city_hospitals_div = div_city.find_all(class_="hospitalName")
        wait_times_div = div_city.find_all(class_="wt-times")

        for hospital, wait_time in zip(city_hospitals_div, wait_times_div):

            try:
                hospitals.append(hospital.find("a").contents[0].replace('.', '*'))
            except Exception as e:
                msg = f"Exception happened in {self.city} _get_wait_data()." \
                      f"  Trying to append {hospital} in {city_hospitals_div}."
                print(msg)
                print(e)
                hospitals.append(None)
                wait_times.append(None)
                continue

            wait_time_strong_tags = wait_time.find_all("strong")

            if len(wait_time_strong_tags) == 2:
                try:
                    hours_wait = int(wait_time_strong_tags[0].string)
                    minutes_wait = int(wait_time_strong_tags[1].string)
                    wait_times.append(hours_wait * MINUTES_PER_HOUR + minutes_wait)
                except Exception as e:
                    msg = f"Exception happened in {self.city} _get_wait_data()." \
                          f"  Trying to gather wait data: {wait_time_strong_tags} in {wait_times_div}."
                    print(msg)
                    print(e)
                    wait_times.append(None)
                    continue
            else:
                wait_times.append(None)

        wait_data = dict(zip(hospitals, wait_times))
        now = datetime.datetime.now(timezone('Canada/Mountain')).strftime(DATE_TIME_FORMAT)
        current_time = {"time_stamp": now}

        return {**current_time, **wait_data}, now

    # -------------------------------------------------------------------------------------------------

    def _write_csv(self, data):
        """Writes data to CSV file.
        :param: data (dict) Data to be written to csv file.  File name of csv file is dictated in the constructor.
        :return: None"""

        # Output to csv file, this is the header of the file
        fields = list(data.keys())

        # Create new file if one not exists
        if not os.path.isfile(self.stats_file_name):
            with open(self.stats_file_name, 'w') as fout:
                writer = csv.DictWriter(fout, fieldnames=fields)
                writer.writeheader()
                writer.writerows([data])

        # Otherwise append data
        else:
            with open(self.stats_file_name, 'a') as fout:
                writer = csv.DictWriter(fout, fieldnames=fields)
                writer.writerows([data])

    # -------------------------------------------------------------------------------------------------

    def _write_db(self, data):
        """Writes data to mongo db.
        :param: data (dict) Data to be written to db.
        :return: None"""

        try:
            db_client = MongoClient(MONGO_CLIENT_URL, tlsCAFile=certifi.where())
            db = db_client[DB_NAME]
            city_collection = db[self.city]
            city_collection.insert_one(data)
            db_client.close()

        except Exception as e:
            msg = f"Exception happened in _write_db() for {self.city} writing data {data}."
            print(msg)

    # -------------------------------------------------------------------------------------------------

    def capture_data(self):
        """Runs once capturing ER wait time data for the particular city.
        :param: None
        :return: None"""


        # Intentional delay to handle both city web-drivers accessing at the same time
        if self.city.lower() == "calgary":
            time.sleep(30)

        try:
            # Grab the HTML
            page = self._run_driver(3)

        # If an exception happens, just skip it for this iteration and continue
        except Exception as e:
            msg = f"Exception happened in {self.city} capture_data() _run_driver()."
            print(msg)
            raise

        try:
            # Put it in the parser
            doc = BeautifulSoup(page, "html.parser")
        except Exception as e:
            msg = f"Exception happened in {self.city} capture_data() BeautifulSoup()."
            print(msg)
            raise

        # Combine data with current time
        wait_data, now = self._get_wait_data(doc)
        print(wait_data)

        # Output to csv file
        # TODO: Comment out in production
        #self._write_csv(wait_data)

        # Output to db
        self._write_db(wait_data)

    # -------------------------------------------------------------------------------------------------


def capture_data(event=None, context=None):

    city = event['city']

    city_data = ErWait(city)

    # calgary_data = ErWait("Calgary")
    # edmonton_data = ErWait("Edmonton")

    print(f"Data capturing staring for {city}.")
    city_data.capture_data()

    # calgary_data.capture_data()
    # edmonton_data.capture_data()

    return {'result': 0}



# from selenium import webdriver
# from tempfile import mkdtemp
# from selenium.webdriver.common.by import By


# def handler(event=None, context=None):
#     options = webdriver.ChromeOptions()
#     options.binary_location = '/opt/chrome/chrome'
#     options.add_argument('--headless')
#     options.add_argument('--no-sandbox')
#     options.add_argument("--disable-gpu")
#     options.add_argument("--window-size=1280x1696")
#     options.add_argument("--single-process")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-dev-tools")
#     options.add_argument("--no-zygote")
#     options.add_argument(f"--user-data-dir={mkdtemp()}")
#     options.add_argument(f"--data-path={mkdtemp()}")
#     options.add_argument(f"--disk-cache-dir={mkdtemp()}")
#     options.add_argument("--remote-debugging-port=9222")
#     driver = webdriver.Chrome("/opt/chromedriver",
#                               options=options)