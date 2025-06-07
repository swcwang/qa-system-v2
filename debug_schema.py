import duckdb

con = duckdb.connect("./data/qanda_may.duckdb")

# Check episode table columns
print("=== Episode Table Schema ===")
episode_schema = con.execute("PRAGMA table_info(dim_episode)").fetchall()
for row in episode_schema:
    print(f"Column: {row[1]}, Type: {row[2]}")

# Check first few episodes
print("\n=== Sample Episode Data ===")
episodes = con.execute("SELECT * FROM dim_episode LIMIT 3").fetchall()
for ep in episodes:
    print(ep)