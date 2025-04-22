from dotenv import load_dotenv
import os 
import yaml 
load_dotenv('/project/.env')



class Config :
    with open('/project/config/config.yml','r') as file:
        config_data = yaml.load(file , Loader=yaml.FullLoader)

        producer_config = config_data["PRODUCER"]['PRODUCER_CONFIG']
        topic_name = config_data["PRODUCER"]['TOPIC_NAME']
        server = config_data["CONSUMER"]['SERVER']




        finnhub_token = os.getenv('FINNHUB_TOKEN')







config = Config()    
#print(config.finnhub_token)