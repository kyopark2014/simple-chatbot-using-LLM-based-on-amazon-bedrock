const aws = require('aws-sdk');

dynamodb = boto3.resource('dynamodb')
const tableName = process.env.tableName;

exports.handler = async (event, context) => {
    //console.log('## ENVIRONMENT VARIABLES: ' + JSON.stringify(process.env));
    //console.log('## EVENT: ' + JSON.stringify(event));

    const userId = event['userId'];

    console.log('userId: ', userId)

    let queryParams = {
        TableName: tableName,
        KeyConditionExpression: "user_id = :userId",
        ExpressionAttributeValues: {
            ":userId": {'S': userId},
        }
    };
    
    try {
        let result = await dynamodb.deleteItem(queryParams).promise();
    
        console.log('result: ', JSON.stringify(result));    

        const response = {
            statusCode: 200,            
        };
        return response;  
          
    } catch (error) {
        console.log(error);

        const response = {
            statusCode: 500,
            msg: error
        };
        return response;  
    } 
};