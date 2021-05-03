# Serverless Stream Processing AWS MSK - Lambda
Serverless framework based stream processing using Amazon MSK and Amazon Lambda

![image info](./serverless-stream-processing-aws-msk-lambda-architecture.png)

## Pros & Cons
This framework has several pros and cons as described below:

### Pros
- Easy development and deployment
- Suitable for quick event-based architecture deployment with low-to-medium traffic
- Battle proven by AWS Lambda
- No resource to manage. You can focus totally on logic
- Pay as you use cost, depends on Lambda invocation cost
- Logging by AWS Cloudwatch
- Serverless Framework popularity and many supporting plugins
- It's just simple Python code!

### Cons
- Hard (if not impossible) to test locally, since AWS MSK deployed on secured VPC
- Only two consumer group message available, since the beginning of topic (TRIM_HORIZON) and LATEST
- Not suitable for high traffic topic
- Sometimes deployment and removal takes quite long time

## Project Directory Structures

TODO
