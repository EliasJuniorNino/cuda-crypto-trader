import tweepy
import env

client = tweepy.Client(
    consumer_key=env.consumer_key,
    consumer_secret=env.consumer_secret,
    access_token=env.access_token,
    access_token_secret=env.access_token_secret,
    wait_on_rate_limit=True
)

timeline = client.get_home_timeline()
print(timeline.items())

try:
    for i in timeline:
        print(i)
except:
    pass
