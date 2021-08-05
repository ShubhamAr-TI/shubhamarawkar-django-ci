# cj-app
Django 3.1.6 - Python 3.9

    PROJECT START STEPS:

    Pre-requisites:
    1. Install need python and pip to be installed in your system.


    Steps:
    1. To run this application, do the following:
        1.a. Go to the project root directory.
        1.b. Run the following commands to install dependencies of the app:
        	- pip install -r requirements.txt
        1.c. Run the following command(s) in the terminal/command line to run the app:    
            - python manage.py runserver 0.0.0.0:8080
    
    2. Go to http://localhost:8080 in your browser to view it.
    
    CLOUD-IDE SETUP STEPS(follow the below steps in case you are using the Cloud IDE instead of your Local IDE):
	1. Please run the below commands from the project root to setup MySQL and MongoDB in this workspace:
		- chmod 0755 ./database-setup.sh
		- sh ./database-setup.sh
	2. In case you want to connect to MySQL or MongoDB, kindly use the following credentials in your application:
		2.a. MySQL
			- host: localhost
			- port: 3306
			- username: root
			- password: admin
			- database: db
		2.b. MongoDB
			- host: localhost
			- port: 27017
			- username: root
			- password: admin
			- database: db
