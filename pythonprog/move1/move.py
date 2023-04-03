import json
import boto3
from datetime import datetime,timedelta
#import pytz

def lambda_handler(event, context):
    
    event = event.get("detail")
    snsArn = 'arn:aws:sns:us-east-1:129176122008:mnrsns' # sns Topic ARN
    roleArn = 'arn:aws:iam::129176122008:role/Account-MoveBack-Lambda-Role' #role with schduler event creation access
    targetArn = 'arn:aws:lambda:us-east-1:129176122008:function:Moveback' #2nd lambda ARN
    timeDelta = 1 #in minutes

    
    reqParameters = event.get('requestParameters')
    orgClient = boto3.client('organizations')
    
    #Get Account Name Section
    MovedAccountId = reqParameters.get("accountId")
    AccountName = orgClient.describe_account(AccountId=MovedAccountId).get('Account').get('Name')
    
    #Get Source OU Section
    sourceOrgUnit = reqParameters.get("sourceParentId")
    sourceOrgUnitName = orgClient.describe_organizational_unit(
        OrganizationalUnitId=sourceOrgUnit
    ).get("OrganizationalUnit").get("Name")
    
    #Get Destination Ou Section
    destOrgUnit = reqParameters.get("destinationParentId")
    destOrgUnitName = orgClient.describe_organizational_unit(
        OrganizationalUnitId=destOrgUnit
    ).get("OrganizationalUnit").get("Name")
    
    ## ID extract section
    requestedUser = event.get("userIdentity").get("principalId").split(":")[1]
    
    #Final Email Template
    message = f'''
        Account with { AccountName }({MovedAccountId}) has been moved by {requestedUser} from {sourceOrgUnitName} to {destOrgUnitName}
        this action will be reverted back in {timeDelta} minuties.
        if this move is not approved. Please 
    '''
    
    ## SNS Section
    snsClient= boto3.client('sns')
    response = snsClient.publish(
        TargetArn=snsArn,
        Message=message
    )
    
    
    ### pre schdule tasks
#    EST = pytz.timezone('US/Eastern')
    time_string = event.get('eventTime')
    eventTime = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')
    schduletime = eventTime + timedelta(minutes=timeDelta)
    schdulerEventTime = schduletime.strftime('%Y-%m-%dT%H:%M:%S')
    schdulerEventTimeNameSuffix = schduletime.strftime('%Y_%m_%dT%H_%M_%S')
    ## Schduler Section
    schdulerClient = boto3.client('scheduler')
    
    Schedulerresponse = schdulerClient.create_schedule(
        Description='string',
        FlexibleTimeWindow={
            'Mode': 'OFF'
        },
        Name=f'move_account_{schdulerEventTimeNameSuffix}',
        ScheduleExpression=f'at({schdulerEventTime})', #at()
        ScheduleExpressionTimezone='US/Eastern', #timezone
        State='ENABLED',
        Target={
            'Arn': targetArn,
            'Input': json.dumps(event),
            'RetryPolicy': {
                'MaximumEventAgeInSeconds': 300,
                'MaximumRetryAttempts': 3
            },
            'RoleArn': roleArn,
        }
    )
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(Schedulerresponse)
    }
