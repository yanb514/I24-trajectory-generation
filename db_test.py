from db_reader import DBReader
from db_writer import DBWriter
import db_parameters
import time

# %% Test connection Done
dbr = DBReader(host=db_parameters.DEFAULT_HOST, port=db_parameters.DEFAULT_PORT, username=db_parameters.DEFAULT_USERNAME,   
               password=db_parameters.DEFAULT_PASSWORD,
               database_name=db_parameters.DB_NAME, collection_name=db_parameters.RAW_COLLECTION)



# %% Test read_query Done
dbr.create_index(["last_timestamp", "first_timestamp", "starting_x", "ending_x"])
res = dbr.read_query(query_filter = {"last_timestamp": {"$gt": 5, "$lt":309}}, query_sort = [("last_timestamp", "ASC"), ("starting_x", "ASC")],
                   limit = 0)

for doc in res:
    print("last timestamp: {:.2f}, starting_x: {:.2f}, ID: {}".format(doc["last_timestamp"], doc["starting_x"], doc["ID"]))


#%% Test read_query_range (no range_increment) Done
print("Using while-loop to read range")
rri = dbr.read_query_range(range_parameter='last_timestamp', range_greater_equal=300, range_less_than=330, range_increment=None)
while True:
    try:
        print(next(rri)["ID"]) # access documents in rri one by one
    except StopIteration:
        print("END OF ITERATION")
        break

print("Using for-loop to read range")
for result in dbr.read_query_range(range_parameter='last_timestamp', range_greater_equal=300, range_less_than=330, range_increment=None):
    print(result["ID"])
print("END OF ITERATION")


#%% Test read_query_range (with range_increment) Done
print("Using while-loop to read range")
rri = dbr.read_query_range(range_parameter='last_timestamp', range_greater_equal=300, range_less_than=330, range_increment=10)
while True:
    try:
        print("Current range: {}-{}".format(rri._current_lower_value, rri._current_upper_value))
        for doc in next(rri): # next(rri) is a cursor
            print(doc["ID"])
    except StopIteration:
        print("END OF ITERATION")
        break

# print("Using for-loop to read range")
# for interval in dbr.read_query_range(range_parameter='last_timestamp', range_greater_equal=300, range_less_than=330,range_increment=10):
#     print("next interval ")
#     for doc in interval:
#         print(doc["ID"])
# print("END OF ITERATION")

#%% Test DBWriter write_stitch Done
# query some test data to write to a new collection
print("Connect to DBReader")
test_dbr = DBReader(host=db_parameters.DEFAULT_HOST, port=db_parameters.DEFAULT_PORT, username=db_parameters.DEFAULT_USERNAME,   
               password=db_parameters.DEFAULT_PASSWORD,
               database_name=db_parameters.DB_NAME, collection_name=db_parameters.GT_COLLECTION)
print("Query...")
test_res = test_dbr.read_query(query_filter = {"last_timestamp": {"$gt": 5, "$lt":600}}, query_sort = [("last_timestamp", "ASC"), ("starting_x", "ASC")],
                   limit = 0)
test_res = list(test_res)
print("Connect to DBWriter")
dbw = DBWriter(host=db_parameters.DEFAULT_HOST, port=db_parameters.DEFAULT_PORT, username=db_parameters.DEFAULT_USERNAME,   
               password=db_parameters.DEFAULT_PASSWORD,
               database_name=db_parameters.DB_NAME, server_id=1, process_name=1, process_id=1, session_config_id=1)
print("Writing {} documents...".format(len(test_res)))

col = dbw.db[db_parameters.STITCHED_COLLECTION]
col.drop()
for doc in test_res:
    dbw.write_stitch(doc, collection_name = db_parameters.STITCHED_COLLECTION)


for doc in col.find({}):
    print(doc["ID"], doc["last_timestamp"]
    
#%% Async insert_many using motor
import asyncio

dbw = DBWriter(host=db_parameters.DEFAULT_HOST, port=db_parameters.DEFAULT_PORT, username=db_parameters.DEFAULT_USERNAME,   
               password=db_parameters.DEFAULT_PASSWORD,
               database_name=db_parameters.DB_NAME, server_id=1, process_name=1, process_id=1, session_config_id=1)

# dbw.motor_db[db_parameters.STITCHED_COLLECTION].drop()

print("start inserting")
t1 = time.time()
col = dbw.motor_db[db_parameters.STITCHED_COLLECTION]
async def f():
    await col.insert_many(({'i': i} for i in range(1000)))
    count = await col.count_documents({})
    print("Final count: %d" % count)
  
# loop = asyncio.get_event_loop()
# loop.run_until_complete(f())
t2 = time.time()
print("Elapsed time: ", t2-t1)
count = col.count_documents({})
print(count)



