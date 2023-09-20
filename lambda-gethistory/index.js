const aws = require('aws-sdk');

var dynamo = new aws.DynamoDB();
const tableName = process.env.tableName;

exports.handler = async (event, context) => {
    //console.log('## ENVIRONMENT VARIABLES: ' + JSON.stringify(process.env));
    //console.log('## EVENT: ' + JSON.stringify(event));

    const userId = event['userId'];
    const allowTime = event['allowTime'];

    console.log('userId: ', userId)
    console.log('allowTime: ', allowTime)

    let msg = "";
    let queryParams = {
        TableName: tableName,
        KeyConditionExpression: "user_id = :userId and request_time > :allowTime",
        ExpressionAttributeValues: {
            ":userId": {'S': userId},
            ":allowTime": {'S': allowTime}
        }
    };
    
    try {
        result = await dynamo.query(queryParams).promise();
    
        console.log(JSON.stringify(result));    

        msg = result['Item']['msg']['S'];
    } catch (error) {
        console.log(error);
        return;
    } 

    const response = {
        statusCode: 200,
        msg: msg
    };
    return response;
};