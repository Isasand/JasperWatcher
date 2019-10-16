# JasperWatcher
A watcher for units in Tele2 Jasper Wireless 

### AWS Lambda version: 
Lambda function created for AWS. 
Watches Jasper to see if the provided search units are in session. 
If they are, an email or/ and an SMS will be sent with the Device ID and IP address. 

Set up: 
* Install the Requests library locally, create a Lambda package with that and JasperWatcher.py. 
* Upload the zip file to AWS Lambda. 
* Create an IAM role with the following premissions: 
```{
	"Version" : "2012-10-17", 
	"Statement" : [
		{
			"Effect" : "Allow", 
			"Action" : [
				"logs:CreateLogStream", 
				"logs:PutLogEvents", 
				"logs:CreateLogGroup" 
			], 
			"Resource" : "arn:aws:logs:*" 
		}, 
		{
			"Effect" : "Allow", 
			"Action" : "SNS:Publish", 
			"Resource" : "*"
		}, 
		{
			"Effect" : "Allow", 
			"Action" : "ses:SendEmail",
			"Resource" : "arn:aws:ses:*"
		}
	]
}
```
 
* Attach the role to the Lambda function 
* Set environment variables needed: 
  * Key: password Value: Jasper Wireless password 
  * Key: user Value: Jasper Wireless username 
* Provide some search units to the list in JasperWatcher.py (this will be replaced with a text file for easier use) 
* Set the SNS_NOTIFICATION and SES_NOTIFICATION variables to a desired value (True/False). (this will also be moved to a text file)   
* Schedule your function!

You will now get an email or/ and SMS when the search units are in session. 

### Bash version: 
Simple bash client. Run with cron and provide search ids to the function. 
Current version can not yet handle lists. 

run command: 
`$ ./JasperWatcher searchunit`
