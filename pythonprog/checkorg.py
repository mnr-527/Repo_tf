import boto3
def lambda_handler(event, context):
    
    event = event.get("detail")
    snsArn = 'arn:aws:sns:us-east-1:129176122008:mnrsns' # sns Topic ARN
    roleArn = 'arn:aws:iam::129176122008:role/Account-MoveBack-Lambda-Role' #role with schduler event creation access
 #  targetArn = 'arn:aws:lambda:us-east-1:129176122008:function:Moveback' #2nd lambda ARN
    timeDelta = 1 #in minutes

    
    orgClient = boto3.client('organizations')
    reqParameters = event.get('requestParameters')
    
    accountdet = orgClient.list_accounts(
    NextToken='string',
    MaxResults=123
    )
    print(accountdet)

    if accountdet is None :
        print('NO account in Destination org')
    else:
          
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
            OrganizationalUnitId=sourceOrgUnit).get("OrganizationalUnit").get("Name")
        
        #Get Destination Ou Section
            destOrgUnit = reqParameters.get("destinationParentId")
            destOrgUnitName = orgClient.describe_organizational_unit(
            OrganizationalUnitId=destOrgUnit
            ).get("OrganizationalUnit").get("Name")
        
        ## ID extract section
            requestedUser = event.get("userIdentity").get("principalId").split(":")[1]
        
        #Final Email Template
            message = f'''Account with { AccountName }({MovedAccountId}) has been moved back from {destOrgUnitName} to {sourceOrgUnitName}
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

