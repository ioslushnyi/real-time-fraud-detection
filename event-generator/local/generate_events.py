# Generate fake payment events and publish them to a Google Cloud Pub/Sub topic
import time
from google.cloud import pubsub_v1
from datetime import datetime, timezone
from faker import Faker
import json
import uuid
import random
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--project", default='fraud-detection-v1', help='GCP project ID')
parser.add_argument('--output_topic', default='payment-events', help='Pub/Sub topic ID for writing raw incoming events')
args = parser.parse_args()

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(args.project, args.output_topic)
fake = Faker()

# Generate a single fake payment event
def generate_fake_event():
    # assume that 90% of users are from Poland or Ukraine
    country = random.choice(["PL", "UA"]) if random.random() > 0.1 else (random.choice(["DE", "CZ", "SK", "UK"]) if random.random() > 0.5 else fake.country_code())
    # and 10% use VPN, so we can generate random country code for them
    ip_country = country if random.random() > 0.1 else fake.country_code()
    # 95 of the users are making purchases between 100 and 12000 money units, 5% are making large purchases between 10000 and 20000 money units
    amount = round(random.uniform(100, 11000), 2) if random.random() > 0.1 else round(random.uniform(10000, 20000), 2)
    # 95% of users use USD, EUR, PLN or UAH, 5% use other currencies
    currency = random.choice(["USD", "EUR", "PLN", "UAH"]) if random.random() > 0.05 else fake.currency_code()
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "amount": amount,
        "currency": currency,
        "country": country,
        "ip_country": ip_country,
        "device": random.choice(["iPhone", "Android", "Windows", "Linux", "Mac"]),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def publish_event(event):
    event_data = json.dumps(event).encode("utf-8")
    future = publisher.publish(topic_path, data=event_data)
    print(f"Published message ID: {future.result()}")

count = 0
# Generate and publish events in a loop
while count < 1000:  # Adjust the number of events as needed
    try:
        event = generate_fake_event()
        print(f"Event: {event}")
        # random burst of events for the same user (2% chance)
        if (random.random() <= 0.02 ):
            print(f"Burst event sequence triggered for user {event['user_id']}")
            for _ in range(random.randrange(5,8)):
                burst_event = event.copy()
                burst_event["event_id"] = str(uuid.uuid4())
                publish_event(burst_event)
                count += 1
                # Sleep for a short time to simulate burst
                time.sleep(3)
        else:
            publish_event(event)
            count += 1

    except Exception as e:
        print(f"Error occured when publishing event {event} \nError: {e}")
    # Wait for a while before publishing the next event
    time.sleep(random.uniform(5, 15))


print(f"Published {count} events.")
