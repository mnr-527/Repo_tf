import json
import boto3
import time

def lambda_handler(event, context):
    event = event.get("detail")
    
    client = boto3.client('organizations')
    
    reqParameters = event.get('requestParameters')
    accountId = reqParameters.get("accountId")
    sourceOu = reqParameters.get("sourceParentId")
    destinationOu = reqParameters.get('destinationParentId')
    
    response = client.list_parents(ChildId=accountId)
    ouId = response['Parents'][0]['Id']

    if  not (ouId == "ou-afgk-htcq00rd"):
        return "Account already Moved"
      
      
    response = client.move_account(
        #AccountId=accountId,
        #SourceParentId=destinationOu,
        #DestinationParentId=sourceOu
         
        AccountId=accountId,
        SourceParentId= destinationOu,
        DestinationParentId=sourceOu
        )
        
    response = client.list_parents(ChildId=accountId)
    ouId = response['Parents'][0]['Id']
        
    if (ouId == sourceOu):
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
            Account with { AccountName }({MovedAccountId}) has been moved back from {destOrgUnitName} to {sourceOrgUnitName}
        '''
    else:
        message = f'''
            Account with { AccountName }({MovedAccountId})  failed to moved back from {destOrgUnitName} to {sourceOrgUnitName}
        '''
        
    snsArn = 'arn:aws:sns:us-east-1:129176122008:mnrsns' # sns Topic ARN
    snsClient= boto3.client('sns')
    response = snsClient.publish(
        TargetArn=snsArn,
        Message=message
    )

    scheduler = boto3.client('scheduler')

    flex_window = { "Mode": "OFF" }

    schedule_check_accounts = {
        "RoleArn": "arn:aws:iam::556276873924:role/schedule_Movingaccountrole",
        "Arn": "arn:aws:lambda:us-east-1:556276873924:function:checkorg",
        "Input": "{ 'Payload': 'move_account' }"}
    
    scheduler.create_schedule(
        Name="schedule_check_accounts",
        schedule_expression = "cron(5,35 14 * * ? *)",
        Target=schedule_check_accounts,
        FlexibleTimeWindow=flex_window)
    
    return {
    'statusCode': 200,
    'body': json.dumps('MOVED')
    }
