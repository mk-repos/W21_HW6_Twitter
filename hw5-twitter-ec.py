#########################################
##### Name:       Moeki Kurita      #####
##### Uniqname:   mkurita           #####
#########################################

from requests_oauthlib import OAuth1
import json
import requests
import hw6_secrets_starter as secrets
import stop_words

CACHE_FILENAME = "twitter_cache.json"
CACHE_DICT = {}

client_key = secrets.TWITTER_API_KEY
client_secret = secrets.TWITTER_API_SECRET
access_token = secrets.TWITTER_ACCESS_TOKEN
access_token_secret = secrets.TWITTER_ACCESS_TOKEN_SECRET

oauth = OAuth1(client_key,
               client_secret=client_secret,
               resource_owner_key=access_token,
               resource_owner_secret=access_token_secret)

STOP_WORDS = stop_words.STOP_WORDS


def test_oauth():
    ''' Helper function that returns an HTTP 200 OK response code and a 
    representation of the requesting user if authentication was 
    successful; returns a 401 status code and an error message if 
    not. Only use this method to test if supplied user credentials are 
    valid. Not used to achieve the goal of this assignment.'''

    url = "https://api.twitter.com/1.1/account/verify_credentials.json"
    auth = OAuth1(client_key, client_secret, access_token, access_token_secret)
    authentication_state = requests.get(url, auth=auth).json()
    return authentication_state


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()


def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params

    AUTOGRADER NOTES: To correctly test this using the autograder, use an underscore ("_") 
    to join your baseurl with the params and all the key-value pairs from params
    E.g., baseurl_key1_value1
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    concat = []
    for k, v in params.items():
        concat.append(f"{k}_{v}")
    concat.sort()
    unique = baseurl + "_" + "_".join(concat)
    return unique


def make_request(baseurl, params):
    '''Make a request to the Web API using the baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the data returned from making the request in the form of 
        a dictionary
    '''
    response = requests.get(baseurl, params=params, auth=oauth)
    return response.json()


def make_request_with_cache(baseurl, hashtag, count):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    AUTOGRADER NOTES: To test your use of caching in the autograder, please do the following:
    If the result is in your cache, print "fetching cached data"
    If you request a new result using make_request(), print "making new request"

    Do no include the print statements in your return statement. Just print them as appropriate.
    This, of course, does not ensure that you correctly retrieved that data from your cache, 
    but it will help us to see if you are appropriately attempting to use the cache.
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    hashtag: string
        The hashtag to search (i.e. #MarchMadness2021)
    count: int
        The number of tweets to retrieve
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    params = {"q": hashtag, "count": count}
    request_key = construct_unique_key(baseurl=baseurl, params=params)
    if request_key in CACHE_DICT.keys():
        print("fetching cached data")
        return CACHE_DICT[request_key]
    else:
        print("making new request")
        response = make_request(baseurl=baseurl, params=params)
        CACHE_DICT[request_key] = response
        save_cache(CACHE_DICT)
        return response


def find_three_most_cooccurring_hashtag(tweet_data, hashtag_to_ignore):
    ''' Finds the three most commonly used hashtag which cooccured with
    the hashtag queried in make_request_with_cache().

    Parameters
    ----------
    tweet_data: dict
        Twitter data as a dictionary for a specific query
    hashtag_to_ignore: string
        the same hashtag that is queried in make_request_with_cache() 
        (e.g. "#MarchMadness2021")

    Returns
    -------
    dict
        the dict of hashtags that most commonly co-occurs with
        the hashtag queried in make_request_with_cache()
        ordered by its number of occurence (decending)
    '''
    hashtags_list = []
    # iterate through all the tweets
    for tweet in tweet_data["statuses"]:
        # extract a list of hashtag object
        hashtags = tweet["entities"]["hashtags"]
        # if hashtag object exist
        if hashtags:
            # iterate through all the hashtags
            for hashtag in hashtags:
                # store all hashtags with duplicates allowed
                hashtags_list.append(f"#{hashtag['text'].lower()}")
    # based on the list of all hashtags with duplicates, count each
    count_dict = {hashtag: hashtags_list.count(hashtag)
                  for hashtag in hashtags_list}
    try:
        del count_dict[hashtag_to_ignore.lower()]
    except KeyError:
        pass
    # get three most frequent in decending order with number of occurence
    sorted_hashtags = sorted(count_dict, key=count_dict.get, reverse=True)
    sorted_dict = {}
    for hashtag in sorted_hashtags[:3]:
        sorted_dict[hashtag] = count_dict[hashtag]
    return sorted_dict


def find_ten_most_cooccurring_words(tweet_data):
    ''' Finds the ten most commonly used words which cooccured with
    the hashtag queried in make_request_with_cache().

    Parameters
    ----------
    tweet_data: dict
        Twitter data as a dictionary for a specific query

    Returns
    -------
    dict
        the dict of words that most commonly co-occurs with
        the hashtag queried in make_request_with_cache()
        ordered by its number of occurence (decending)
    '''
    ignore = ["rt"] + STOP_WORDS
    words_list = []
    # iterate through all the tweets
    for tweet in tweet_data["statuses"]:
        # get list of words in the text
        words = tweet["text"].lower().split()
        # exclude trailling/following symbols
        cleaned_words = []
        bad_char = ",.()[]!?;:…"
        for word in words:
            cleaned_words.append(word.strip(bad_char))
        words_list.extend(cleaned_words)
    # based on the list of all words with duplicates, count each
    count_dict = {
        word: words_list.count(word)
        for word in words_list
        if word not in ignore and not word.startswith("#")
    }
    # get ten most frequent in decending order with number of occurence
    sorted_words = sorted(count_dict, key=count_dict.get, reverse=True)
    sorted_dict = {}
    for word in sorted_words[:10]:
        sorted_dict[word] = count_dict[word]
    return sorted_dict


if __name__ == "__main__":
    if not client_key or not client_secret:
        print("You need to fill in CLIENT_KEY and CLIENT_SECRET in secret_data.py.")
        exit()
    if not access_token or not access_token_secret:
        print("You need to fill in ACCESS_TOKEN and ACCESS_TOKEN_SECRET in secret_data.py.")
        exit()

    CACHE_DICT = open_cache()

    baseurl = "https://api.twitter.com/1.1/search/tweets.json"
    count = 100

    prompt = "Enter a #hashtag you want to search, or 'exit' to quit: "

    # hashtag = '#marchmadness2021sssssssssss'
    # tweet_data = make_request_with_cache(baseurl, hashtag, count)
    # three_hashtags = find_three_most_cooccurring_hashtag(
    #     tweet_data=tweet_data, hashtag_to_ignore=hashtag)
    # print(three_hashtags)

    while True:
        hashtag = input(prompt)
        # check exit
        if hashtag == "exit":
            print("Bye!")
            break
        # format as a hashtag
        elif not hashtag.startswith("#"):
            hashtag = "#" + hashtag
        # get tweet data
        tweet_data = make_request_with_cache(baseurl, hashtag, count)
        # get cooccuring hashtags/words
        three_hashtags = find_three_most_cooccurring_hashtag(
            tweet_data=tweet_data, hashtag_to_ignore=hashtag)
        ten_words = find_ten_most_cooccurring_words(tweet_data=tweet_data)
        # no result
        if not three_hashtags and not ten_words:
            print("No results found.")
            continue
        # display hashtags
        else:
            print(f"THREE MOST FREQUENT HASHTAGS FOR {hashtag}")
            for k, v in three_hashtags.items():
                print("\t", k, " appered ", v, " times")
            # display words
            print(f"\nTEN MOST FREQUENT WORDS FOR {hashtag}")
            for k, v in ten_words.items():
                print("\t", k, " appered ", v, " times")
