import os
import uuid

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# The constants with information about the layer layout
FONTCONFIG_LINUX_PATH: str = "/opt/etc/fonts"
DOWNLOAD_LOCATION: str = "/tmp/"
TMP_FOLDER: str = f"/tmp/{uuid.uuid4()}"
CHROMEDRIVER_EXEC_PATH: str = "/opt/chromedriver"
HEADLESS_CHROMIUM_EXEC_PATH: str = "/opt/headless-chromium"
HEADLESS_CHROMIUM_LOG_LEVEL: int = 0
HEADLESS_CHROMIUM_VERBOSITY_LEVEL: int = 0

# The default parameters. Modify at your own risk.
HEADLESS_CHROMIUM_WINDOW_SIZE: str = "1280x1696"
USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
HEADLESS_CHROMIUM_PARAMS: list = [
    "--headless",
    "--no-sandbox",
    "--single-process",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--hide-scrollbars",
    "--enable-logging",
    "--ignore-certificate-errors",
    f"--log-level={HEADLESS_CHROMIUM_LOG_LEVEL}",
    f"--v={HEADLESS_CHROMIUM_VERBOSITY_LEVEL}",
    f"--window-size={HEADLESS_CHROMIUM_WINDOW_SIZE}",
    "--user-data-dir={}".format(TMP_FOLDER + "/user-data"),
    "--data-path={}".format(TMP_FOLDER + "/data-path"),
    f"--homedir={TMP_FOLDER}",
    "--disk-cache-dir={}".format(TMP_FOLDER + "/cache-dir"),
    f"--user-agent={USER_AGENT}",
]

# Need to configure the FONTCONFIG_PATH to work
os.environ["FONTCONFIG_PATH"] = FONTCONFIG_LINUX_PATH
print("FONTCONFIG_PATH configured: %s", FONTCONFIG_LINUX_PATH)


def _create_folders(tmp_folder: str = None):
    """ Created the chrome data structure under tmp_folder """
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)
        print("Created folder: %s", tmp_folder)

    tmp_user_data = tmp_folder + "/user-data"
    if not os.path.exists(tmp_user_data):
        os.makedirs(tmp_user_data)
        print("Created folder: %s", tmp_user_data)

    tmp_data_path = tmp_folder + "/data-path"
    if not os.path.exists(tmp_data_path):
        os.makedirs(tmp_data_path)
        print("Created folder: %s", tmp_data_path)

    tmp_cache_dir = tmp_folder + "/cache-dir"
    if not os.path.exists(tmp_cache_dir):
        os.makedirs(tmp_cache_dir)
        print("Created folder: %s", tmp_cache_dir)


def _configure_download_location(download_location: str = None) -> dict:
    """ Configure the download folders, if they exists """
    prefs = {}
    if download_location:
        prefs = {
            "download.default_directory": download_location,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "safebrowsing.disable_download_protection": True,
            "profile.default_content_setting_values.automatic_downloads": 1,
        }
        print("Configured download folder: %s", download_location)
    else:
        print("Download folder not configured")

    return prefs


def _convert_param_list_to_dict(param_list: list, parameters_dict: dict) -> dict:
    """ Convert the list of parameters to a list of duples (parameter,argument) """
    for param in param_list:
        param_array: list = param.split("=")
        key: str = param_array[0]
        value: str = None
        if len(param_array) > 1:
            value = param_array[1]
        parameters_dict[key] = value
    return parameters_dict


def create_driver(custom_config: list = None) -> Chrome:
    """ Returns an instance of the Chrome webdriver ready to use """

    # Create folders, if needed
    _create_folders(tmp_folder=TMP_FOLDER)

    # Configure Chromedriver and Headless Chromium
    options: Options = Options()
    options.binary_location = HEADLESS_CHROMIUM_EXEC_PATH
    print(
        "Headless Chromium binary location path: %s",
        HEADLESS_CHROMIUM_EXEC_PATH,
    )

    # Create the new dict with the combination of default and new parameters
    parameters_dict: dict = _convert_param_list_to_dict(HEADLESS_CHROMIUM_PARAMS, {})
    if custom_config is not None:
        parameters_dict: dict = _convert_param_list_to_dict(
            custom_config,
            parameters_dict,
        )

    # Convert the dict to a list of parameters for Chromium
    final_params: list = []
    for key, value in parameters_dict.items():
        if value is not None:
            final_params.append(f"{key}={value}")
        else:
            final_params.append("%s" % key)

    for param in final_params:
        options.add_argument(param)
        print("Argument passed to headless chromium: %s", param)

    experimental_prefs: dict = _configure_download_location(
        download_location=DOWNLOAD_LOCATION,
    )
    options.add_experimental_option("prefs", experimental_prefs)

    print(os.getcwd())
    print(os.listdir())
    os.chdir('..')
    print(os.getcwd())
    print(os.listdir())
    os.chdir('..')
    print(os.getcwd())
    print(os.listdir())
    os.chdir('./opt')
    print(os.getcwd())
    print(os.listdir())
    print(os.environ['PATH'])
    print(os.environ['MONGO_DB_URL'])

    driver = Chrome(service=Service(executable_path=CHROMEDRIVER_EXEC_PATH), options=options)
    # driver = Chrome(options=options)
    print("Driver chromedriver initialized in: %s", CHROMEDRIVER_EXEC_PATH)
    return driver
