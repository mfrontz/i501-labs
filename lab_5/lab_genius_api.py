# Michael Frontz - INFO-I501
# lab_05

# built-in
import requests
import os

from multiprocessing import Pool
from time import sleep

# user-installed
import pandas as pd

from tqdm import tqdm
from numpy.random import uniform
from dotenv import load_dotenv

load_dotenv()

# constants
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']

def genius(search_term, per_page=15):
    """
    Collect data from the Genius API by searching for `search_term`.
    
    **Assumes ACCESS_TOKEN is loaded in environment.**

    Parameters
    ----------
    search_term : str
        The name of an artist, album, etc.
    per_page : int, optional
        Maximum number of results to return, by default 15

    Returns
    -------
    list
        All the hits which match the search criteria.
    """
    genius_search_url = f"http://api.genius.com/search?q={search_term}&" + \
                        f"access_token={ACCESS_TOKEN}&per_page={per_page}"
    
    try:
        response = requests.get(genius_search_url)
        json_data = response.json()

    except:
        print('Error connecting to API for search term:', search_term)
    
    return json_data['response']['hits']

def genius_to_df(search_term, n_results_per_term=10, 
                 verbose=True, savepath=None):
    """
    Generate a pandas.DataFrame from a single call to the Genius API.

    Parameters
    ----------
    search_term : str
        Genius search term
    n_results_per_term : int, optional
        Number of results "per_page" for each search term provided, by default 10

    Returns
    -------
    pandas.DataFrame
        The final DataFrame containing the results. 
    """
    try:
        json_data = genius(search_term, per_page=n_results_per_term)
        hits = [hit['result'] for hit in json_data]
        df = pd.DataFrame(hits)
    
        # expand dictionary elements
        df_stats = df['stats'].apply(pd.Series)
        df_stats.rename(columns={c:'stat_' + c for c in df_stats.columns},
                        inplace=True)
        
        df_primary = df['primary_artist'].apply(pd.Series)
        df_primary.rename(columns={c:'primary_artist_' + c 
                                   for c in df_primary.columns},
                          inplace=True)
        
        df = pd.concat((df, df_stats, df_primary), axis=1)
        
        if verbose:
            print(f'PID: {os.getpid()} ... search_term:', search_term)
            print(f"Data gathered for {search_term}.")

        try:
            # this is a good practice for numerous automated data pulls ...
            if savepath:
                # replace any spaces in search term with hyphens
                df.to_csv(savepath + '/genius-' + search_term.replace(' ', '-') + '.csv', 
                          index=False)

        except:
            print('Error saving data as CSV to path:', savepath)

    except:
        print('Error processing JSON data for search term:', search_term)

    return df

def genius_to_dfs(search_terms, **kwargs):
    """
    Generate a pandas.DataFrame from multiple calls to the Genius API.

    Parameters
    ----------
    search_terms : list of strings
        List of artists (say) to search in Genius.
    
    **kwargs : arguments passed to genius_api.genius_to_df

    Returns
    -------
    pandas.DataFrame
        The final DataFrame containing the results. 
    """

    try:
        dfs = []
    
        # loop through search_terms in question
        for search_term in tqdm(search_terms):
            df = genius_to_df(search_term, **kwargs)
            
            # add to list of DataFrames
            dfs.append(df)

    except:
       print('Error iterating through search terms:', search_terms)
    
    return pd.concat(dfs)

def genius_to_dfs_mp(search_terms, savepath = None):
    """
    Generate a pandas.DataFrame from multiple calls to the Genius API using Multiprocessing.

    Parameters
    ----------
    search_terms : list of strings
        List of artists (say) to search in Genius.
    
    savepath : str, optional
        Path to use to save CSV of dataframe
        
    Returns
    -------
    pandas.DataFrame
        The final DataFrame containing the results. 
    """

    with Pool(8) as p:
        results = p.map(genius_to_df, search_terms)

    df_genius_mp = pd.concat(results)

    try:
        if savepath:
            df_genius_mp.to_csv(savepath + '/genius_data_mp.csv', index=False)
            
    except:
        print('Error saving data as CSV to path:', savepath)
    
    return df_genius_mp