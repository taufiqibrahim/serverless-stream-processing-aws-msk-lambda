# Walkthrough

## 1 System Design
TODO

## 2 AWS Infrastructure Requirements
- AWS VPC
- Running AWS MSK cluster inside VPC
- S3 deployment bucket which is stored in AWS_S3_DEPLOYMENT_BUCKET
- Lambda execution role
- Lambda security group 

This document does not specify on how to create AWS VPC and MSK cluster. You can find the details on https://docs.aws.amazon.com/msk/latest/developerguide/getting-started.html.

More detail regarding on using AWS MSK with Lambda here https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html

### Create Lambda Execution Role
- Go to AWS IAM > Roles
- Create role
- Choose a use case = Lambda
- Next: Permissions
- Attach permissions policies. In the search box, enter the policy name `AWSLambdaMSKExecutionRole`
- Create new role with name `AWSLambdaMSKDemoWalkthroughRole`

### Create Lambda Security Group
We also need to create Security Group with inbound access to AWS MSK.
- Go to AWS EC2 > Security Groups
- Create Security Group
    - Security group name: `AWSLambdaMSKDemoWalkthroughSG`
    - Description: AWSLambdaMSKDemoWalkthroughSG
    - VPC: same VPC ID with your MSK cluster
    - Inbound rules:
        - Custom TCP 9092 with Source = Anywhere

## 3 Creating Orders Kafka Topic

Let's create our simple JSON topic called `demo-walkthrough-orders` inside AWS MSK cluster. We will use a versatile tool called kafkacat https://github.com/edenhill/kafkacat. Since AWS MSK cluster deployed inside a private VPC, we must invoke the command on a bastion host or accessible EC2 which can access MSK.

```bash
kafkacat -P -b <BOOTSTRAP_SERVERS_URLS> -t demo-walkthrough-orders -K: -l orders-data.txt
```

## 4 Initialize Stream Processing demo-walkthrough App

First we install Serverless Framework globally.
```bash
npm install -g serverless
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


## Creating Functions

### 
