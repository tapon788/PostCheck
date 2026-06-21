import pandas as pd

KEY_COLUMNS = [
    "Supplementary Information",
    "Distinguished Name",
    "Diagnostic Info"
]


def create_key(df):
    df = df.copy()

    for col in KEY_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["_KEY"] = (
        df["Supplementary Information"].fillna("").astype(str)
        + "|"
        + df["Distinguished Name"].fillna("").astype(str)
        + "|"
        + df["Diagnostic Info"].fillna("").astype(str)
    )

    return df

def build_key(df):

    key_cols = [
        "Supplementary Information",
        "Distinguished Name",
        "Diagnostic Info"
    ]

    df = df.copy()

    for col in key_cols:
        if col not in df.columns:
            df[col] = ""

    df["_KEY"] = (
        df[key_cols]
        .fillna("")
        .astype(str)
        .agg("|".join, axis=1)
    )

    return df
def calculate_delta(
        pre_df,
        post_df,
        history_df=None,
        post_history_df=None):

    # -------------------------
    # PRE / POST
    # -------------------------
    pre = build_key(pre_df)
    post = build_key(post_df)

    pre_keys = set(pre["_KEY"])
    post_keys = set(post["_KEY"])

    new_df = post[
        ~post["_KEY"].isin(pre_keys)
    ].copy()

    cleared_df = pre[
        ~pre["_KEY"].isin(post_keys)
    ].copy()

    # -------------------------
    # HISTORY / POST HISTORY
    # -------------------------
    hist_new_df = pd.DataFrame()
    hist_cleared_df = pd.DataFrame()

    if (
        history_df is not None
        and post_history_df is not None
        and not history_df.empty
        and not post_history_df.empty
    ):

        history = build_key(history_df)
        post_history = build_key(post_history_df)

        history_keys = set(history["_KEY"])
        post_history_keys = set(post_history["_KEY"])

        hist_new_df = post_history[
            ~post_history["_KEY"].isin(history_keys)
        ].copy()

        hist_cleared_df = history[
            ~history["_KEY"].isin(post_history_keys)
        ].copy()

    # -------------------------
    # HISTORY MATCHING
    # (for New alarms)
    # -------------------------
    if (
        history_df is not None
        and not history_df.empty
        and not new_df.empty
    ):

        history = build_key(history_df)

        counts = history["_KEY"].value_counts()

        new_df["History Count"] = (
            new_df["_KEY"]
            .map(counts)
            .fillna(0)
            .astype(int)
        )

        new_df["History Match"] = (
            new_df["History Count"] > 0
        ).map({
            True: "YES",
            False: "NO"
        })

    else:

        new_df["History Count"] = 0
        new_df["History Match"] = "NO"

    return (
        new_df.drop(columns=["_KEY"], errors="ignore"),
        cleared_df.drop(columns=["_KEY"], errors="ignore"),
        hist_new_df.drop(columns=["_KEY"], errors="ignore"),
        hist_cleared_df.drop(columns=["_KEY"], errors="ignore"),
    )


import pandas as pd

import pandas as pd

def calculate_pre_post_delta(pre_df, post_df, history_df=None):

    if pre_df is None:
        pre_df = pd.DataFrame()
    if post_df is None:
        post_df = pd.DataFrame()
    if history_df is None:
        history_df = pd.DataFrame()

    if pre_df.empty or post_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    key_cols = [
        "Alarm Number",
        "Supplementary Information",
        "Distinguished Name",
        "Diagnostic Info",
        "Severity",
    ]

    def make_key(df):
        return (
            df[key_cols]
            .fillna("")
            .astype(str)
            .agg("|".join, axis=1)
        )

    pre = pre_df.copy()
    post = post_df.copy()

    pre["_KEY"] = make_key(pre)
    post["_KEY"] = make_key(post)

    pre_set = set(pre["_KEY"])
    post_set = set(post["_KEY"])

    new_df = post[post["_KEY"].isin(post_set - pre_set)].copy()
    cleared_df = pre[pre["_KEY"].isin(pre_set - post_set)].copy()

    # -----------------------------
    # HISTORY ENRICHMENT
    # -----------------------------
    if not history_df.empty:

        history = history_df.copy()
        history["_KEY"] = make_key(history)

        history_counts = history["_KEY"].value_counts().to_dict()
        history_set = set(history["_KEY"])

        # NEW DF enrichment
        new_df["History Count"] = new_df["_KEY"].map(history_counts).fillna(0).astype(int)
        #new_df["History Match"] = new_df["_KEY"].isin(history_set)

        new_df["History Match"] = (
            new_df["_KEY"]
            .isin(history_set)
            .map({
                True: "Exists",
                False: "Not Found"
            })
        )

        # CLEARED DF enrichment
        cleared_df["History Count"] = cleared_df["_KEY"].map(history_counts).fillna(0).astype(int)
        #cleared_df["History Match"] = cleared_df["_KEY"].isin(history_set)

        cleared_df["History Match"] = (
            cleared_df["_KEY"]
            .isin(history_set)
            .map({
                True: "Exists",
                False: "Not Found"
            })
        )


    else:
        new_df["History Count"] = 0
        new_df["History Match"] = False

        cleared_df["History Count"] = 0
        cleared_df["History Match"] = False

    # cleanup
    new_df.drop(columns=["_KEY"], inplace=True)
    cleared_df.drop(columns=["_KEY"], inplace=True)

    return new_df, cleared_df

def calculate_history_delta(history_df: pd.DataFrame, post_history_df: pd.DataFrame):
    """
    Returns:
        hist_new_df, hist_cleared_df
    """

    if history_df is None:
        history_df = pd.DataFrame()
    if post_history_df is None:
        post_history_df = pd.DataFrame()

    hist_new_df = pd.DataFrame()
    hist_cleared_df = pd.DataFrame()

    if history_df.empty or post_history_df.empty:
        return hist_new_df, hist_cleared_df

    key_cols = [
        "Alarm Number",
        "Supplementary Information",
        "Distinguished Name",
        "Diagnostic Info",
        "Severity",
    ]

    def make_key(df):
        return (
            df[key_cols]
            .fillna("")
            .astype(str)
            .agg("|".join, axis=1)
        )

    history = history_df.copy()
    post_hist = post_history_df.copy()

    history["_KEY"] = make_key(history)
    post_hist["_KEY"] = make_key(post_hist)

    history_set = set(history["_KEY"])
    post_hist_set = set(post_hist["_KEY"])

    # NEW in post-history
    hist_new_df = post_hist[post_hist["_KEY"].isin(post_hist_set - history_set)].copy()

    # CLEARED from history
    hist_cleared_df = history[history["_KEY"].isin(history_set - post_hist_set)].copy()

    hist_new_df.drop(columns=["_KEY"], inplace=True, errors="ignore")
    hist_cleared_df.drop(columns=["_KEY"], inplace=True, errors="ignore")

    return hist_new_df, hist_cleared_df