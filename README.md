# Music-Analytics-Prediction-RAG

### A music analytics, prediction, and RAG pipeline that ingests music data, cleans and preprocesses it to build prediction models and an analytics dashboard, then applies RAG (retrieval augmented generation) for a user chatbot for music creators and artists.

#### 1) Motivation

I applied to and was accepted to the Booz Allen Mentorship program. This is a 4-month program where I am paired with a mentor to develop an AI/DS project. Due to my interest in music and desire to implement RAG, I decided to create a music analytics dashboard for music creators and artists.

This dashboard will include descriptive analytics of the music data and predictive modeling to predict the song's genre and decade based on acoustic features. Then, there will be a RAG chatbot that allows the user to ask natural language questions across specific artists, decades, or instrumental/vocal style songs.

I first needed to find a reliable data source. I originally wanted to use the Spotify API, however, I realized that many of its API features were discontinued in February 2026. Therefore, I came across the AcousticBrainz and MetaBrainz datasets, which are publicly available, open-source datasets created by a nonprofit for people to attach a tool and give audio features, or to enter song features.

After ingesting this data from various MetaBrainz sources and combining the data based off the unique mbid (ID for each record), I removed duplicate songs and ended up with around 7 million songs, which are the total number of songs in the database.

I then needed to perform data cleaning and preprocessing, exploratory data analysis, and feature scaling to prepare the data for modeling.

After fitting several ensemble-based models, I then find the most relevant features, perform feature selection, and save the model pickle files for the dashboard.

I then develop a simple Streamlit dashboard with 4 pages.

I then implement the RAG portion and add it as a metadata filter.

## Data Ingestion

I first ingest the following files from AcousticBrainz:

* acousticbrainz-rhythm.csv
* acousticbrainz-lowlevel.csv
* acousticbrainz-tonal.csv

These files contain duplicate mbid values from different user submissions for the same song. After examining the data, I decide to take the median of all the values.

I then merge the 3 files on the mbid.

I then do some other data processing and load in the musicbrainz_canonical.parquet.

I then merge that with the existing data.

Finally, I ingest data from mbdump.tar.bz2 and mbdump-derived.tar.bz2 for features such as artist name, location, etc.

I then merge this dump data with the overall data to create the final dataframe.

## Exploratory Data Analysis

#### For Decade Prediction

The next step is exploratory data analysis.

After examining my features, I decide to predict genre and song decade based on acoustic features only since I don't want to introduce bias or leak the target in the training data from features like artist name, country, etc.

Here are some of the acoustic features used and what they mean:

onset rate: divides the total number of these detected events by the duration of the track, giving you an average frequency (events per second).

dynamic_complexity: quantifies how frequently and drastically the volume changes throughout the recording.

mfcc_zero_mean: Mel-Frequency Cepstral Coefficients. MFCCs are the standard representation used in audio processing to capture the timbre (the quality or "color" of a sound that makes a guitar sound different from a piano, even if they play the exact same note).

I handle NULL values by dropping them since I still have a substantial amount of data to work with (~5M rows).

I create the decade binning variable and only keep records after 1930 since they make up a tiny proportion.

I encode pre-1950 as 1950.

I undersample the majority class:

```text
decade
2000    250000
1990    250000
2010    250000
2020    250000
1980    250000
1970    143567
1960     79474
1950     24959
```

I then examine the distribution of the numeric features and their statistics.

A tiny amount make up strange BPM values, which I drop.

I also clean the danceability variable.

I also look at value counts and encode mood binaries to 0 and 1.

#### For Genre Prediction
Genre EDA is very similar to what I did for decade.

I do the same dropping and remove NULLs except for genre instead of decade.

There are many random genres, so I need to do extensive cleaning and preprocessing of genre.

I decide to bucket into main genres and use RapidFuzz.

After genre features are cleaned, I then do the same conversion of binary features to 0 and 1.

I combine the genres further into these final genres:

```text
main_genre
Electronic     961377
Rock           857129
Pop            346058
Jazz/Blues     306069
Classical      299607
Metal          266239
Hip-Hop/R&B    227304
Punk           119940
Folk           104295
Country         87465
```

## Data Modeling
#### Decade
I perform a stratified train-test split.

I verify class distribution after the split of train and test sets.

I then perform Pearson correlation to determine highly correlated features. I drop these columns.

Then, I perform mutual information gain and decide not to drop additional features.

I then examine feature distributions and decide how to scale features:

#### Leave unscaled

* average_loudness - since using tree-based models predominantly

#### Standard scaling

* bpm
* second_peak_bpm_mean
* danceability
* mfcc_zero_mean
* tuning_frequency - spike is normal frequency

#### Log transform + standard scaling

* onset_rate
* dynamic_complexity
* tuning_equal_tempered_deviation

#### Min-max scaling

* mood_happy_prob
* mood_aggressive_prob

I then fit the model using the following metrics:

```text
"Macro F1": macro_f1,
"Weighted F1": weighted_f1,
"Macro PR-AUC": macro_prauc,
"Macro ROC AUC": macro_rocauc,
"Top-3 Accuracy": top_3_acc,
"Log-Loss": logloss,
"Adjacent Accuracy": adjacent_accuracy,
"Mean Average Error": mae_decades
```

Using:

sample_weights_train = compute_sample_weight(class_weight='balanced', y=y_train) on Random Forest, LightGBM, CatBoost, and XGBoost.

After finding the most important features using feature importance, I retrain to get the best model pickle files.

#### Genre
I also perform a stratified train-test split as with Decade.

I do the correlation matrix and the same scaling as Decade.

I do the same model training as done with Decade.

I redo the training on final selected features, same as Decade.

## Streamlit Dashboard
I create a simple Streamlit dashboard.

I organize it with app.py in the main directory, with a rag folder containing rag/retriver.py and rag/generator.py.

I have a pages folder containing:

* artist_explorer.py
* temporal_trends.py
* genre_comparison.py
* prediction.py
* music_rag_serach.py

#### Artist Explorer
The Artist Explorer page allows the user to search an artist and select from the available artists.

There are around 3 million rows total, so I use DuckDB for more efficient search and loading.

The user can then see statistics for the songs from that artist, such as mean, standard deviation, minimum, maximum, etc., and also the average of a feature for each release_year over time.

#### Temporal Trends

For the Temporal Trends page, the user sees a graph of the average loudness over time, aggregated on all songs in the database.

Then, the user can select two features to compare the trends over the decade on two y-axes.

#### Genre Comparison

For the Genre Comparison page, the user can select from any of the available genres to view:

* BPM differences between them
* Loudness
* Danceability
* Aggressive and happy probability differences
* Dynamic complexity and onset rate differences

#### Predict Genre or Decade

For the Predict Genre or Decade page, the user can input any of their audio features and predict for either genre or decade or both.

The user can also view the model probabilities to get a clearer picture.

#### RAG Music Search

For the RAG Music Search page, the user can search for any semantic query and manually choose filters on:

* Artist
* Decade
* Instrumental/vocal
* Release year

The RAG will then perform semantic similarity accounting for the metadata filters and the user text.

## RAG Implementation

For the RAG implementation, I approached it locally using Ollama models.

Being completely new to RAG, I originally wanted the RAG to retrieve information such as:

* "Which decade had the highest danceability on average?"
* "How has the average BPM of hip hop changed since the 1990s?"

But I realized it was more reliable to use a Python filter directly, and RAG was more powerful for semantic search. This is what led me to use a metadata filter plus semantic search for questions such as:

* "show me aggressive songs with high energy"
* "find songs that feel dark and tonal from 1990s"
* "find me instrumental tracks with high dynamic complexity"

The original data did not have a lot of textual data, so I generated textual descriptions for each row by inputting the features into a sentence, but varying the wording used, for example:
```text
"tempo": {
    "very slow": "very slow, calm, unhurried, and relaxed",
    "slow": "slow, laid-back, and relaxed",
}

"rhythmic_density": {
    "very sparse": "very sparse rhythms with few note events",
    "sparse": "a sparse and open rhythmic texture",
}
```
This provided richer natural language for the LLM to perform semantic search.

Next, I was using another smaller LLM to extract the metadata filters from the user query.

However, due to company download restrictions, I was not able to get an Ollama model powerful enough to accurately extract metadata information from user queries. Therefore, I decided to have the user text be only semantic search, and the user manually chooses metadata filters, if any.

The result is a powerful and accurate RAG chatbot that will apply any metadata filter and perform semantic search on the music database for the user query.

## Conclusion

Overall, this music analytics dashboard with prediction and RAG was an exciting project where I learned a lot, but not without its roadblocks.

First, I started out with the Spotify API, but then realized its discontinued features and quickly found a suitable publicly available source of MetaBrainz. Then, I needed to determine what features I could predict based on what was available.

I learned about different acoustic features present in music, and why some are better at predicting things like the song's genre or what decade the song was from.

I noticed that predicting the decade of the song could be leaked by features describing the song's tuning and recording quality, as older songs were less likely to be tuned correctly. So, there may have been other features that could predict decade.

Additionally, extensive preprocessing and feature engineering was needed, especially for messy text columns like genre, artist, and release name. I learned how to classify genres into one bucket, and how to standardize release names that were in different languages all to alphanumeric characters.

I was able to use powerful ensemble methods such as XGBoost and CatBoost to achieve a decent score. I had to take into consideration class imbalances.

Using DuckDB to parse the 3 million rows was necessary to prevent lag in the Streamlit dashboard.

I also learned about RAG and the guardrails it needs to correctly identify metadata filters.

To expand on this project would be to implement data from other sources, to model features across things like country or language, and to develop a more complex RAG chatbot that could aggregate across time periods and artists.