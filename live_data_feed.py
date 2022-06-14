#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 10 14:55:04 2022

@author: yanbing_wang
"""
from i24_database_api.db_reader import DBReader
import i24_logger.log_writer as log_writer
import time

def format_flat(columns, document, impute_none_for_missing=False):
    """
    Takes a `document` returned from MongoDB and organizes it into an ordered list of values specified by `columns`.
    :param columns: List of column names corresponding to document fields.
    :param document: Dictionary-like document from MongoDB with fields corresponding to column names.
    :param impute_none_for_missing: If True, sets value to None for any missing columns in `document`.
    :return: List of values corresponding to columns.
    """
    # TODO: fill this in
    # TODO: type hints correct to the data type the document will come through as
    return []


def read_query_once(host, port, username, password, database_name, collection_name,
                    query_filter, query_sort = None, limit = 0):
    """
    Executes a single database read query using the DBReader object, which is destroyed immediately upon completion.
    :param host: Database connection host name.
    :param port: Database connection port number.
    :param username: Database authentication username.
    :param password: Database authentication password.
    :param database_name: Name of database to connect (do not confuse with collection name).
    :param collection_name: Name of database collection from which to query.
    :param query_filter: Currently a dict following pymongo convention (need to abstract this).
    :param query_sort: List of tuples: (field_to_sort, sort_direction); direction is ASC/ASCENDING or DSC/DESCENDING.
    :param limit: Numerical limit for number of documents returned by query.
    :return:
    """
    dbr = DBReader(host=host, port=port, username=username, password=password,
                   database_name=database_name, collection_name=collection_name)
    result = dbr.read_query(query_filter=query_filter, query_sort=query_sort, limit=limit)
    return result



def live_data_reader(host, port, username, password, database_name, collection_name, range_increment, direction,
                     ready_queue, t_buffer = 100, min_queue_size = 1000):
    """
    Runs a database stream update listener on top of a managed cache that buffers data for a safe amount of time so
        that it can be assured to be time-ordered. Refill data queue if the queue size is below a threshold AND the next query range is before change_stream t_max - t_buffer
    ** THIS PROCEDURE AND FUNCTION IS STILL UNDER DEVELOPMENT **
    ** NEEDS TO DETERMINE **
    t_buffer: buffer time (in sec) such that no new fragment will be inserted before t_max - t_buffer   
    
    :param host: Database connection host name.
    :param port: Database connection port number.
    :param username: Database authentication username.
    :param password: Database authentication password.
    :param database_name: Name of database to connect to (do not confuse with collection name).
    :param collection_name: Name of database collection from which to query.
    :param ready_queue: Process-safe queue to which records that are "ready" are written.  multiprocessing.Queue
    :return:
    """
    
    # Connect to a database reader
    dbr = DBReader(host=host, port=port, username=username,password=password,
                   database_name=database_name, collection_name=collection_name)
    # temporary: start from min and end at max
    dir = 1 if direction == "east" else -1
    rri = dbr.read_query_range(range_parameter='last_timestamp', range_increment=range_increment,
                               static_parameters = ["direction"], static_parameters_query = [("$eq", dir)])
    
    pipeline = [{'$match': {'operationType': 'insert'}}] # watch for insertion only
    first_change_time = dbr.get_max("last_timestamp") # to keep track of the first change during each change stream event
    safe_query_time = first_change_time - t_buffer # guarantee time-order up until safe_query_time

    logger = log_writer.logger
    logger.set_name("live_data_reader_"+direction)
    
    while True:
        try:
            logger.info("current queue size: {}, first_change_time: {:.2f}, range_iter_stop:{:.2f}, query: {:.2f}-{:.2f}".format(ready_queue.qsize(),first_change_time, dbr.range_iter_stop, rri._current_lower_value, rri._current_upper_value))
            if ready_queue.qsize() <= min_queue_size: # only move to the next query range if queue is low in stock
                stream = dbr.collection.watch(pipeline) 
                first_insert_change = stream.try_next() # get the first insert since last listen
                logger.info("first_insert_change: {}".format(first_insert_change))
  
                if first_insert_change: # if there is updates by the time collection.watch() is called
                    first_change_time = max(first_insert_change["fullDocument"]["last_timestamp"], first_change_time)
                    safe_query_time = first_change_time - t_buffer
                    dbr.range_iter_stop = safe_query_time
    
                if rri._current_upper_value < safe_query_time: # if safe to query
                    logger.info("read next query range: {:.2f}-{:.2f}".format(rri._current_lower_value, rri._current_upper_value))
                    next_batch = next(rri)
        
                    for doc in next_batch:
                        ready_queue.put(doc)
                else: # if not safe to query, then wait 
                    # logger.info("qsize for raw_data_queue: {}".format(ready_queue.qsize()))
                    time.sleep(2)
            else: # if queue has sufficient number of items, then wait before the next iteration (throttle)
                logger.info("queue size is sufficient")     
                time.sleep(10)
                        
        except StopIteration: # rri reaches the end
            logger.warning("live_data_reader reaches the end of query range iteration.")
            pass

    