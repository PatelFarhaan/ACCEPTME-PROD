import memcache
import enum


client = memcache.Client([('127.0.0.1', 11211)])


class CONSTANT(enum.Enum):
    TOTAL_REQUEST_TO_BE_ACCEPT = "total_request_to_be_accept"
    IS_REQUEST_COMPLETE = "is_request_complete"
    SUCCESSFUL_ACCEPTED = "successful_accepted"
    REQUEST_FAILED = "request_failed"
    ALL_INFO = "_all_info"