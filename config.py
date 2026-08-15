# Define standard feature configurations for the models

FEATURE_OPTIONS = [
    "bpm",
    "danceability",
    "average_loudness",
    "mood_happy_prob",
    "mood_aggressive_prob",
    "onset_rate",
    "dynamic_complexity",
    "key_scale",
    "mood_happy",
    "mood_sad",
    "mood_relaxed",
    "mood_aggressive",
    "mood_acoustic",
    "mood_electronic",
    "mood_party",
    "timbre",
    "tonal_atonal",
]

TRAINING_COLUMNS_ORDER = [
    "bpm",
    "danceability",
    "onset_rate",
    "average_loudness",
    "dynamic_complexity",
    "mfcc_zero_mean",
    "tuning_frequency",
    "tuning_equal_tempered_deviation",
    "mood_happy_prob",
    "mood_aggressive_prob",
    "mood_acoustic",
    "mood_electronic",
    "timbre",
    "voice_instrumental",
]

GENRE_LABELS = [
    "Classical",
    "Country",
    "Electronic",
    "Folk",
    "Hip-Hop/R&B",
    "Jazz/Blues",
    "Metal",
    "Pop",
    "Punk",
    "Rock",
]

DECADE_LABELS = [
    1950,
    1960,
    1970,
    1980,
    1990,
    2000,
    2010,
    2020,
]

FEATURE_LIMITS = {
    "bpm": (40, 200),
    "danceability": (0.0, 3.0),
    "onset_rate": (0.0, 24.0),
    "average_loudness": (0.0, 1.0),
    "dynamic_complexity": (0.0, 80.0),
    "mfcc_zero_mean": (-1100.0, -450.0),
    "tuning_frequency": (430.0, 460.0),
    "tuning_equal_tempered_deviation": (0.0, 0.5),
    "mood_happy_prob": (0.0, 1.0),
    "mood_aggressive_prob": (0.0, 1.0),
    "mood_acoustic": (0, 1),
    "mood_electronic": (0, 1),
    "timbre": (0, 1),
    "voice_instrumental": (0, 1),
}