# CMPUT404-project-socialdistribution

CMPUT404-project-socialdistribution

See [the web page](https://uofa-cmput404.github.io/general/project.html) for a description of the project.

Make a distributed social network!

# API Documentation

To access our swagger documentation for our API, go to `/api/v1/swagger` at any deployed/local app.

[Example of deployed documentation here](https://we-love-programming-node1-873dc2b46eb5.herokuapp.com/api/v1/swagger/).

# Deployments

➡️ See [this wiki](https://github.com/uofa-cmput404/w24-project-we-love-programming/wiki/How-to-Deploy) on how to deploy this app.

➡️ See [this wiki](<https://github.com/uofa-cmput404/w24-project-we-love-programming/wiki/Connecting-to-our-node-(and-vice-versa)>) on how to connect with our app.

Currently deployed apps are:

1. https://we-love-programming-node2-c6c1b9ebb4a6.herokuapp.com/
2. https://vedantwlp-0914b68a2c0a.herokuapp.com/
3. https://we-love-programming-node1-873dc2b46eb5.herokuapp.com/

# Running app locally

## Database

_Note: This should be setup before your backend or else you will run into an error later._

**Create Postgres database**

Make sure you have postgreSQL and downloaded, if not check out [the download page](https://www.postgresql.org/download/). Install it with [pgAdmin](https://www.pgadmin.org/) if possible, it's a GUI for creating/accessing the database. In pgAdmin or the terminal, create a postgreSQL database for local development.

## REST Api and Front-end

_Requires python version 3+_

**For first time setup:**

1. From the root of the repo, create a virtual environment by running `python -m venv venv`
2. Activate virtual environment by running `source venv/bin/activate` (Mac/unix) or `venv/Scripts/activate` (Windows)
3. Install packages by running `pip install -r requirements.txt`
4. Create a `.env` file at the `/app` directory. Copy the content of `.env.example` into your `.env` and fill the values according to the DB you created.

_To run django server after setup:_

1. Activate virtual environment (see step 3 above)
2. run `cd app`
3. Run `python manage.py migrate` to apply any changes to models
4. Run `python manage.py runserver` to start django server

# Tests

Tests are written for the API of this app. They can be found in `app/api/tests`. To run the tests, run (From the root of the project):

```
cd app
python app/manage.py test api.tests
```

# AJAX

Ajax is used at the frontend in `app/client`. It is used:

- In the home/stream page of our app. This will poll every 5 seconds and check for new post that the user can see. The implementation can be found in `app/client/templates/home/index.html`
- During the background. We poll for any new inbox items every 10 seconds at every page of the frontend. The implementation can be found in `app/static/js/notifications.js` and `app/client/templates/base.html`

# Contributing

1. JiaXian Tan
2. Muzammil Arshad
3. Anurag Chopra
4. Vedant Talati
5. Jordan Isaac

# Contributors / Licensing

Generally everything is LICENSE'D under the Apache 2 license by Abram Hindle.

All text is licensed under the CC-BY-SA 4.0 http://creativecommons.org/licenses/by-sa/4.0/deed.en_US

Contributors:

    Karim Baaba
    Ali Sajedi
    Kyle Richelhoff
    Chris Pavlicek
    Derek Dowling
    Olexiy Berjanskii
    Erin Torbiak
    Abram Hindle
    Braedy Kuzma
    Nhan Nguyen

# Referenced source code

- https://stackoverflow.com/a/38044377 in `validation.py` for retrieving username and password from auth header
