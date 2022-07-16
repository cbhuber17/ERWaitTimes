"""Module to capture ER wait data from various hospitals in Alberta."""

import time
import datetime
import threading
import os
import csv
from send_sms import sms_exception_message
from pymongo import MongoClient
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

POLLING_INTERVAL = 3600  # seconds
DATE_TIME_FORMAT = "%a %b %d %Y - %H:%M:%S"
MINUTES_PER_HOUR = 60

# ER Wait times URL for alberta
URL = "https://www.albertahealthservices.ca/waittimes/waittimes.aspx"

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
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument("--log-level=3")

        self.stats_file_name = f"{self.city}_hospital_stats.csv"

    # -------------------------------------------------------------------------------------------------

    def _run_driver(self, wait_secs):
        """Runs the Chrome webdriver and returns the HTML of the page (doc) of URL.
        :param: wait_secs (int) How many seconds to wait after the driver has launched.  3 secs seems good.
        :return: page HTML source (str)"""

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

        # Get page and wait for JS to load
        driver.get(URL)
        time.sleep(wait_secs)

        # Grab the HTML and stop driver
        page = driver.page_source
        driver.quit()

        return page

    # -------------------------------------------------------------------------------------------------

    def _get_div_city(self, doc):
        """Returns a div of the city containing the hospital data.
        :param: doc (str) The HTML source of the page
        :return: doc.find (str) of the city of the hospital."""

        return doc.find("div", class_=f"cityContent-{self.city.lower()}")

    # -------------------------------------------------------------------------------------------------

    def _get_hospitals(self, doc):
        """Returns a list of hospitals available that have ER wait times.
        :param: doc (str) The HTML source of the page
        :return: A list of hospitals (list)"""

        hospitals = []

        div_city = self._get_div_city(doc)
        city_hospitals_div = div_city.find_all(class_="hospitalName")

        # Capture hospital names
        for hospital in city_hospitals_div:
            # Mongo restrictions https://www.mongodb.com/docs/manual/reference/limits/#Restrictions-on-Field-Names
            # No dots (.) in field names (column names)
            hospitals.append(hospital.find("a").contents[0].replace('.', '*'))
        return hospitals

    # -------------------------------------------------------------------------------------------------

    def _get_wait_times(self, doc):
        """Returns a list of wait times (in minutes) for each hospital.
        :param: doc (str) The HTML source of the page
        :return: A list of wait times (in minutes)"""

        wait_times = []
        div_city = self._get_div_city(doc)

        wait_times_div = div_city.find_all(class_="wt-times")

        # Capture wait times for each hospital (in minutes to keep it simple)
        for wait_time in wait_times_div:

            wait_time_strong_tags = wait_time.find_all("strong")

            if len(wait_time_strong_tags) == 2:
                hours_wait = int(wait_time_strong_tags[0].string)
                minutes_wait = int(wait_time_strong_tags[1].string)
                wait_times.append(hours_wait * MINUTES_PER_HOUR + minutes_wait)
            else:
                wait_times.append(None)

        return wait_times

    # -------------------------------------------------------------------------------------------------

    def _zip_data_and_current_time(self, data1, data2):
        """Helper function to zip two lists and a dictionary of the current time in one dict.
        :param: data1 (list)
        :param: data2 (list)
        :return: a zipped dict of data1, dat2, and the current time."""

        temp = dict(zip(data1, data2))
        now = datetime.datetime.now().strftime(DATE_TIME_FORMAT)
        current_time = {"time_stamp": now}

        return {**current_time, **temp}, now

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
            db_client = MongoClient(MONGO_CLIENT_URL)
            db = db_client[DB_NAME]
            city_collection = db[self.city]
            city_collection.insert_one(data)
            db_client.close()

        except Exception as e:
            msg = f"Exception happened in _write_db() for {self.city} writing data {data}."
            sms_exception_message(msg, e)

    # -------------------------------------------------------------------------------------------------

    def capture_data(self):
        """Runs forever capturing ER wait time data for the particular city.  Ideally to be run as a separate thread
        process.
        :param: None
        :return: None"""

        # Run forever
        while True:

            # Intentional delay to handle both city web-drivers accessing at the same time
            if self.city.lower() == "calgary":
                time.sleep(1)

            try:
                # Grab the HTML
                page = self._run_driver(3)

            # If an exception happens, just skip it for this iteration and continue
            except Exception as e:
                msg = f"Exception happened in {self.city} capture_data().  Waiting {POLLING_INTERVAL} to try again."
                sms_exception_message(msg, e)
                time.sleep(POLLING_INTERVAL)
                continue

            # Put it in the parser
            doc = BeautifulSoup(page, "html.parser")

            hospitals = self._get_hospitals(doc)
            wait_times = self._get_wait_times(doc)

            # Combine data with current time
            wait_data, now = self._zip_data_and_current_time(hospitals, wait_times)

            # Output to csv file
            self._write_csv(wait_data)

            # Output to db
            # TODO: Comment out in production
            self._write_db(wait_data)

            # Wait to poll again
            print(f"Thread: {threading.current_thread().name} and OS PID: {os.getpid()}.")
            print(f"Polled {self.city} website at: {now}.  Waiting {POLLING_INTERVAL} seconds.")
            time.sleep(POLLING_INTERVAL)

    # -------------------------------------------------------------------------------------------------


if __name__ == "__main__":

    calgary_data = ErWait("Calgary")
    edmonton_data = ErWait("Edmonton")

    print("Data capturing staring. Press CTRL+BREAK to terminate.")

    # Separate entity threading
    t_yyc = threading.Thread(target=calgary_data.capture_data)
    t_yeg = threading.Thread(target=edmonton_data.capture_data)

    t_yyc.start()
    t_yeg.start()

    # Threads will run forever, but this main thread keeps an eye on it
    t_yyc.join()
    t_yeg.join()
