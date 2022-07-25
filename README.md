# ERWaitTimes
A hobby project as an introduction to self-taught data science.  It is a web scraping app to plot ER wait times in Alberta.

## Table of Contents

1. [Background Information](#background-inforomation)
2. [Local Setup](#local-setup)
3. [MongoDB](#mongodb)
4. [Running Dash Server](#running-dash-server)
5. [Heroku Deployment](#heroku-deployment)

## Background Information

Data was collected on my local machine before being published to [Heroku](#heroku-deployment).  The app uses the following:

* Python 3.9.7
* Data captured every hour for each city/hospital.
* Plotly and Dash for visual display of the ER wait data.
* MongoDB for storage and retrieval of the data.
  * Prior to MongoDB, data was collected in .csv files.
* A trial [Twilio](https://www.twilio.com/) account to send SMS messages if exceptions happen during production.  SMS messages are sent to my phone number only.
* Environment variables for safekeeping of the MongoDB cloud URL and Twilio account information

Data is captured for all available Calgary and Edmonton hospitals.  Web scraping of the data is captured from here:

https://www.albertahealthservices.ca/waittimes/waittimes.aspx
 
Additional cities in Alberta can be added as a future update to the project.

Note: There is no retrospective data; data is only available from when I started collecting in May/June 2022 and is subject to outages beyond my control.

Data is visualized as follows:

* Line plots of the ER wait time as a function of every hour.
* A table showing the average and standard deviation of all data points for each hospital
* Violin sub-plots (kernel density plots) of each hospital in a 24-hour period
* Complete violin and table data for each hospital hour (average and standard deviation) when clicking on the hyperlink of the hospital name in the violin sub-plot
  * A sinusoid (cosine) model "best fit curve" and equation is shown for each hospital's violin 24-hour period

Interactive features include:
* Viewing the page/plots in light or dark mode
* Comping a rolling average (boxcar filter) based on input hours selected
* Selecting date ranges by clicking relative time buttons
* Enabling/disabling hospitals in the legend
* Click-dragging zoom levels for all plots
* Toolbar control features (save as .png, zoom control, etc.)

Webpage is best viewed on a desktop PC, however it is supported for mobile.  For best results, please rotate phone to landscape orientation. 

## Local Setup

**Note:** The instructions below are for a Windows platform using Python 3.9.X.

### Project Directory

Create a folder on your PC to host the project files.  Navigate to the root folder and open a command window ```(Windows Key + cmd.exe)``` at this location.

### Environment Variables

The following environment variables are to be set by pressing ```Windows Key``` and typing ```path``` and hit enter.  Then select ```Environment Variables...```.  In the bottom half of the window under "System variables", click ```New...``` and add the following environment variables:

* ```MONGO_DB_URL```
* ```TWILIO_ACCOUNT_SID```
* ```TWILIO_AUTH_TOKEN```
* ```MY_TWILIO_NUM```
* ```MY_PHONE_NUM```

Click ```OK``` for this to take effect.

**<span style="color:red">IMPORTANT!</span>**  Updating environment variables for the OS requires new instances of command windows (e.g. ```cmd.exe```) to be openend, and/or IDEs like PyCharm or VS Code to be restarted.

### Virtual Environment

Create the virtual environment in the root folder by running the following command:

```
python -m venv waittimes
```

For Windows, this means going into the ```waittimes\Scripts``` folder(by using the ```cd``` command in ```cmd.exe```) and running ```activate``` via command prompt.  Now this command prompt has ```(waittimes)``` in it and is the virtual environment for this project, only containing the dependencies required for it (i.e. those from [requirements.txt](requirements.txt)).

### PIP Dependencies

Once you have your virtual environment setup and running, install dependencies by navigating to the root directory in the command window (```cd..``` twice) and running:

```
pip install -r requirements.txt
```

This will install all of the required packages we selected within the `requirements.txt` file.

## MongoDB

[MongoDB](https://www.mongodb.com/) is the cloud host for my data.  It can be run locally at:

[mongodb://127.0.0.1:27017](mongodb://127.0.0.1:27017)

Start the local mongo servers with the following in seperate ```cmd.exe``` windows:

run ```mongod```

run ```mongo```

run ```mongosh```

All of these tools have their ```PATH``` set from:

```C:\Program Files\MongoDB\Server\5.0\bin```

```C:\Program Files\MongoDB\Tools\100\bin```


### Importing CSV files to MongoDB

Data is imported from the CSV file by following these instructions:

1. Copy and paste the ```Calgary_hospital_stats.csv``` and the  ```Edmonton_hospital_stats.csv``` in the same folder which will create ```Calgary_hospital_stats - Copy.csv``` and ```Edmonton_hospital_stats - Copy.csv```.
2. Open each copied ```.csv``` file in ```notepad++``` and press ```CTRL+H``` (to find/replace).  Find all instances of ```\r\r``` and replace with ```\r```.  Save these files and close ```notepad++```.
3. Open the updated ```.csv``` files in ```Excel```, and simply save these files in Excel to properly format them as csv files that ```mongoimport``` can recognize.

Next, open a command window ```cmd.exe``` and run  the following commands to populate the MongoDB on the cloud:

```
mongoimport --uri mongodb+srv://<USERNAME>:<PASSWORD>@cluster0.chujx.mongodb.net/erWaitTimesDB --collection Calgary --type=csv --headerline --maintainInsertionOrder --file "Calgary_hospital_stats - Copy.csv"
mongoimport --uri mongodb+srv://<USERNAME>:<PASSWORD>@cluster0.chujx.mongodb.net/erWaitTimesDB --collection Edmonton --type=csv --headerline --maintainInsertionOrder --file "Edmonton_hospital_stats - Copy.csv"
```

If just populating the localhost, removing the ```--uri``` option will allow the local database to be populated.

## Running Dash Server

Run the dashboard as:

```
python dash_er_wait.py
```

The server will start at [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

## Heroku Deployment

The app is located at: https://alberta-er-wait-times.herokuapp.com/
