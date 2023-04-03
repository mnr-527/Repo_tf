import boto3
def lambda_handler(event, context):
    
    event = event.get("detail")
    snsArn = 'arn:aws:sns:us-east-1:129176122008:mnrsns' # sns Topic ARN
    roleArn = 'arn:aws:iam::129176122008:role/Account-MoveBack-Lambda-Role' #role with schduler event creation access
 #  targetArn = 'arn:aws:lambda:us-east-1:129176122008:function:Moveback' #2nd lambda ARN
    timeDelta = 1 #in minutes

    reqParameters = event.get('requestParameters')
    orgClient = boto3.client('organizations')
    
    response = orgClient.list_accounts(
    NextToken='string',
    MaxResults=123
    )
    print(response)

    if response is None :
        print('NO accounts in Destination org')
    else:
        MovedAccountId = reqParameters.get("accountId")
        AccountName = orgClient.describe_account(AccountId=MovedAccountId).get('Account').get('Name')
    
    #Get Source OU Section
        sourceOrgUnit = reqParameters.get("sourceParentId")
        sourceOrgUnitName = orgClient.describe_organizational_unit(   OrganizationalUnitId=sourceOrgUnit ).get("OrganizationalUnit").get("Name")
    
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
    

       
    

