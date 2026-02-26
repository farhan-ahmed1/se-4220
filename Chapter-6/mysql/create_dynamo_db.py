'''
MIT License

Copyright (c) 2019 Arshdeep Bahga and Vijay Madisetti

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
import os
import boto3
import dotenv
dotenv.load_dotenv()

aws_acess_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_region = os.environ.get("AWS_REGION_NAME")

PHOTOS_TABLE = 'photogallery'
USERS_TABLE  = 'photogallery_users'

dynamodb = boto3.client('dynamodb',
                        aws_access_key_id=aws_acess_key,
                        aws_secret_access_key=aws_secret,
                        region_name=aws_region)

# ── Existing table names ──────────────────────────────────────────────────────
existing = [t['TableName'] for t in dynamodb.list_tables()['TableNames']
            if t in [PHOTOS_TABLE, USERS_TABLE]] if False else \
           dynamodb.list_tables()['TableNames']


def create_table_if_missing(name, key_schema, attribute_definitions):
    if name in existing:
        print(f"Table '{name}' already exists — skipping.")
        return
    print(f"Creating table '{name}' ...")
    dynamodb.create_table(
        TableName=name,
        KeySchema=key_schema,
        AttributeDefinitions=attribute_definitions,
        BillingMode='PAY_PER_REQUEST',
    )
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName=name)
    desc = dynamodb.describe_table(TableName=name)['Table']
    print(f"  Status : {desc['TableStatus']}")
    print(f"  ARN    : {desc['TableArn']}")


# ── photogallery: user_id (PK) + photo_id (SK) ───────────────────────────────
create_table_if_missing(
    PHOTOS_TABLE,
    key_schema=[
        {'AttributeName': 'user_id',  'KeyType': 'HASH'},
        {'AttributeName': 'photo_id', 'KeyType': 'RANGE'},
    ],
    attribute_definitions=[
        {'AttributeName': 'user_id',  'AttributeType': 'S'},
        {'AttributeName': 'photo_id', 'AttributeType': 'S'},
    ],
)

# ── photogallery_users: username (PK) ────────────────────────────────────────
create_table_if_missing(
    USERS_TABLE,
    key_schema=[
        {'AttributeName': 'username', 'KeyType': 'HASH'},
    ],
    attribute_definitions=[
        {'AttributeName': 'username', 'AttributeType': 'S'},
    ],
)

print("\nDone. Both tables are ready.")


