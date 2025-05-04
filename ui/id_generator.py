import uuid


def gen_uid():
    return str(uuid.uuid4())


def shorten_uid(uid):
    return uid[:3]
