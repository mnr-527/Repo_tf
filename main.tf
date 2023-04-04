terraform {
required_providers {
  aws = ">= 3.55.0"
 }
 
}
provider "aws" {
  region = "us-east-1"
  shared_credentials_files = [ "C:/Users/Nagaraju/.aws/credentials" ]
}

 resource "aws_cloudwatch_event_rule" "movingaccount" {
   name        = "Monitor_accounts"
   description = "Monitoring moving od accounts in organizations"
   event_pattern = <<EOF
  {
    "source": ["aws.organizations"],
    "detail-type": ["AWS API Call via CloudTrail"],
    "detail": {
      "eventSource": ["organizations.amazonaws.com"],
      "eventName": ["MoveAccount"],
      "requestParameters": {
        "destinationParentId": ["ou-afgk-htcq00rd"]
     }
   }
 }
 EOF
   
 }

 resource "aws_iam_role" "Scheduler_role_tf" {
    name   = "schedule_Movingaccountrole"
    assume_role_policy = <<EOF
    {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "scheduler.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
      ]
    }
  EOF
 }

 resource "aws_iam_role" "lambda_role_tf" {
    name   = "Movingaccountrole"
    assume_role_policy = <<EOF
    {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
      ]
    }
  EOF
 }
  


resource "aws_iam_policy" "iam_policy_for_lambda_tf" {
 
 name         = "aws_iam_policy_for_terraform_aws_lambda_role_tf"
 path         = "/"
 description  = "AWS IAM Policy for managing aws lambda role"
 policy = <<EOF
{
 "Version": "2012-10-17",
 "Statement": [
   {
     "Action": [
       "logs:CreateLogGroup",
       "logs:CreateLogStream",
       "logs:PutLogEvents",
       "lambda:GetAccountSettings",
       "lambda:GetEventSourceMapping",
       "lambda:GetFunction",
       "lambda:GetFunctionConfiguration",           
       "lambda:GetFunctionCodeSigningConfig",
       "lambda:GetFunctionConcurrency",                
       "lambda:ListEventSourceMappings",
       "lambda:ListFunctions",      
       "lambda:ListTags",
       "iam:ListRoles",
       "sns:Publish",
       "events:*"  
     ],
     "Resource": "arn:aws:logs:*:*:*",
     "Effect": "Allow"
   }
 ]
}
EOF
}
 
resource "aws_iam_role_policy_attachment" "attach_iam_policy_to_iam_role_tf" {
 role        = aws_iam_role.lambda_role_tf.name
 policy_arn  = aws_iam_policy.iam_policy_for_lambda_tf.arn
}

data "archive_file" "zip_the_python_code_moving" {
type        = "zip"
source_dir  = "${path.module}/pythonprog/move1"
//source_file = "move.py"
output_path = "${path.module}/pythonprog/move.zip"
//output_path = "move.zip"
}

data "archive_file" "zip_the_python_code_moveback" {
type        = "zip"
source_dir  = "${path.module}/pythonprog/back1"
output_path = "${path.module}/pythonprog/back.zip"
}

data "archive_file" "zip_the_python_code_checkorg" {
type        = "zip"
source_dir  = "${path.module}/pythonprog"
output_path = "${path.module}/pythonprog/checkorg.zip"
}

resource "aws_lambda_function" "terraform_lambda_func_tf" {
filename                       = "${path.module}/pythonprog/move.zip"
function_name                  = "move"
role                           =  aws_iam_role.lambda_role_tf.arn
//role                           = "arn:aws:iam::556276873924:role/Movingaccountrole"
handler                        = "move.lambda_handler"
source_code_hash               = data.archive_file.zip_the_python_code_moving.output_base64sha256
runtime                        = "python3.9"
timeout                        =  10
//depends_on                     = aws_iam_role_policy_attachment.attach_iam_policy_to_iam_role
}

resource "aws_lambda_function" "terraform_lambda_func_tf_back" {
filename                       = "${path.module}/pythonprog/back.zip"
function_name                  = "back"
role                           =  aws_iam_role.lambda_role_tf.arn
//role                           = "arn:aws:iam::556276873924:role/Movingaccountrole"
handler                        = "back.lambda_handler"
source_code_hash               = data.archive_file.zip_the_python_code_moveback.output_base64sha256
runtime                        = "python3.9"
timeout                        =  10
//depends_on                     = aws_iam_role_policy_attachment.attach_iam_policy_to_iam_role
}

resource "aws_lambda_function" "terraform_lambda_func_tf_checkaccount" {
filename                       = "${path.module}/pythonprog/checkorg.zip"
function_name                  = "checkorg"
role                           =  aws_iam_role.lambda_role_tf.arn
//role                           = "arn:aws:iam::556276873924:role/Movingaccountrole"
handler                        = "back.lambda_handler"
source_code_hash               = data.archive_file.zip_the_python_code_checkorg.output_base64sha256
runtime                        = "python3.9"
timeout                        =  10
//depends_on                     = aws_iam_role_policy_attachment.attach_iam_policy_to_iam_role
}

resource "aws_cloudwatch_event_target" "Lambda_tf" {
  rule      = aws_cloudwatch_event_rule.movingaccount.name
  target_id = "terraform_lambda_func_tf"
  arn       = aws_lambda_function.terraform_lambda_func_tf.arn
  }

  resource "aws_scheduler_schedule" "movebackaccount" {
  name       = "my-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(30 minutes)"

  target {
    arn      = aws_lambda_function.terraform_lambda_func_tf_back.arn
    role_arn = aws_iam_role.Scheduler_role_tf.arn
  }
  
}

 resource "aws_scheduler_schedule" "checkaccount" {
  name       = "schedule_check_accounts"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(5,35 14 * * ? *)"

  target {
    arn      = aws_lambda_function.terraform_lambda_func_tf_checkaccount.arn
    role_arn = aws_iam_role.Scheduler_role_tf.arn
  }
  
}

  
