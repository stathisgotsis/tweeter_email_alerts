from os.path import exists
import tweepy
import smtplib, ssl
from email.mime.text import MIMEText
import config


def send_email(sender, receivers, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)

    context = ssl._create_unverified_context()
    with smtplib.SMTP(config.settings['smtp']['server'], config.settings['smtp']['port']) as server:
        server.starttls(context=context)
        server.login(config.settings['smtp']['username'], 
        	config.settings['smtp']['password'])
        server.sendmail(sender, receivers, msg.as_string())

def read_latest_tweet_id(filepath):
    tweet_id = 0

    if not exists(filepath):
        return tweet_id

    with open(filepath, 'r') as f:
        try:
            tweet_id = int(f.readline())    
        except ValueError:
            pass
    
    return tweet_id

def write_latest_tweet_id(filepath, tweet_id):
    with open(filepath, 'w') as f:
    	f.write(str(tweet_id))    

def get_tweets(last_tweet_id):
    tweet_results = []
    latest_tweet_id = 0

    client = tweepy.Client(
        consumer_key=config.settings['twitter_keys']['api_key'], 
        consumer_secret=config.settings['twitter_keys']['api_key_secret'],
        access_token=config.settings['twitter_keys']['access_token'], 
        access_token_secret=config.settings['twitter_keys']['access_token_secret']
    )

    twitter_username = config.settings['twitter_filters']['username']
    response = client.get_user(username=twitter_username, user_auth=True)
    if not response.data:
        print("User %s not found" % twitter_username)
        return tweet_results, latest_tweet_id

    user_id = response.data.id

    response = client.get_users_tweets(id=user_id, max_results=20, exclude=['retweets','replies'], since_id=last_tweet_id, user_auth=True)
    if not response.data:
        return tweet_results, latest_tweet_id

    tweets = response.data    
    for tweet in tweets:
        if latest_tweet_id == 0:
            latest_tweet_id = tweet.id
        text = tweet.text
        text_lower = text.lower()
        for filter in config.settings['twitter_filters']['tweet_filters']:
            if filter.lower() in text_lower:
                tweet_results.append(text)

    return tweet_results, latest_tweet_id


if __name__ == "__main__":
    LATEST_TWEET_FILENAME = 'latest_tweet_id.txt'

    latest_tweet_id = read_latest_tweet_id(LATEST_TWEET_FILENAME)
    tweets, latest_tweet_id = get_tweets(latest_tweet_id)
    if latest_tweet_id != 0:
        write_latest_tweet_id(LATEST_TWEET_FILENAME, latest_tweet_id)

    for tweet in tweets:
        send_email(config.settings['email_settings']['from'], 
            config.settings['email_settings']['to'], 
            "Twitter email alert", 
            tweet)
