# Walkthrough

## 1 System Design
TODO

## 2 AWS Infrastructure Requirements
- AWS VPC
- Running AWS MSK cluster inside VPC
- S3 deployment bucket which is stored in AWS_S3_DEPLOYMENT_BUCKET
- Lambda execution role
- Lambda security group
- MySQL RDS

This document does not specify on how to create AWS VPC and MSK cluster. You can find the details on https://docs.aws.amazon.com/msk/latest/developerguide/getting-started.html.

More detail regarding on using AWS MSK with Lambda here https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html

### 2.1 Create Lambda Execution Role
- Go to AWS IAM > Roles
- Create role
- Choose a use case = Lambda
- Next: Permissions
- Attach permissions policies. In the search box, enter the policy name `AWSLambdaMSKExecutionRole`
- Create new role with name `AWSLambdaMSKDemoWalkthroughRole`

### 2.2 Create Lambda Security Group
We also need to create Security Group with inbound access to AWS MSK.
- Go to AWS EC2 > Security Groups
- Create Security Group
    - Security group name: `AWSLambdaMSKDemoWalkthroughSG`
    - Description: AWSLambdaMSKDemoWalkthroughSG
    - VPC: same VPC ID with your MSK cluster
    - Inbound rules:
        - Custom TCP 9092 with Source = Anywhere

### 2.3 Allow Inbound On MSK from Lambda Security Group
Now, we need to allow inbound from Lambda Security Group on MSK.
- Go to MSK
- Find `Security groups applied`
- Add inbound rules:
    - Self referencing inbound rule from MSK own Security groups applied
    - from Lambda Security Group on port 9092

### 2.4 Populate MySQL RDS Database

We will use MySQL database as lookup source. So we need to populate it first using SQL available on `apps/demo-walkthrough/data/mysql.sql`. It will create and populate table called `demo.customers`.

## 3 Initialize Stream Processing demo-walkthrough App

First we install Serverless Framework globally.
```bash
npm install -g serverless
```

Next, we install local dependencies as declared in `package.json`. Serverless Plugins should be declared here as well.
```bash
npm install
```

Let assume that we want to create a new stream processing application called `demo-walkthrough`. The code live inside `apps/demo-walkthrough/` directory which is currently not exist yet. We will create it using Serverless framework.

```bash
# Go inside apps/ directory
cd apps/

# Create app skeleton using serverless create
serverless create --template aws-python3 --name demo-walkthrough --path demo-walkthrough
```

Now our repository structure become like this
```bash
.
├── apps
│   └── demo-walkthrough
│       ├── handler.py
│       └── serverless.yml
```

## 4 Develop Functions

This part is where we start develop Python code used for event processing.

### 4.1 Prepare Python Virtual Environment

Let's start by creating a new Python virtual environment inside `apps/demo-walkthrough/` directory. We will develop and perform deployment in active virtual environment.

```bash
# Go into app directory
cd apps/demo-walkthrough/

# Create virtualenv if not exists
virtualenv venv --python=python3.8

# Activate
. venv/bin/activate
```

Install dependencies using `requirements.txt`.
```bash
pip install -r requirements.txt
```

### 4.2 Example p01OrdersEnrichCustomerLocation

This function:
- Takes event records from topic `demo-walkthrough-orders` as input
- Perform customer address lookup from MySQL database table `customers`
- Produce Kafka topic called `demo-walkthrough-p01OrdersEnrichCustomerLocation` with some additional enrichment fields

The demo code written in `apps/demo-walkthrough/p01OrdersEnrichCustomerLocation.py`.

Some helper functions were used and available under `utils/` directory. You can add more functions here, as it's included on `apps/demo-walkthrough/serverless.yml` config file.


## 5 Deploy Functions

On last step before deployment. We need to create a Serverless Variables stored on a JSON file.
Copy `apps/demo-walkthrough/env.example.json` and stored it as file called `apps/demo-walkthrough/env.dev.json`. This file will be ignored by `.gitignore` since it will contain credentials.

Below is the explanation for each key value pairs.

|key                         |value                                                         |description                                                     |
|----------------------------|--------------------------------------------------------------|----------------------------------------------------------------|
|AWS_S3_DEPLOYMENT_BUCKET    |my-serverless-deployment                                      |S3 bucket name                                                  |
|AWS_LAMBDA_EXECUTION_ROLE   |arn:aws:iam::<ACCOUNT_ID>:role/AWSLambdaMSKDemoWalkthroughRole|AWSLambdaMSKDemoWalkthroughRole ARN                             |
|AWS_LAMBDA_EXECUTION_TIMEOUT|300                                                           |Lambda execution timeout                                        |
|AWS_LAMBDA_MSK_BATCH_SIZE   |1000                                                          |Execution batch size                                            |
|AWS_VPC_SECURITY_GROUP_ID_1 |sg-<AWSLambdaMSKDemoWalkthroughSG>                            |Lambda security group ID                                        |
|AWS_VPC_SUBNET_ID_1         |<SUBNET_ID_1>                                                 |Lambda subnet ID 1                                              |
|AWS_VPC_SUBNET_ID_2         |<SUBNET_ID_2>                                                 |Lambda subnet ID 2                                              |
|AWS_MSK_CLUSTER_1           |<AWS_MSK_CLUSTER_1_ARN>                                       |MSK cluster ARN 1                                               |
|AWS_MSK_BOOTSTRAP_SERVERS_1 |<AWS_MSK_BOOTSTRAP_SERVERS_1_URLS>                            |MSK bootstrap server URLs 1                                     |
|AWS_MSK_CLUSTER_2           |<AWS_MSK_CLUSTER_1_ARN>                                       |MSK cluster ARN 2                                               |
|AWS_MSK_BOOTSTRAP_SERVERS_2 |<AWS_MSK_BOOTSTRAP_SERVERS_1_URLS>                            |MSK bootstrap server URLs 2                                     |
|KAFKA_STARTING_POSITION     |LATEST                                                        |Lambda MSK Kafka starting position offset [LATEST, TRIM_HORIZON]|
|ORDERS_TOPIC                |demo-walkthrough-orders                                       |Source topic                                                    |
|SCHEMA_REGISTRY_URL         |http://schema-registry-url:8081                               |Confluent Schema Registry URL                                   |
|MYSQL_CONN_STRING           |mysql+pymysql://user:password@rds_host:3306/database_name     |MySQL SQL Alchemy connection string                             |


Before continue to the next step, please make sure you're Python virtual environment is in active state.

Now let's print our `serverless.yml` config file with all variables resolved.
```bash
serverless print --stage dev
```
It should print something like this without any warning.
```bash
$ serverless print --stage dev
service:
  name: demo-walkthrough
frameworkVersion: '2'
provider:
  stage: dev
  region: ap-southeast-1
  name: aws
  runtime: python3.8
  environment:
    AWS_S3_DEPLOYMENT_BUCKET: <CREDENTIALS_OMITTED>
    AWS_LAMBDA_EXECUTION_ROLE: arn:aws:iam::<ACCOUNT_ID>:role/AWSLambdaMSKDemoWalkthroughRole
    AWS_LAMBDA_EXECUTION_TIMEOUT: '300'
    AWS_LAMBDA_MSK_BATCH_SIZE: '1000'
    AWS_VPC_SECURITY_GROUP_ID_1: sg-<CREDENTIALS_OMITTED>
    AWS_VPC_SUBNET_ID_1: subnet-<CREDENTIALS_OMITTED>
    AWS_VPC_SUBNET_ID_2: subnet-<CREDENTIALS_OMITTED>
    AWS_MSK_CLUSTER_1: arn:aws:kafka:ap-southeast-1:<CREDENTIALS_OMITTED>
    AWS_MSK_BOOTSTRAP_SERVERS_1: <CREDENTIALS_OMITTED>
    AWS_MSK_CLUSTER_2: <AWS_MSK_CLUSTER_1_ARN>
    AWS_MSK_BOOTSTRAP_SERVERS_2: <AWS_MSK_BOOTSTRAP_SERVERS_1_URLS>
    KAFKA_STARTING_POSITION: LATEST
    ORDERS_TOPIC: demo-walkthrough-orders
    SCHEMA_REGISTRY_URL: http://<CREDENTIALS_OMITTED>:8081
    MYSQL_CONN_STRING: mysql+pymysql://<CREDENTIALS_OMITTED>:3306/demo
  profile: serverless
  memorySize: 1024
  timeout: 300
  logRetentionInDays: 14
  deploymentBucket: <CREDENTIALS_OMITTED>
  iam:
    role: arn:aws:iam::<ACCOUNT_ID>:role/AWSLambdaMSKDemoWalkthroughRole
  lambdaHashingVersion: '20201221'
  vpc:
    securityGroupIds:
      - sg-<CREDENTIALS_OMITTED>
    subnetIds:
      - subnet-<CREDENTIALS_OMITTED>
  versionFunctions: true
  variableSyntax: \${([^{}:]+?(?:\(|:)(?:[^:{}][^{}]*?)?)}
custom:
  startingPosition: LATEST
  pythonRequirements:
    dockerizePip: non-linux
    slim: true
plugins:
  - serverless-python-requirements
functions:
  p01OrdersEnrichCustomerLocation:
    handler: p01OrdersEnrichCustomerLocation.main
    events:
      - msk:
          arn: arn:aws:kafka:ap-southeast-1:<CREDENTIALS_OMITTED>
          topic: demo-walkthrough-orders
          batchSize: 1000
          startingPosition: LATEST
          enabled: true
    environment:
      SERVICE: demo-walkthrough-dev-p01OrdersEnrichCustomerLocation
      TOPIC_IN: demo-walkthrough-orders
      TOPIC_OUT: demo-walkthrough-p01OrdersEnrichCustomerLocation
      KAFKA_BOOTSTRAP_SERVERS_READ: <CREDENTIALS_OMITTED>
      KAFKA_BOOTSTRAP_SERVERS_WRITE: <CREDENTIALS_OMITTED>
    package: {}
    name: demo-walkthrough-dev-p01OrdersEnrichCustomerLocation
```

If no warning, then we're good to go. Let's deploy it.
```bash
serverless deploy --stage dev
```

Let's produce our simple JSON to topic called `demo-walkthrough-orders` inside AWS MSK cluster. We will use a versatile tool called kafkacat https://github.com/edenhill/kafkacat. Since AWS MSK cluster deployed inside a private VPC, we must invoke the command on a bastion host or accessible EC2 which can access MSK.

```bash
kafkacat -P -b <AWS_MSK_BOOTSTRAP_SERVERS_URLS> -t demo-walkthrough-orders -l ./data/orders.txt
```

We will use `orders.txt` to simulate incoming events.

Now, let's check the topics

Source topic:
```bash
kafkacat -C -b <AWS_MSK_BOOTSTRAP_SERVERS_URLS> -t demo-walkthrough-orders -o -20 -e | jq -c
% Reached end of topic demo-walkthrough-orders [0] at offset 10: exiting
{"OrderNo":"SO-001","OrderDate":"1/6/19","Region":"East","Customer":"Jones","Item":"Pencil","Units":95,"Unit Cost":1.99,"Total":189.05}
{"OrderNo":"SO-002","OrderDate":"1/23/19","Region":"Central","Customer":"Kivell","Item":"Binder","Units":50,"Unit Cost":19.99,"Total":999.5}
{"OrderNo":"SO-003","OrderDate":"2/9/19","Region":"Central","Customer":"Jardine","Item":"Pencil","Units":36,"Unit Cost":4.99,"Total":179.64}
{"OrderNo":"SO-004","OrderDate":"2/26/19","Region":"Central","Customer":"Gill","Item":"Pen","Units":27,"Unit Cost":19.99,"Total":539.73}
{"OrderNo":"SO-005","OrderDate":"3/15/19","Region":"West","Customer":"Sorvino","Item":"Pencil","Units":56,"Unit Cost":2.99,"Total":167.44}
{"OrderNo":"SO-006","OrderDate":"4/1/19","Region":"East","Customer":"Jones","Item":"Binder","Units":60,"Unit Cost":4.99,"Total":299.4}
{"OrderNo":"SO-007","OrderDate":"4/18/19","Region":"Central","Customer":"Andrews","Item":"Pencil","Units":75,"Unit Cost":1.99,"Total":149.25}
{"OrderNo":"SO-008","OrderDate":"5/5/19","Region":"Central","Customer":"Jardine","Item":"Pencil","Units":90,"Unit Cost":4.99,"Total":449.1}
{"OrderNo":"SO-009","OrderDate":"5/22/19","Region":"West","Customer":"Thompson","Item":"Pencil","Units":32,"Unit Cost":1.99,"Total":63.68}
{"OrderNo":"SO-010","OrderDate":"6/8/19","Region":"East","Customer":"Jones","Item":"Binder","Units":60,"Unit Cost":8.99,"Total":539.4}
```

Output topic:
```bash
kafkacat -C -b <AWS_MSK_BOOTSTRAP_SERVERS_URLS> -t demo-walkthrough-p01OrdersEnrichCustomerLocation -o -20 -e | jq -c
% Reached end of topic demo-walkthrough-p01OrdersEnrichCustomerLocation [0] at offset 10: exiting
{"OrderNo":"SO-001","OrderDate":"1/6/19","Region":"East","Customer":"Jones","Item":"Pencil","Units":95,"Unit Cost":1.99,"Total":189.05,"address":"1745 T Street Southeast","longitude":"-76.979235","latitude":"38.867033"}
{"OrderNo":"SO-002","OrderDate":"1/23/19","Region":"Central","Customer":"Kivell","Item":"Binder","Units":50,"Unit Cost":19.99,"Total":999.5,"address":"6007 Applegate Lane","longitude":"-85.649851","latitude":"38.134301"}
{"OrderNo":"SO-003","OrderDate":"2/9/19","Region":"Central","Customer":"Jardine","Item":"Pencil","Units":36,"Unit Cost":4.99,"Total":179.64,"address":"560 Penstock Drive","longitude":"-121.077583","latitude":"39.213076"}
{"OrderNo":"SO-004","OrderDate":"2/26/19","Region":"Central","Customer":"Gill","Item":"Pen","Units":27,"Unit Cost":19.99,"Total":539.73,"address":"150 Carter Street","longitude":"-72.473091","latitude":"41.765560"}
{"OrderNo":"SO-005","OrderDate":"3/15/19","Region":"West","Customer":"Sorvino","Item":"Pencil","Units":56,"Unit Cost":2.99,"Total":167.44,"address":"2721 Lindsay Avenue","longitude":"-85.700243","latitude":"38.263793"}
{"OrderNo":"SO-006","OrderDate":"4/1/19","Region":"East","Customer":"Jones","Item":"Binder","Units":60,"Unit Cost":4.99,"Total":299.4,"address":"1745 T Street Southeast","longitude":"-76.979235","latitude":"38.867033"}
{"OrderNo":"SO-007","OrderDate":"4/18/19","Region":"Central","Customer":"Andrews","Item":"Pencil","Units":75,"Unit Cost":1.99,"Total":149.25,"address":"18 Densmore Drive","longitude":"-73.101883","latitude":"44.492953"}
{"OrderNo":"SO-008","OrderDate":"5/5/19","Region":"Central","Customer":"Jardine","Item":"Pencil","Units":90,"Unit Cost":4.99,"Total":449.1,"address":"560 Penstock Drive","longitude":"-121.077583","latitude":"39.213076"}
{"OrderNo":"SO-009","OrderDate":"5/22/19","Region":"West","Customer":"Thompson","Item":"Pencil","Units":32,"Unit Cost":1.99,"Total":63.68,"address":"637 Britannia Drive","longitude":"-122.193849","latitude":"38.104770"}
{"OrderNo":"SO-010","OrderDate":"6/8/19","Region":"East","Customer":"Jones","Item":"Binder","Units":60,"Unit Cost":8.99,"Total":539.4,"address":"1745 T Street Southeast","longitude":"-76.979235","latitude":"38.867033"}
```

To remove Serverless stack, simply run this command.
```bash
serverless remove --stage dev
```
It will remove all resources created by Serverless Framework.
