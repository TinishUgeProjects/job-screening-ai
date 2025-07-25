# import sqlite3
#
# conn = sqlite3.connect("job_screening.db")
# cursor = conn.cursor()
#
# # Check Job Listings
# print("📌 Job Listings:\n" + "-" * 50)
# cursor.execute("SELECT * FROM job_listings")
# job_rows = cursor.fetchall()
#
# if job_rows:
#     for row in job_rows:
#         print(row)
# else:
#     print("No job listings found.")
#
# print("\n📋 Shortlisted Candidates:\n" + "-" * 50)
# # Check Shortlisted Candidate Details
# try:
#     cursor.execute("SELECT * FROM shortlisted_candidates")
#     candidate_rows = cursor.fetchall()
#
#     if candidate_rows:
#         for row in candidate_rows:
#             print(row)
#     else:
#         print("No shortlisted candidates found.")
# except sqlite3.OperationalError:
#     print("❌ Table 'shortlisted_candidates' does not exist.")
#
# cursor.execute("PRAGMA table_info(shortlisted_candidates)")
# columns = cursor.fetchall()
# for col in columns:
#     print(col)
#
# conn.close()
import sqlite3

conn = sqlite3.connect("job_screening.db")
cursor = conn.cursor()

# Show all column names for the table
cursor.execute("PRAGMA table_info(shortlisted_candidates)")
columns = cursor.fetchall()

print("Columns in 'shortlisted_candidates':")
for col in columns:
    print(f" - {col[1]}")

conn.close()
