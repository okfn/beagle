# Beagle

Beagle is software used to track changes to web resources and send out reminder emails. It reads site urls from a MongoDB database and runs a scraper (called beagleboy) to check if the sites have changed. It also looks at resources linked to by the site (in case content is being served with an iframe, swf file etc.).

Beagle is intended to be a backend service that reminds users and saves changes into a database. A front end service manages the rest of the user facing service by working from the same database.

The front end service that has been developed in collaboration with Beagle is [Aquarium](http://github.com/okfn/aquarium).

## Installation

The recommended way to install the software is to use a virtual environment and assumes you have installed [virtualenv](http://www.virtualenv.org/) and [git](http://git-scm.com/):

    > git clone https://github.com/tryggvib/beagle.git
    > cd beagle
    > virtualenv venv
    > source venv/bin/activate
    > pip install -r requirements.txt

## Usage

### Beagleboy

The scraper is a python software built on [scrapy](http://scrapy.org) and is used like a scrapy scraper.

This assumes you're in the beagle directory (from step 2 in the installation). If you haven't activated the virtual environment (assuming you called it venv) start py activating it:

    > source venv/bin/activate

Then to run beagleboy you initially have to put in your email server settings in beagleboy/settings.py after that it's always the same:

    > scrapy crawl webresources

#### Database structure

Beagleboy fetches the sites from a user collection in the MongoDB database (database name defaults to beagle). A *users* collection document has the following structure:

    {
        _id: <email address of user, e.g. 167-671@beagleboys.com>,
        name: <name of user, e.g. Bigtime Beagle>,
        sites: [
                {
                      title: <title of site>
                      url: <url of a budget page to be scraped / not scraped if null>
                      last_modified: <date when change was last seen>
                },
               ]
    }

So to add a page that should be scraped one only needs to push a document like:

    {
        url: 'http://scrooge.mcduck.com'
    }

to a specific users sites array. Beagleboy will pick this up and notify that particular user when a change is noticed in the url.

#### Running Beagleboy

Since Beagleboy is built using [scrapy](http://scrapy.org) it can use [scrapyd](http://scrapyd.readthedocs.org/en/latest/) to schedule scraping jobs with a json configuration file.

Please read the documentation on scrapyd but it's really easy. You install it. It exposes a webservice where you can schedule scraping via a curl request. This would be the curl request for beagleboy

    > curl http://localhost:6800/schedule.json -d project=beagleboy -d spider=webresources

You can expose the scrapyd web server if you want but then you should definitely put in some authentication.

Another way is to run Beagleboy via a scheduler. The file scheduler.py has a cron job that runs the scraper on the last day of the month.

#### Generic Reminder

Just as Beagleboy can be run via scheduler there's another scheduled task in scheduler.py which calls a function in reminder.py to send out emails to all users.

The emails get sent to users who are assigned to sites that are active and where the day of execution (scheduled call) is somewhere between the publication date and a grace period (default 4 weeks).

This sends out regular reminder emails (once per week) around the dates of publication. The emails are sent out irrespectively of whether url is null or not.

## Hacking on Beagle

### Email templates

Beagle sends out emails to users to notify them of changes or as reminders. These emails are handled by *beaglemail* and the email templates can be found in a directory called *templates* as part of the *beaglemail* module and use the *.email* suffix.

The email templates are based on [jinja2](http://jinja.pocoo.org/2/) but have some noteworthy *quirks*:

* First line is always the subject line the remaining lines are the body
* A template parameter called *output* can be set to *html* to ask for html email output
    * Template should also return plain text content (ignore the *output* parameter)
    * Subject line rule (first line) also applies for html version
    * Yes, this makes them slightly harder to read unless template designer wants to repeat text blocks (just remember the DRY rule of thumb)
* Templates will get translated so be sure to wrap text in jinja *{% trans %}* blocks

### Translation process

1. Extract messages
2. Initialise or update translations files
3. Translate
4. Compile translations

The process assumes you're in the beagle directory as described in step 2 of the installation.

#### Extracting messages

Even though all messages are stored in beagleboy/messages.py pybabel works on directories so to extract the run the following command

    > pybabel extract -F babel.cfg -o locale/beagle.pot .

#### Initialise or update translations

If you want to create a new language to translate messages into you need to initialise it with the following command (where language code is something like is_IS):

    > pybabel init -D beagle -i locale/beagle.pot -d locale/ -l <language code>

However if you're updating a translation you don't have to initialise the language but update it with the following command (again where language code is something like en_GB):

    > pybabel update -D beagle -i locale/beagle.pot -d locale/ -l <language code>

If you want to update all locales at the same time you can skip the *-l <language code>*

#### Translate

Translate with your favourite po file translator, e.g. [poedit](http://www.poedit.net/). The project can also be uploaded to Transifex with little effort (not supported at the moment). The po file to be translated will be available in locale/<language code>/LC_MESSAGES/beagle.po

#### Compile translations

To compile translations (and thus make them available to the software) one just runs the following command:

    > pybabel compile -D beagle -d locale/

This compiles all of the translations in one go and everybody is happy.

## License

Beagle is released under the [GNU General Public License version 3 or later](http://www.gnu.org/licenses/).
