from queue import SimpleQueue, PriorityQueue

status_queue = SimpleQueue()
alarm_queue = SimpleQueue()
strip_queue = PriorityQueue(maxsize=50)
restapi_queue = SimpleQueue()
presence_queue = SimpleQueue()
serial_queue = SimpleQueue()
mqtt_queue = PriorityQueue(maxsize=50)
