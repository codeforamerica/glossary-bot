# Deploying Glossary Bot to Heroku from the command line

Follow these instructions to deploy or upgrade Glossary Bot to Heroku from the command line. You can also deploy Glossary Bot the easy way using the *Deploy to Heroku* button as described in [README](README.md)

#### Requirements

Glossary Bot is written in Python 3.6.6.

#### Install

Glossary Bot is a [Flask](http://flask.pocoo.org/) app built to run on [Heroku](https://heroku.com/).

#### Set Up on Slack

Glossary Bot uses two Slack integrations: [Slash Commands](https://api.slack.com/slash-commands) for private communication between the bot and the user, and [Incoming Webhooks](https://api.slack.com/incoming-webhooks) for posting public messages.

[Set up a Slash Command integration](https://my.slack.com/services/new/slash-commands). There are three critical values that you need to set or save: **Command** is the command people on Slack will use to communicate with the bot. We use `/gloss`. **URL** is the public URL where the bot will live; **LEAVE THIS PAGE OPEN** so that you can fill this in after you've deployed the application to Heroku, as described below. **Token** is used to authenticate communication between Slack and the bot; save this value for when you're setting up the bot on Heroku.

[Set up an Incoming Webhooks integration](https://my.slack.com/services/new/incoming-webhook). The first important value here is **Post to Channel**, which is a default channel where public messages from the bot will appear. This default is always overridden by the bot, but you do need to have one – we created a new channel called *#glossary-bot* for this purpose. Save the value of **Webhook URL**; this is the URL that the bot will POST public messages to, and you'll need it when setting up Gloss Bot on Heroku.

#### Deploy on Heroku

Now it's time to deploy the bot to Heroku! First, make sure you've got the basics set up by following [Heroku's instructions for getting started with Python](https://devcenter.heroku.com/articles/getting-started-with-python-o).

Clone Glossary Bot's repository and cd into the resulting directory:

```
git clone git@github.com:codeforamerica/glossary-bot.git
cd glossary-bot
```

Now, create a new Heroku application. You can give it a name: `heroku create my-glossary-bot`, or let Heroku generate one: `heroku create`. You won't see this name in Slack, it'll just be part of the URL that Slack uses to communicate with the bot behind the scenes.

```
heroku create
```

When it's done, the heroku command will output public and git URLs. When you deploy your app, it'll be reachable at the public URL; something like `https://my-glossary-bot.herokuapp.com/`. Enter this URL into the **URL** field of the Slash Commands integration on Slack. See the [Heroku documentation](https://devcenter.heroku.com/articles/getting-started-with-python-o#deploy-your-application-to-heroku) for more configuration options.

To give the bot everything it needs to communicate with Slack, set the config variables you saved when you set up the Slack integrations above. The **Token** from the Slash Command integration:

```
heroku config:set SLACK_TOKEN=1234567890
```

and the **Webhook URL** from the Incoming Webhooks integration:

```
heroku config:set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/1234567/1234567/1234567890
```

You can also set these variables in the Heroku web interface.

When you created your Heroku app, it outputted a git URL. You'll use that URL to push the application code to Heroku. If you didn't save the URL, you can get it again with the Heroku info command (replacing _my-glossary-bot_ with the name of your app):

```
heroku info --app my-glossary-bot
```

Add the git URL to your repository as a remote named "heroku":

```
git remote add heroku https://git.heroku.com/my-glossary-bot.git
```

With that command, you've connected your local copy of the Gloss Bot repository to your app on Heroku! You can verify the change like this:

```
git remote -v
```

Now run a git push to deploy the application:

```
git push heroku master
```

When that's finished, initialize the database:

```
heroku run python manage.py db upgrade
```

And you're good to get glossing! Open up Slack and type `/gloss help` to start.

#### Upgrade on Heroku

Here's what to do if you've got an older version of Gloss Bot on Heroku and want to upgrade to the latest version. First, guarantee that you've got a backup of your database by following the instructions in [Heroku's PGBackups documentation](https://devcenter.heroku.com/articles/heroku-postgres-backups).

##### If you used the Deploy To Heroku button

If you installed Gloss Bot using the *Deploy to Heroku* button, follow the steps below. If not, [skip ahead](#if-you-did-not-use-the-deploy-to-heroku-button).

First, make sure you've got the basics set up by following [Heroku's instructions for getting started with Python](https://devcenter.heroku.com/articles/getting-started-with-python-o).

Open the terminal and clone the Gloss Bot repository onto your machine:

```
git clone git@github.com:codeforamerica/glossary-bot.git
```

Then change into the resulting directory:

```
cd glossary-bot
```

Find the name of the heroku app that's running Gloss Bot by typing:

```
heroku apps
```

This'll show you a list of apps, one of which should be your Gloss Bot instance.

If you're not sure which app is the Gloss Bot app, go to [your Slack's custom integrations page](https://my.slack.com/apps/manage/custom-integrations), click into *Slash Commands*, and find the slash command you configured for Gloss Bot. It'll say something like _When a user enters /gloss, POST to https://my-cool-bot-12345.herokuapp.com/_. Whatever's in the URL in place of 'my-cool-bot-12345' is the name of your app.

Back in the terminal, get more info on the app by typing (replacing _my-cool-bot-12345_ with the name of your app):

```
heroku info --app my-cool-bot-12345
```

You'll see a list of information about the app, including its `Git URL`. Copy the URL and use it in this command:

```
git remote add heroku https://git.heroku.com/my-cool-bot-12345.git
```

With that command, you've connected your local copy of the Gloss Bot repository to your app on Heroku! You can verify the change like this:

```
git remote -v
```

Now, push the latest code to your app on Heroku:

```
git push -f heroku master
```

And upgrade the database:

```
heroku run python manage.py db upgrade --app my-cool-bot-12345
```

And your Gloss Bot has been updated!

##### If you did not use the Deploy To Heroku button

Change into your local Gloss Bot directory and pull the latest code:

```
git pull
```

Deploy it to Heroku:

```
git push heroku master
```

You may need to run database migrations to get your database current with the new version:

```
heroku run python manage.py db upgrade
```

If you get errors when you try that, you may need to stamp your database with a revision id that matches its current state. You can check whether that's the problem by connecting to your remote database:

```
heroku pg:psql
```

And in `psql`, checking for the `alembic_version` table:

```
SELECT * FROM alembic_version;
```

If that gives you an error like `ERROR:  relation "alembic_version" does not exist` then you need to create that table. First type `\q` to leave `psql`, then run this heroku command:

```
heroku run python manage.py db stamp 578b43a08697
```

That will create the `alembic_version` table and give it a value for `version_num` of `578b43a08697`, which matches [the inital database migration](https://github.com/codeforamerica/glossary-bot/blob/master/migrations/versions/578b43a08697_initial_migration.py) for the application.

Now that you've done that, you should be able to run

```
heroku run python manage.py db upgrade
```

without errors.
