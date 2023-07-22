import numpy as np
import time
from lambda_function import lambda_handler  

def load_event():
    json_data = {
        "request-id": "test1234",
        "type": "text",
        "body": "Building a website can be done in 10 simple steps."
    }
    event = {
        'body': json_data,
        'isBase64Encoded': False
    }
    print('event: ', event)

    return event

def main():
    start = time.time()

    # load samples
    event = load_event()

    # Inference
    results = lambda_handler(event,"")  
    
    # results
    print(results['statusCode'])
    print(results['body'])

    print('Elapsed time: %0.2fs' % (time.time()-start))   

if __name__ == '__main__':
    main()