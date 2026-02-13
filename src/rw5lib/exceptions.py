class MalformedGPSRecordError(Exception):
    """Some GPS records may not include quality info, indicating that it should not be used as a point."""
