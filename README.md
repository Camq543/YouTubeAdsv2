# YouTubeAdsv2

### Setup
You need python with the selenium package (currently need version 4.2.0, updated code will use any selenium version), and a driver for chrome found here https://chromedriver.chromium.org/downloads 

The directory containing the chrome driver must be in the environment PATH variable.

Make a folder called config, and add a config file called "computer_config.json". An example of this file can be found in the constants directory. 

You will also need a google account. Change the username and password in the config file to your google acount. To setup the driver to launch using your account:
1. Open chrome
2. Log in to the account
3. Fully exit chrome
4. Copy the "User Data" folder found in your computers chrome directory, and paste it into the main folder for this repo 
5. Change the 'user_data' entry in the config file to the copied directory (works best if you delete the spaces from the "User Data" directory name


### Running the program
The scraper is run by calling 'seed_accounts.py' This program will generate a list of videos pulled from a given video file (see constants/video_list_example.json for example), then watch the full videos to seed an account for recommendations and personalization

### To do
* Write code to manage interests (record and delete them from personal profile)
* Update to new selenium version - find_element_by_xpath is deprecated. Need to use new methods (probably best to use CSS selectors)
* Fix ad targeting info retrieval
