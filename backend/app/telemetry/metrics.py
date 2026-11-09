from prometheus_client import Counter, Gauge, Histogram

release_observations = Counter(
    "rook_release_observations_total",
    "Number of release observation stages completed.",
    ["decision"],
)
release_rollbacks = Counter("rook_release_rollbacks_total", "Number of rollback attempts.")
release_outcomes = Counter("rook_release_outcomes_total", "Terminal release outcomes.", ["outcome"])
observation_latency = Histogram(
    "rook_observation_duration_seconds",
    "Time spent collecting an observation from the local gateway.",
)
active_releases = Gauge("rook_active_releases", "Number of releases currently in progress.")
