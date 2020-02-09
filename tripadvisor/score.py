import yaml
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from time import sleep

from sentiment_scorer import SentimentScorer

with open('config_file.yml') as file:
    configs = yaml.load(file, Loader=yaml.FullLoader)

with open('api_keys.yml') as file:
    api_keys = yaml.load(file, Loader=yaml.FullLoader)['API_Keys']

# Amend the following 3 variables to continue from previous API calls.
target_folder = configs['TripAdvisor']['target_folder']
continue_in_folder = configs['TripAdvisor']['continue_in_folder']
continue_from_poi_index = configs['TripAdvisor']['continue_from_poi_index']
continue_from_row_index = configs['TripAdvisor']['continue_from_row_index']


class SentimentScorerFSM:
    def __init__(self):
        self.sentiment_scorer = SentimentScorer(
            target_folder=target_folder,
            continue_in_folder=continue_in_folder,
            continue_from_poi_index=continue_from_poi_index,
            continue_from_row_index=continue_from_row_index)
        self.authenticator = None
        self.nlu = None
        self.api_key_index = None

    def initialise_nlu(self):
        self.authenticator = IAMAuthenticator(api_keys[self.api_key_index])
        self.nlu = NaturalLanguageUnderstandingV1(
            version='2019-07-12',
            authenticator=self.authenticator
        )
        self.nlu.set_service_url(
            'https://gateway.watsonplatform.net/natural-language-understanding/api/v1/analyze?version=2019-07-12')

    def start(self):
        self.api_key_index = 0
        while self.sentiment_scorer.fsm_state != 4:
            initialisation_count = 0
            while initialisation_count < 5:
                try:
                    print('Initialising IBM Watson NLU')
                    self.initialise_nlu()
                    break
                except:
                    print('Failed to initialise IBM Watson NLU.')
                    initialisation_count += 1
            if initialisation_count == 5:
                print('Breaking out of FSM loop due to failure to initialise IBM Watson NLU.')
                break

            # Scoring is done here
            self.sentiment_scorer.score_sentiments(self.nlu)

            # FSM state handling
            if self.sentiment_scorer.fsm_state == 2:
                log = open(self.sentiment_scorer.sentiment_folder_path + 'log.txt', 'a+')
                log.write('API key {} has been exhausted.\n'.format(self.api_key_index))
                log.close()
                self.api_key_index += 1
                print('##########')
                print(
                    'FSM state is 2. changing to API key {}.'.format(
                        self.api_key_index
                    )
                )
                print('##########')
            elif self.sentiment_scorer.fsm_state == 3:
                print('##########')
                print('FSM state is 3.')
                print('##########')


fsm = SentimentScorerFSM()
fsm.start()