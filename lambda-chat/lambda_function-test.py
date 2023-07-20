import numpy as np
import pandas as pd
import time
from xgboost import XGBRegressor
from lambda_function import handler  

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
    # Version check
    print('np version: ', np.__version__)
    print('pandas version: ', pd.__version__)

    import xgboost as xgb
    print('xgb version: ', xgb.__version__)

    start = time.time()

    # load samples
    event = load_event()

    # Inference
    results = handler(event,"")  
    
    # results
    print(results['statusCode'])
    print(results['body'])

    print('Elapsed time: %0.2fs' % (time.time()-start))   

if __name__ == '__main__':
    main()